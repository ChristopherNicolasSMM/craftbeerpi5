from abc import ABCMeta
import asyncio
from cbpi.api.config import ConfigType

__all__ = ["CBPiActor"]

import logging

logger = logging.getLogger(__file__)

"""
================================================================================
CLASSE BASE: CBPiActor
================================================================================
Classe base abstrata para todos os atuadores do sistema.

Um atuador é um dispositivo que pode ser controlado (ligado/desligado)
com potência variável, como:
- Bombas
- Aquecedores
- Válvulas
- Agitadores

Todas as implementações de atuadores devem herdar desta classe e implementar
os métodos on() e off().

Ciclo de vida:
1. __init__: Inicialização
2. init(): Configuração inicial (opcional)
3. start(): Inicia o atuador (chama on_start() -> run() -> on_stop())
4. stop(): Para o atuador
"""
class CBPiActor(metaclass=ABCMeta):

    def __init__(self, cbpi, id, props):
        """
        Inicializa um atuador.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
            id: ID único do atuador
            props: Propriedades/configurações do atuador
        """
        self.cbpi = cbpi
        self.id = id
        self.props = props  # Propriedades do atuador (definidas no config.yaml)
        self.logger = logging.getLogger(__file__)
        self.data_logger = None  # Logger para dados (opcional)
        self.state = False  # Estado atual (True = ligado, False = desligado)
        self.running = False  # Se está em execução (task ativa)
        self.power = 100  # Potência atual (0-100)

    def init(self):
        """
        Método de inicialização chamado após criação do atuador.
        
        Pode ser sobrescrito para fazer configurações iniciais específicas.
        """
        pass

    def log_data(self, value):
        """
        Registra um valor no log do atuador.
        
        Args:
            value: Valor a ser logado
        """
        self.cbpi.log.log_data(self.id, value)
        
    def get_state(self):
        """
        Retorna o estado atual do atuador.
        
        Returns:
            Dicionário com estado (ligado/desligado)
        """
        return dict(state=self.state)

    async def start(self):
        """
        Inicia o atuador (método abstrato - deve ser implementado).
        
        Este método deve ligar o atuador e iniciar a task de execução.
        """
        pass

    async def stop(self):
        """
        Para o atuador (método abstrato - deve ser implementado).
        
        Este método deve desligar o atuador e cancelar a task de execução.
        """
        pass

    async def on_start(self):
        """
        Callback chamado quando o atuador é iniciado.
        
        Pode ser sobrescrito para executar código antes de iniciar.
        """
        pass

    async def on_stop(self):
        """
        Callback chamado quando o atuador é parado.
        
        Pode ser sobrescrito para executar código de limpeza.
        """
        pass

    async def run(self):
        """
        Método principal de execução do atuador (método abstrato).
        
        Este método é executado em loop enquanto o atuador está ativo.
        Deve ser implementado para definir o comportamento do atuador.
        
        Returns:
            Razão do cancelamento (quando parar)
        """
        pass
    
    async def _run(self):
        """
        Método interno que gerencia o ciclo de vida do atuador.
        
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



    def get_static_config_value(self,name,default):
        return self.cbpi.static_config.get(name, default)

    def get_config_value(self,name,default):
        return self.cbpi.config.get(name, default=default)

    async def set_config_value(self,name,value):
        return await self.cbpi.config.set(name,value)

    async def add_config_value(self, name, value, type: ConfigType, description, options=None):
        await self.cbpi.add(name, value, type, description, options=None)

    async def on(self, power):
        """
        Liga o atuador com potência especificada (método abstrato).
        
        Este método DEVE ser implementado por todas as subclasses.
        É responsável por ligar fisicamente o atuador.
        
        Args:
            power: Potência entre 0 e 100
        """
        pass

    async def off(self):
        """
        Desliga o atuador (método abstrato).
        
        Este método DEVE ser implementado por todas as subclasses.
        É responsável por desligar fisicamente o atuador.
        """
        pass

    async def set_power(self, power):
        """
        Define a potência do atuador (se já estiver ligado).
        
        Este método pode ser sobrescrito para ajustar potência sem
        desligar/ligar o atuador.
        
        Args:
            power: Potência entre 0 e 100
        
        Returns:
            Dicionário com potência atual
        """
        return dict(power=self.power)
        pass

