import asyncio

from ._job import Job

try:
    from collections.abc import Collection
except ImportError:  # pragma: no cover
    # Python 3.5 has no Collection ABC class
    from collections.abc import Sized, Iterable, Container
    bases = Sized, Iterable, Container
else:  # pragma: no cover
    bases = (Collection,)


class Scheduler(*bases):
    def __init__(self, cbpi, *, close_timeout, limit, pending_limit,
                 exception_handler, loop):
        self._loop = loop
        self.cbpi = cbpi
        self._jobs = set()
        self._close_timeout = close_timeout
        self._limit = limit
        self._exception_handler = exception_handler
        self._failed_tasks = asyncio.Queue()
        self._failed_task = loop.create_task(self._wait_failed())
        self._pending = asyncio.Queue(maxsize=pending_limit)
        self._closed = False

    def __iter__(self):
        return iter(list(self._jobs))

    def __len__(self):
        return len(self._jobs)

    def __contains__(self, job):
        return job in self._jobs

    def __repr__(self):
        info = []
        if self._closed:
            info.append('closed')
        info = ' '.join(info)
        if info:
            info += ' '
        return '<Scheduler {}jobs={}>'.format(info, len(self))

    @property
    def limit(self):
        return self._limit

    @property
    def pending_limit(self):
        return self._pending.maxsize

    @property
    def close_timeout(self):
        return self._close_timeout

    @property
    def active_count(self):
        return len(self._jobs) - self._pending.qsize()

    @property
    def pending_count(self):
        return self._pending.qsize()

    @property
    def closed(self):
        return self._closed

    async def spawn(self, coro, name=None, type=None):
        """
        Agenda uma nova tarefa (job) para execução.
        
        Se houver limite de jobs simultâneos e já estiver no limite,
        a tarefa é adicionada à fila de espera.
        
        Args:
            coro: Corrotina a ser executada
            name: Nome da tarefa (para logs e identificação)
            type: Tipo da tarefa (ex: "background", "step")
        
        Returns:
            Objeto Job criado
        """
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        job = Job(coro, name, type, self, self._loop)
        # Verifica se pode iniciar imediatamente ou deve aguardar na fila
        should_start = (self._limit is None or
                        self.active_count < self._limit)
        self._jobs.add(job)
        if should_start:
            job._start()  # Inicia imediatamente
        else:
            # Aguarda slot livre na fila
            await self._pending.put(job)
        return job

    async def close(self):
        """
        Fecha o scheduler e cancela todas as tarefas.
        
        Processo:
        1. Marca como fechado (não aceita novas tarefas)
        2. Limpa fila de espera
        3. Cancela todas as tarefas ativas
        4. Aguarda conclusão do cancelamento
        """
        if self._closed:
            return
        self._closed = True  # Impede adicionar novos jobs

        jobs = self._jobs
        if jobs:
            # Limpa fila de espera
            while not self._pending.empty():
                self._pending.get_nowait()
            # Cancela todas as tarefas ativas
            await asyncio.gather(
                *[job._close(self._close_timeout) for job in jobs],
                return_exceptions=True)
            self._jobs.clear()
        # Sinaliza task de tratamento de erros para encerrar
        self._failed_tasks.put_nowait(None)
        await self._failed_task

    def call_exception_handler(self, context):
        """
        Chama handler de exceções para uma tarefa que falhou.
        
        Args:
            context: Contexto da exceção
        """
        handler = self._exception_handler
        if handler is None:
            # Usa handler padrão do event loop
            handler = self._loop.call_exception_handler(context)
        else:
            # Usa handler customizado
            handler(self, context)

    @property
    def exception_handler(self):
        """Retorna o handler de exceções configurado"""
        return self._exception_handler

    def _done(self, job):
        """
        Callback chamado quando uma tarefa completa.
        
        Processo:
        1. Dispara evento de conclusão no Event Bus
        2. Remove tarefa da lista de ativas
        3. Se houver espaço e tarefas na fila, inicia próxima
        
        Args:
            job: Tarefa que completou
        """
        # Dispara evento de conclusão
        self.cbpi.bus.sync_fire("job/%s/done" % job.type, type=job.type, key=job.name)
        self._jobs.discard(job)  # Remove da lista
        
        # Se não houver tarefas na fila, não precisa fazer nada
        if not self.pending_count:
            return
        
        # Calcula quantas tarefas podem ser iniciadas
        # Se limit é None, pode iniciar todas
        ntodo = self._limit - self.active_count
        i = 0
        # Inicia tarefas da fila até preencher slots disponíveis
        while i < ntodo:
            if not self.pending_count:
                return
            new_job = self._pending.get_nowait()
            if new_job.closed:
                continue  # Pula tarefas já fechadas
            new_job._start()
            i += 1

    def is_running(self, name):

        for j in self._jobs:
            if name == j.name:
                return True
        return False

    async def _wait_failed(self):
        # a coroutine for waiting failed tasks
        # without awaiting for failed tasks async raises a warning
        while True:
            task = await self._failed_tasks.get()
            if task is None:
                return  # closing
            try:
                await task  # should raise exception
            except Exception:
                # Cleanup a warning
                # self.call_exception_handler() is already called
                # by Job._add_done_callback
                # Thus we caught an task exception and we are good citizens
                pass