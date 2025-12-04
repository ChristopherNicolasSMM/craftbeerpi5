from cbpi.api.base import CBPiBase
from cbpi.api.extension import CBPiExtension
from abc import ABCMeta
import logging
import asyncio

"""
================================================================================
CLASSE BASE: CBPiFermenterLogic
================================================================================
Classe base abstrata para lógicas de controle de fermentadores.

Uma lógica de fermentador define como o fermentador se comporta, como:
- Hysteresis (liga/desliga baseado em temperatura)
- PID (controle proporcional-integral-derivativo)
- Controle de pressão

Todas as implementações de lógicas de fermentador devem herdar desta classe
e implementar o método run() que define o comportamento.

Ciclo de vida:
1. __init__: Inicialização
2. init(): Configuração inicial (opcional)
3. start(): Inicia controle (cria task assíncrona)
4. run(): Execução principal (loop de controle)
5. stop(): Para o controle
"""
class CBPiFermenterLogic(CBPiBase, metaclass=ABCMeta):

    def __init__(self, cbpi, id, props):
        """
        Inicializa uma lógica de fermentador.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
            id: ID do fermentador
            props: Propriedades/configurações da lógica
        """
        self.cbpi = cbpi
        self.id = id
        self.props = props  # Propriedades da lógica (ex: temperatura alvo, pressão)
        self.state = False  # Estado atual (True = controle ativo)
        self.running = False  # Se está em execução (task ativa)

    def init(self):
        pass
    
    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def run(self):
        pass
    
    async def _run(self):

        try:
            await self.on_start()
            self.cancel_reason = await self.run()
        except asyncio.CancelledError as e:
            pass
        finally:
            await self.on_stop()
        
    def get_state(self):
        return dict(running=self.state)

    async def start(self):
        
        self.state = True

    async def stop(self):
        
        self.task.cancel()
        await self.task
        self.state = False
