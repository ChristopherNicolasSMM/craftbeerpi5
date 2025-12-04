from cbpi.api.base import CBPiBase
from cbpi.api.extension import CBPiExtension
from abc import ABCMeta
import logging
import asyncio

"""
================================================================================
CLASSE BASE: CBPiKettleLogic
================================================================================
Classe base abstrata para lógicas de controle de panelas.

Uma lógica de panela define como a panela se comporta, como:
- Hysteresis (liga/desliga baseado em temperatura)
- PID (controle proporcional-integral-derivativo)
- Manual (controle manual)

Todas as implementações de lógicas de panela devem herdar desta classe
e implementar o método run() que define o comportamento.

Ciclo de vida:
1. __init__: Inicialização
2. init(): Configuração inicial (opcional)
3. start(): Inicia controle (cria task assíncrona)
4. run(): Execução principal (loop de controle)
5. stop(): Para o controle
"""
class CBPiKettleLogic(CBPiBase, metaclass=ABCMeta):

    def __init__(self, cbpi, id, props):
        """
        Inicializa uma lógica de panela.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
            id: ID da panela
            props: Propriedades/configurações da lógica
        """
        self.cbpi = cbpi
        self.id = id
        self.props = props  # Propriedades da lógica (ex: temperatura alvo, histerese)
        self.state = False  # Estado atual (True = controle ativo)
        self.running = False  # Se está em execução (task ativa)

    def init(self):
        """
        Método de inicialização chamado após criação da lógica.
        
        Pode ser sobrescrito para fazer configurações iniciais específicas.
        """
        pass
    
    async def on_start(self):
        """
        Callback chamado quando o controle é iniciado.
        
        Pode ser sobrescrito para executar código antes de iniciar.
        """
        pass

    async def on_stop(self):
        """
        Callback chamado quando o controle é parado.
        
        Pode ser sobrescrito para executar código de limpeza.
        """
        pass

    async def run(self):
        """
        Método principal de controle da panela (método abstrato).
        
        Este método é executado em loop enquanto o controle está ativo.
        Deve implementar a lógica de controle (ex: ler temperatura,
        ligar/desligar aquecedor, etc.).
        
        Returns:
            Razão do cancelamento (quando parar)
        """
        pass
    
    async def _run(self):
        """
        Método interno que gerencia o ciclo de vida do controle.
        
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
        
    def get_state(self):
        """
        Retorna o estado atual do controle.
        
        Returns:
            Dicionário com estado (running: True/False)
        """
        return dict(running=self.state)

    async def start(self):
        """
        Inicia o controle da panela.
        
        Marca estado como True. A task de execução deve ser criada
        externamente (pelo KettleController).
        """
        self.state = True

    async def stop(self):
        """
        Para o controle da panela.
        
        Cancela a task de execução e marca estado como False.
        """
        self.task.cancel()
        await self.task  # Aguarda cancelamento
        self.state = False
