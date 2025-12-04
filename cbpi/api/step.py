import asyncio
import logging
from abc import abstractmethod
import cbpi

from cbpi.api.base import CBPiBase

__all__ = ["StepResult", "StepState", "StepMove", "CBPiStep", "CBPiFermentationStep"]

from enum import Enum

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)



"""
================================================================================
ENUMS: Estados e Resultados de Etapas
================================================================================
"""
class StepResult(Enum):
    """Resultado da execução de uma etapa"""
    STOP = 1  # Etapa foi parada manualmente
    NEXT = 2  # Etapa completou e deve ir para próxima
    DONE = 3  # Todas as etapas completaram
    ERROR = 4  # Erro durante execução


class StepState(Enum):
    """Estado atual de uma etapa"""
    INITIAL = "I"  # Inicial (não iniciada)
    DONE = "D"  # Completa
    ACTIVE = "A"  # Em execução
    ERROR = "E"  # Erro
    STOP = "S"  # Parada


class StepMove(Enum):
    """Direção para mover etapa na sequência"""
    UP = -1  # Mover para cima (antes)
    DOWN = 1  # Mover para baixo (depois)


"""
================================================================================
CLASSE BASE: CBPiStep
================================================================================
Classe base para todas as etapas do processo de brassagem.

Uma etapa representa uma fase do processo, como:
- Aquecimento até temperatura
- Mosturação por tempo determinado
- Fervura
- Adição de lúpulo

Todas as implementações de etapas devem herdar desta classe e implementar
o método run() que define o comportamento da etapa.

Ciclo de vida:
1. __init__: Inicialização
2. start(): Inicia execução (cria task assíncrona)
3. run(): Execução principal (deve retornar StepResult)
4. next()/stop(): Para a etapa
5. on_done callback: Chamado quando etapa completa
"""
class CBPiStep(CBPiBase):

    def __init__(self, cbpi, id, name, props, on_done) -> None:
        """
        Inicializa uma etapa.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
            id: ID único da etapa
            name: Nome da etapa
            props: Propriedades/configurações da etapa
            on_done: Callback chamado quando etapa completa
        """
        self.name = name
        self.cbpi = cbpi
        self.id = id
        self.timer = None  # Timer opcional para etapas com duração
        self._done_callback = on_done  # Callback quando completa
        self.props = props  # Propriedades da etapa
        self.cancel_reason: StepResult = None  # Razão do cancelamento
        self.summary = ""  # Resumo da execução
        self.task = None  # Task assíncrona de execução
        self.running: bool = False  # Se está em execução
        self.logger = logging.getLogger(__name__)

    def _done(self, task):
        """
        Callback chamado quando a task de execução completa.
        
        Args:
            task: Task que completou
        """
        if self._done_callback is not None:
            try:
                result = task.result()  # Obtém resultado (StepResult)
                self._done_callback(self, result)  # Chama callback do StepController
            except Exception as e:
                self.logger.error(e)

    async def start(self):
        """
        Inicia a execução da etapa.
        
        Cria uma task assíncrona que executa o método _run().
        """
        self.logger.info("Start {}".format(self.name))
        self.running = True
        self.task = asyncio.create_task(self._run())  # Cria task assíncrona
        self.task.add_done_callback(self._done)  # Registra callback de conclusão

    async def next(self):
        """
        Avança para a próxima etapa.
        
        Cancela a etapa atual e marca como NEXT para que o StepController
        inicie a próxima etapa na sequência.
        """
        self.running = False
        self.cancel_reason = StepResult.NEXT
        self.task.cancel()  # Cancela task atual
        await self.task  # Aguarda cancelamento

    async def stop(self):
        """
        Para a execução da etapa.
        
        Cancela a task e marca como STOP (não avança para próxima).
        """
        try:
            self.running = False
            if self.task is not None and self.task.done() is False:
                self.cancel_reason = StepResult.STOP
                self.task.cancel()
                await self.task  # Aguarda cancelamento
        except Exception as e:
            logging.error(e)
        
    async def reset(self):
        pass

    async def on_props_update(self, props):
        self.props = {**self.props, **props}

    async def save_props(self):
        await self.cbpi.step.save()

    async def push_update(self):
        self.cbpi.step.push_udpate()

    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def _run(self):
        try:
            await self.on_start()
            await self.run()
            self.cancel_reason = StepResult.DONE
        except asyncio.CancelledError as e:
            pass
        finally:
            await self.on_stop()

        return self.cancel_reason

    @abstractmethod
    async def run(self):
        pass

    def __str__(self):
        return "name={} props={}, type={}".format(self.name, self.props, self.__class__.__name__)

class CBPiFermentationStep(CBPiBase):

    def __init__(self, cbpi, fermenter, step, props, on_done) -> None:
        self.fermenter = fermenter
        self.name = step.get("name")
        self.cbpi = cbpi
        self.id = step.get("id")
        self.timer = None
        self._done_callback = on_done
        self.props = props
        self.endtime = int(step.get("endtime"))
        self.cancel_reason: StepResult = None
        self.summary = ""
        self.task = None
        self.running: bool = False
        self.logger = logging.getLogger(__name__)
        self.step = step
        self.update_key="fermenterstepupdate"

    def _done(self, task):
        if self._done_callback is not None:
            try:
                result = task.result()
                logging.info(result)
                logging.info(self.fermenter.id)
                fermenter=self.fermenter.id
                self._done_callback(self, result, fermenter)
            except Exception as e:
                self.logger.error(e)

    async def start(self):
        self.logger.info("Start {}".format(self.name))
        self.running = True
        self.task = asyncio.create_task(self._run())
        self.task.add_done_callback(self._done)

    async def next(self, fermenter=None):
        if fermenter is None:
            self.running = False
            self.cancel_reason = StepResult.NEXT
            self.task.cancel()
            await self.task
        else:
            await self.cbpi.fermenter.next(fermenter)

    async def stop(self):
        try:
            self.running = False
            if self.task is not None and self.task.done() is False:
                self.cancel_reason = StepResult.STOP
                logging.info(self.cancel_reason)
                self.task.cancel()
                await self.task
        except Exception as e:
            logging.error(e)
        
    async def reset(self):
        pass

    async def on_props_update(self, props):
        self.props = {**self.props, **props}

    async def update_endtime(self):
        await self.cbpi.fermenter.update_endtime(self.fermenter.id, self.id, self.endtime)

    async def save_props(self):
        self.cbpi.fermenter.save()

    async def push_update(self):
        self.cbpi.fermenter.push_update(self.update_key)

    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def _run(self):
        try:
            await self.on_start()
            await self.run()
            self.cancel_reason = StepResult.DONE
        except asyncio.CancelledError as e:
            pass
        finally:
            await self.on_stop()

        return self.cancel_reason

    @abstractmethod
    async def run(self):
        pass

    def __str__(self):
        return "name={} props={}, type={}".format(self.name, self.props, self.__class__.__name__)