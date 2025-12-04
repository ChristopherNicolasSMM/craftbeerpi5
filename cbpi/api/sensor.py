import asyncio
import logging
from abc import abstractmethod, ABCMeta
from cbpi.api.extension import CBPiExtension

from cbpi.api.base import CBPiBase

"""
================================================================================
CLASSE BASE: CBPiSensor
================================================================================
Classe base abstrata para todos os sensores do sistema.

Um sensor é um dispositivo que lê valores, como:
- Sensores de temperatura (DS18B20, PT100, etc.)
- Sensores de pressão
- Sensores de nível
- Sensores customizados

Todas as implementações de sensores devem herdar desta classe e implementar
os métodos get_state(), get_value() e get_unit().

Ciclo de vida:
1. __init__: Inicialização
2. init(): Configuração inicial (opcional)
3. start(): Inicia leitura contínua (chama on_start() -> run() -> on_stop())
4. stop(): Para a leitura
"""
class CBPiSensor(CBPiBase, metaclass=ABCMeta):

    def __init__(self, cbpi, id, props):
        """
        Inicializa um sensor.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
            id: ID único do sensor
            props: Propriedades/configurações do sensor
        """
        self.cbpi = cbpi
        self.id = id
        self.props = props  # Propriedades do sensor (definidas no config.yaml)
        self.logger = logging.getLogger(__file__)
        self.data_logger = None  # Logger para dados (opcional)
        self.state = False  # Estado atual do sensor
        self.running = False  # Se está em execução (task ativa)

    def init(self):
        """
        Método de inicialização chamado após criação do sensor.
        
        Pode ser sobrescrito para fazer configurações iniciais específicas.
        """
        pass

    def log_data(self, value):
        """
        Registra um valor no log do sensor.
        
        Args:
            value: Valor a ser logado
        """
        self.cbpi.log.log_data(self.id, value)

    def get_state(self):
        """
        Retorna o estado atual do sensor (método abstrato).
        
        Deve retornar um dicionário com informações do sensor, incluindo
        o valor atual e unidade de medida.
        
        Returns:
            Dicionário com estado do sensor (ex: {"value": 25.5, "unit": "C"})
        """
        pass

    def get_value(self):
        """
        Retorna apenas o valor atual do sensor (método abstrato).
        
        Returns:
            Valor numérico do sensor
        """
        pass

    def get_unit(self):
        """
        Retorna a unidade de medida do sensor (método abstrato).
        
        Returns:
            String com unidade (ex: "C", "F", "PSI", "%")
        """
        pass

    def push_update(self, value, mqtt=True):
        """
        Envia atualização do valor do sensor via WebSocket e MQTT.
        
        Args:
            value: Novo valor do sensor
            mqtt: Se True, também publica via MQTT (se habilitado)
        """
        try:
            # Envia via WebSocket para todos os clientes conectados
            self.cbpi.ws.send(dict(topic="sensorstate", id=self.id, value=value))
            if mqtt:
                # Publica via MQTT (mensagem retida para novos subscribers)
                self.cbpi.push_update("cbpi/sensordata/{}".format(self.id), 
                                     dict(id=self.id, value=value), retain=True)
        except:
            logging.error("Failed to push sensor update")

    async def start(self):
        """
        Inicia a leitura contínua do sensor (método abstrato).
        
        Este método deve iniciar uma task que lê o sensor periodicamente.
        """
        pass

    async def stop(self):
        """
        Para a leitura do sensor (método abstrato).
        
        Este método deve cancelar a task de leitura.
        """
        pass

    async def on_start(self):
        """
        Callback chamado quando o sensor é iniciado.
        
        Pode ser sobrescrito para executar código antes de iniciar.
        """
        pass

    async def on_stop(self):
        """
        Callback chamado quando o sensor é parado.
        
        Pode ser sobrescrito para executar código de limpeza.
        """
        pass

    async def run(self):
        """
        Método principal de leitura do sensor (método abstrato).
        
        Este método é executado em loop enquanto o sensor está ativo.
        Deve ler o sensor periodicamente e chamar push_update().
        
        Returns:
            Razão do cancelamento (quando parar)
        """
        pass
    
    async def _run(self):
        """
        Método interno que gerencia o ciclo de vida do sensor.
        
        Executa: on_start() -> run() -> on_stop()
        Trata exceções e cancelamentos adequadamente.
        """
        try:
            await self.on_start()  # Callback de início
            self.cancel_reason = await self.run()  # Execução principal
        except asyncio.CancelledError as e:
            # Cancelamento normal (quando stop() é chamado)
            pass
        finally:
            await self.on_stop()  # Callback de parada (sempre executado)
