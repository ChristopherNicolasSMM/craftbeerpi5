from cbpi.api.dataclasses import Kettle, Props
from cbpi.controller.basic_controller2 import BasicController
import logging
from tabulate import tabulate

"""
================================================================================
CONTROLLER: KettleController
================================================================================
Gerencia panelas de brassagem do sistema.

Responsabilidades:
- Controlar lógica de brassagem (temperatura, aquecimento)
- Gerenciar sensores e aquecedores associados
- Controlar agitadores
- Persistir dados em kettle.json

Herda de BasicController que fornece operações CRUD básicas.
"""
class KettleController(BasicController):

    def __init__(self, cbpi):
        """
        Inicializa o controller de panelas.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
        """
        super(KettleController, self).__init__(cbpi, Kettle, "kettle.json")
        self.update_key = "kettleupdate"  # Chave para atualizações via WebSocket
        self.autostart = False  # Se True, inicia automaticamente ao criar
    
    def create(self, data):
        """
        Cria uma nova panela.
        
        Args:
            data: Dicionário com dados da panela (id, name, type, props, sensor, heater, agitator)
        
        Returns:
            Objeto Kettle criado
        """
        return Kettle(data.get("id"), data.get("name"), type=data.get("type"), 
                     props=Props(data.get("props", {})), sensor=data.get("sensor"), 
                     heater=data.get("heater"), agitator=data.get("agitator"))

    async def toggle(self, id):
        """
        Alterna o estado de uma panela (inicia se parada, para se em execução).
        
        Args:
            id: ID da panela
        """
        try:
            item = self.find_by_id(id)
            
            if item.instance is None or item.instance.state == False: 
                # Panela está parada - inicia
                await self.start(id)
            else:
                # Panela está em execução - para
                await item.instance.stop()
            await self.push_udpate()  # Envia atualização via WebSocket
        except Exception as e:
            logging.error("Failed to switch on KettleLogic {} {}".format(id, e))

    async def set_target_temp(self, id, target_temp):
        """
        Define a temperatura alvo de uma panela.
        
        Args:
            id: ID da panela
            target_temp: Temperatura alvo em graus
        """
        try:
            item = self.find_by_id(id)
            item.target_temp = target_temp
            await self.save()  # Salva alteração no arquivo
        except Exception as e:
            logging.error("Failed to set Target Temp {} {}".format(id, e))

    async def stop(self, id):
        """
        Para a execução de uma panela.
        
        Args:
            id: ID da panela
        """
        try:
            logging.info("Stop Kettle {}".format(id))
            item = self.find_by_id(id)
            if item.instance:
                await item.instance.stop()  # Para a lógica de brassagem
            await self.push_udpate()  # Envia atualização via WebSocket
        except Exception as e:
            logging.error("Failed to switch off KettleLogic {} {}".format(id, e))
