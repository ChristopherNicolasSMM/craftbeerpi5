from cbpi.api.dataclasses import Actor
from cbpi.controller.basic_controller2 import BasicController
import logging
from tabulate import tabulate

"""
================================================================================
CONTROLLER: ActorController
================================================================================
Gerencia todos os atuadores do sistema (bombas, aquecedores, válvulas, etc.).

Responsabilidades:
- Controlar ligar/desligar atuadores
- Gerenciar potência dos atuadores
- Atualizar estado via WebSocket e MQTT
- Persistir dados em actor.json

Herda de BasicController que fornece operações CRUD básicas.
"""
class ActorController(BasicController):

    def __init__(self, cbpi):
        """
        Inicializa o controller de atuadores.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
        """
        super(ActorController, self).__init__(cbpi, Actor,"actor.json")
        self.update_key = "actorupdate"  # Chave para atualizações via WebSocket
        self.sorting=True  # Se True, ordena dados ao enviar via WebSocket

    async def on(self, id, power=None):
        """
        Liga um atuador.
        
        Se o atuador já estiver ligado, apenas ajusta a potência.
        Se power não for especificado, usa a potência salva ou 100% como padrão.
        
        Args:
            id: ID do atuador
            power: Potência (0-100). Se None, usa potência salva ou 100%
        
        Processo:
        1. Busca o atuador pelo ID
        2. Determina a potência a usar
        3. Se desligado, liga com a potência especificada
        4. Se já ligado, apenas ajusta a potência
        5. Envia atualização via WebSocket e MQTT
        """
        try:
            item = self.find_by_id(id)
            if power is None:
                logging.info("Power is none")
                # Usa potência salva ou padrão de 100%
                if item.power:
                    power = item.power
                else:
                    power = 100
            if item.instance.state is False:
                # Atuador está desligado - liga
                await item.instance.on(power)
                # Envia atualização para todos os clientes WebSocket
                self.cbpi.ws.send(dict(topic=self.update_key, data=list(map(lambda item: item.to_dict(), self.data))),self.sorting)
                # Publica atualização via MQTT (se habilitado)
                self.cbpi.push_update("cbpi/actorupdate/{}".format(id), item.to_dict(), True)
            else:
                # Atuador já está ligado - apenas ajusta potência
                await self.set_power(id, power)
                
        except Exception as e:
            logging.error("Failed to switch on Actor {} {}".format(id, e))

    async def off(self, id):
        """
        Desliga um atuador.
        
        Args:
            id: ID do atuador
        
        Processo:
        1. Busca o atuador pelo ID
        2. Se estiver ligado, desliga
        3. Envia atualização via WebSocket e MQTT
        """
        try:
            item = self.find_by_id(id)
            if item.instance.state is True:
                await item.instance.off()
                # Envia atualização para todos os clientes WebSocket
                self.cbpi.ws.send(dict(topic=self.update_key, data=list(map(lambda item: item.to_dict(), self.data))),self.sorting)
                # Publica atualização via MQTT (se habilitado)
                self.cbpi.push_update("cbpi/actorupdate/{}".format(id), item.to_dict())
        except Exception as e:
            logging.error("Failed to switch on Actor {} {}".format(id, e), True)

    async def toogle(self, id):
        """
        Alterna o estado de um atuador (liga se desligado, desliga se ligado).
        
        Args:
            id: ID do atuador
        """
        try:
            item = self.find_by_id(id)
            instance = item.get("instance")
            await instance.toggle()
            # Envia atualização via WebSocket e MQTT
            self.cbpi.ws.send(dict(topic=self.update_key, data=list(map(lambda item: item.to_dict(), self.data))),self.sorting)
            self.cbpi.push_update("cbpi/actorupdate/{}".format(id), item.to_dict())
        except Exception as e:
            logging.error("Failed to toggle Actor {} {}".format(id, e))

    async def set_power(self, id, power):
        """
        Define a potência de um atuador (deve estar ligado).
        
        Args:
            id: ID do atuador
            power: Potência (0-100)
        """
        try:
            item = self.find_by_id(id)
            await item.instance.set_power(power)
        except Exception as e:
            logging.error("Failed to set power {} {}".format(id, e))

    async def actor_update(self, id, power):
        """
        Atualiza a potência de um atuador e envia notificação.
        
        Diferente de set_power, este método também atualiza o valor salvo
        e envia notificações via WebSocket e MQTT.
        
        Args:
            id: ID do atuador
            power: Potência (0-100)
        """
        try:
            item = self.find_by_id(id)
            item.power = round(power)  # Salva potência arredondada
            # Envia atualização via WebSocket e MQTT
            self.cbpi.ws.send(dict(topic=self.update_key, data=list(map(lambda item: item.to_dict(), self.data))),self.sorting)
            self.cbpi.push_update("cbpi/actorupdate/{}".format(id), item.to_dict())
        except Exception as e:
            logging.error("Failed to update Actor {} {}".format(id, e))
