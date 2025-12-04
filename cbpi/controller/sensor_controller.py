from cbpi.api.dataclasses import Sensor
from cbpi.controller.basic_controller2 import BasicController
import logging

"""
================================================================================
CONTROLLER: SensorController
================================================================================
Gerencia todos os sensores do sistema (temperatura, pressão, etc.).

Responsabilidades:
- Gerenciar instâncias de sensores
- Ler valores dos sensores
- Atualizar estado via WebSocket
- Persistir dados em sensor.json

Herda de BasicController que fornece operações CRUD básicas.
"""
class SensorController(BasicController):
    def __init__(self, cbpi):
        """
        Inicializa o controller de sensores.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
        """
        super(SensorController, self).__init__(cbpi, Sensor, "sensor.json")
        self.update_key = "sensorupdate"  # Chave para atualizações via WebSocket
        self.sorting = True  # Se True, ordena dados ao enviar via WebSocket

    def create_dict(self, data):
        """
        Cria um dicionário com dados de um sensor para serialização.
        
        Args:
            data: Dados do sensor (objeto Sensor)
        
        Returns:
            Dicionário com informações do sensor (name, id, type, state, props)
        """
        try:
            instance = data.get("instance")
            state = instance.get_state()  # Obtém estado atual do sensor
        except Exception as e:
            logging.error("Failed to create sensor dict {} ".format(e))
            state = dict() 

        return dict(name=data.get("name"), id=data.get("id"), type=data.get("type"), 
                   state=state, props=data.get("props", []))
    
    def get_sensor_value(self, id):
        """
        Obtém o valor atual de um sensor.
        
        Args:
            id: ID do sensor
        
        Returns:
            Estado atual do sensor (geralmente um dicionário com valor e unidade)
            ou None se houver erro
        """
        try:
            return self.find_by_id(id).instance.get_state()
        except Exception as e:
            logging.error("Failed read sensor value {} {} ".format(id, e))
            return None