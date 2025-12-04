
import logging
import os.path
import json
from cbpi.api.dataclasses import Fermenter, Actor, Props
import sys, os
import shortuuid
import asyncio

from tabulate import tabulate

"""
================================================================================
CLASSE BASE: BasicController
================================================================================
Classe base para todos os controllers que gerenciam recursos (atores, sensores, etc.).

Esta classe fornece funcionalidades comuns:
- CRUD (Create, Read, Update, Delete)
- Persistência em arquivos JSON
- Gerenciamento de instâncias (start/stop)
- Atualizações via WebSocket
- Registro automático no sistema

Controllers que herdam desta classe:
- ActorController
- SensorController
- KettleController
- FermentationController

Padrão:
- Cada recurso tem um tipo (ex: "GPIOActor", "DS18B20Sensor")
- Tipos são registrados via self.types
- Instâncias são criadas dinamicamente baseadas no tipo
- Dados são persistidos em arquivos JSON
"""
class BasicController:

    def __init__(self, cbpi, resource, file):
        """
        Inicializa o controller base.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
            resource: Classe do recurso (ex: Actor, Sensor, Kettle)
            file: Nome do arquivo JSON para persistência (ex: "actor.json")
        """
        self.resource = resource  # Classe do recurso gerenciado
        self.update_key = ""  # Chave para atualizações WebSocket (ex: "actorupdate")
        self.sorting = False  # Se True, ordena dados ao enviar via WebSocket
        self.name = self.__class__.__name__  # Nome da classe (para logs)
        self.cbpi = cbpi
        self.cbpi.register(self)  # Registra automaticamente no sistema
        self.service = self  # Referência ao serviço
        self.types = {}  # Tipos registrados (ex: {"GPIOActor": {"class": GPIOActor, ...}})
        self.logger = logging.getLogger(__name__)
        self.data = []  # Lista de recursos gerenciados
        self.autostart = True  # Se True, inicia recursos automaticamente ao carregar
        self.path = self.cbpi.config_folder.get_file_path(file)  # Caminho do arquivo JSON
        self.cbpi.app.on_cleanup.append(self.shutdown)  # Registra limpeza ao encerrar
        
    async def init(self):
        """
        Inicializa o controller carregando dados do arquivo.
        """
        await self.load()
    
    def create(self, data):
        """
        Cria um novo recurso a partir de dados.
        
        Args:
            data: Dicionário com dados do recurso
        
        Returns:
            Instância do recurso criado
        """
        return self.resource(data.get("id"), data.get("name"), type=data.get("type"), 
                           props=Props(data.get("props", {})))

    async def load(self):
        """
        Carrega recursos do arquivo JSON.
        
        Se autostart=True, inicia automaticamente todos os recursos carregados.
        """
        logging.info("{} Load ".format(self.name))
        with open(self.path) as json_file:
            data = json.load(json_file)
            # Ordena por nome
            data['data'].sort(key=lambda x: x.get('name').upper())
            
            # Cria objetos a partir dos dados
            for i in data["data"]:
                self.data.append(self.create(i))
   
            # Inicia recursos automaticamente se configurado
            if self.autostart is True:
                for item in self.data:
                    logging.info("{} Starting ".format(self.name))
                    await self.start(item.id)
                await self.push_udpate()  # Envia atualização inicial
        
    async def save(self):
        """
        Salva recursos no arquivo JSON.
        
        Também envia atualização via WebSocket após salvar.
        """
        logging.info("{} Save ".format(self.name))
        data = dict(data=list(map(lambda actor: actor.to_dict(), self.data))) 
        with open(self.path, "w") as file:
            json.dump(data, file, indent=4, sort_keys=True)
        await self.push_udpate()  # Notifica clientes da atualização
        
    async def push_udpate(self):
        """
        Envia atualização de todos os recursos via WebSocket e MQTT.
        
        Envia:
        1. Lista completa para tópico geral (ex: "actorupdate")
        2. Dados individuais para tópicos específicos (ex: "cbpi/actorupdate/123")
        """
        # Envia lista completa via WebSocket
        self.cbpi.ws.send(dict(topic=self.update_key, 
                              data=list(map(lambda item: item.to_dict(), self.data))), 
                         self.sorting)
        # Envia atualização individual via MQTT para cada recurso
        for item in self.data:
            self.cbpi.push_update("cbpi/{}/{}".format(self.update_key, item.id), item.to_dict())

    def find_by_id(self, id):
        """
        Encontra um recurso pelo ID.
        
        Args:
            id: ID do recurso
        
        Returns:
            Recurso encontrado ou None
        """
        return next((item for item in self.data if item.id == id), None)
    
    def get_index_by_id(self, id):
        """
        Obtém o índice de um recurso na lista pelo ID.
        
        Args:
            id: ID do recurso
        
        Returns:
            Índice na lista ou None
        """
        return next((i for i, item in enumerate(self.data) if item.id == id), None)

    async def shutdown(self, app):
        """
        Executa limpeza ao encerrar o sistema.
        
        Cancela todas as tasks em execução e salva dados.
        
        Args:
            app: Aplicação web aiohttp
        """
        logging.info("{} Shutdown ".format(self.name))
        tasks = []
        # Cancela todas as tasks em execução
        for item in self.data:
            if item.instance is not None and item.instance.running is True:
                item.instance.task.cancel()
                tasks.append(item.instance.task)
        # Aguarda cancelamento de todas as tasks
        await asyncio.gather(*tasks)
        await self.save()  # Salva estado final

    async def stop(self, id):
        """
        Para um recurso específico.
        
        Args:
            id: ID do recurso
        """
        logging.info("{} Stop Id {} ".format(self.name, id))
        try:
            item = self.find_by_id(id)
            await item.instance.stop()  # Para a instância
            item.instance.running = False
            await self.push_udpate()  # Notifica atualização
        except Exception as e:
            logging.error("{} Cant stop {} - {}".format(self.name, id, e))

    async def start(self, id):
        """
        Inicia um recurso específico.
        
        Processo:
        1. Busca recurso pelo ID
        2. Verifica se já está em execução
        3. Busca classe do tipo registrado
        4. Cria instância da classe
        5. Inicia a instância e cria task de execução
        
        Args:
            id: ID do recurso
        """
        logging.info("{} Start Id {} ".format(self.name, id))
        try:
            item = self.find_by_id(id)
            # Verifica se já está em execução
            if item.instance is not None and item.instance.running is True:
                logging.warning("{} already running {}".format(self.name, id))
                return 
            # Verifica se tipo está definido
            if item.type is None:
                logging.warning("{} No Type {}".format(self.name, id))
                return 
            # Busca classe do tipo registrado
            clazz = self.types[item.type]["class"]
            # Cria instância do recurso
            item.instance = clazz(self.cbpi, item.id, item.props)
            
            # Inicia a instância
            await item.instance.start()
            item.instance.running = True
            # Cria task assíncrona para execução contínua
            item.instance.task = asyncio.get_event_loop().create_task(item.instance._run())
            
            logging.info("{} started {}".format(self.name, id))
        except Exception as e:
            logging.error("{} Cant start {} - {}".format(self.name, id, e))

    def get_types(self):
        """
        Retorna lista de tipos registrados com suas propriedades e ações.
        
        Returns:
            Dicionário com tipos disponíveis e suas configurações
        """
        result = {}
        for key, value in self.types.items():
            result[key] = dict(name=value.get("name"), 
                             properties=value.get("properties"), 
                             actions=value.get("actions"))
        return result

    def get_state(self):
        """
        Retorna estado completo do controller (recursos + tipos).
        
        Returns:
            Dicionário com lista de recursos e tipos disponíveis
        """
        return {"data": list(map(lambda x: x.to_dict(), self.data)), 
                "types": self.get_types()}

    async def add(self, item):
        """
        Adiciona um novo recurso.
        
        Args:
            item: Recurso a ser adicionado
        
        Returns:
            Recurso adicionado (com ID gerado)
        
        Processo:
        1. Gera ID único
        2. Adiciona à lista
        3. Inicia automaticamente se autostart=True
        4. Salva no arquivo
        """
        logging.info("{} Add".format(self.name))
        item.id = shortuuid.uuid()  # Gera ID único
        self.data.append(item)
        if self.autostart is True:
            await self.start(item.id)
        await self.save()
        return item 

    async def update(self, item):
        """
        Atualiza um recurso existente.
        
        Args:
            item: Recurso com dados atualizados
        
        Returns:
            Recurso atualizado
        
        Processo:
        1. Para o recurso atual
        2. Substitui na lista
        3. Reinicia se autostart=True
        4. Salva no arquivo
        """
        logging.info("{} Get Update".format(self.name))
        await self.stop(item.id)  # Para instância atual
        
        # Substitui na lista
        self.data = list(map(lambda old_item: item if old_item.id == item.id else old_item, self.data))
        if self.autostart is True:
            await self.start(item.id)  # Reinicia com novas configurações
        await self.save()
        return self.find_by_id(item.id)

    async def delete(self, id) -> None:
        """
        Remove um recurso.
        
        Args:
            id: ID do recurso a ser removido
        
        Processo:
        1. Para o recurso
        2. Remove da lista
        3. Salva no arquivo
        """
        logging.info("{} Delete".format(self.name))
        await self.stop(id)  # Para antes de remover
        self.data = list(filter(lambda x: x.id != id, self.data))  # Remove da lista
        await self.save()

    async def call_action(self, id, action, parameter) -> None:
        """
        Chama uma ação específica em um recurso.
        
        Ações são métodos definidos no tipo do recurso que podem ser
        chamados dinamicamente (ex: "reset", "calibrate").
        
        Args:
            id: ID do recurso
            action: Nome da ação (método) a ser chamado
            parameter: Parâmetros para a ação (dicionário)
        """
        logging.info("{} call all Action {} {}".format(self.name, id, action))
        try:
            item = self.find_by_id(id)
            # Chama método dinamicamente com parâmetros
            await item.instance.__getattribute__(action)(**parameter)
        except Exception as e:
            logging.error("{} Failed to call action on {} {} {}".format(self.name, id, action, e))
