import asyncio
import inspect
import logging
import yaml

from cbpi.api import *

"""
================================================================================
CLASSE: CBPiEventBus
================================================================================
Sistema de Event Bus para comunicação desacoplada entre componentes.

O Event Bus permite que componentes publiquem eventos e outros componentes
se inscrevam para receber esses eventos, seguindo o padrão pub/sub.

Funcionalidades:
- Registro de handlers por tópico (ex: "actor/update", "sensor/reading")
- Suporte a wildcards: '+' (single level) e '#' (multi level)
- Execução assíncrona de handlers
- Suporte a futures para handlers que retornam valores
- Handlers "once" que são executados apenas uma vez

Exemplo de uso:
    @eventbus("actor/update")
    async def on_actor_update(self, actor_id, **kwargs):
        # Handler será chamado quando evento "actor/update" for disparado
        pass
"""
class CBPiEventBus(object):


    """
    Classe interna: Node
    Representa um nó na árvore de tópicos.
    Usa estrutura de árvore para organizar tópicos hierarquicamente.
    """
    class Node(object):
        __slots__ = '_children', '_content'

        def __init__(self):
            self._children = {}  # Filhos do nó (próximos níveis do tópico)
            self._content = None  # Lista de handlers registrados neste nó

    """
    Classe interna: Content
    Armazena informações sobre um handler registrado.
    """
    class Content(object):
        def __init__(self, parent, topic, method, once, supports_future=False):
            self.parent = parent  # Nó pai na árvore
            self.method = method  # Método/função handler
            self.name = method.__name__  # Nome do método
            self.once = once  # Se True, handler é removido após primeira execução
            self.topic = topic  # Tópico completo
            self.supports_future = supports_future  # Se handler aceita parâmetro 'future'

    """
    Classe interna: Result
    Armazena resultado de um handler que retorna valor via future.
    """
    class Result:
        def __init__(self, result, timeout):
            self.result = result  # Resultado do handler
            self.timeout = timeout  # Se ocorreu timeout

    """
    Classe interna: ResultContainer
    Container para resultados de múltiplos handlers.
    Usado quando fire() é chamado com handlers que retornam valores.
    """
    class ResultContainer:
        def __init__(self, results, timeout=False):
            self.results = {}
            self.timeout = timeout
            self._jobs = set()
            # Processa futures dos handlers
            for key, value in results.items():
                if value.done() is True:
                    # Handler já completou
                    self.results[key] = CBPiEventBus.Result(value.result(), True)
                else:
                    # Handler ainda não completou
                    self.results[key] = CBPiEventBus.Result(None, False)

        def get(self, key):
            """Obtém resultado de um handler específico"""
            r = self.results.get(key)
            if r is None:
                raise CBPiException("Event Key %s not found." % key)
            return (r.result, r.timeout)


    def register(self, topic, method, once=False):
        """
        Registra um handler para um tópico.
        
        Args:
            topic: Tópico do evento (ex: "actor/update", "sensor/reading")
            method: Método/função a ser chamado quando evento for disparado
            once: Se True, handler é removido após primeira execução
        
        Processo:
        1. Verifica se método já está registrado
        2. Cria nós na árvore conforme necessário
        3. Detecta se handler suporta future (retorna valor)
        4. Adiciona handler ao nó correspondente
        """
        if method in self.registry:
            raise RuntimeError("Method %s already registerd. Please unregister first!" % method.__name__)
        self.logger.info("Topic %s", topic)

        # Navega pela árvore criando nós conforme necessário
        node = self._root
        for sym in topic.split('/'):
            node = node._children.setdefault(sym, self.Node())

        # Inicializa lista de handlers se necessário
        if not isinstance(node._content, list):
            node._content = []

        # Verifica se handler aceita parâmetro 'future' (para retornar valores)
        sig = inspect.signature(method)
        if "future" in sig.parameters:
            supports_future = True
        else:
            supports_future = False
        
        # Cria objeto Content e adiciona ao nó
        c = self.Content(node, topic, method, once, supports_future)
        node._content.append(c)
        self.registry[method] = c  # Registra no dicionário para busca rápida

    def get_callbacks(self, key):
        """
        Obtém todos os handlers registrados para um tópico específico.
        
        Args:
            key: Tópico completo (sem wildcards)
        
        Returns:
            Lista de objetos Content (handlers)
        """
        try:
            node = self._root
            # Navega pela árvore até o nó do tópico
            for sym in key.split('/'):
                node = node._children[sym]
            if node._content is None:
                raise KeyError(key)
            return node._content
        except KeyError:
            raise KeyError(key)

    def unregister(self, method):
        """
        Remove um handler do registro.
        
        Args:
            method: Método/função a ser removido
        """
        self.logger.info("Unregister %s", method.__name__)
        if method in self.registry:
            content = self.registry[method]
            # Encontra e remove da lista de handlers do nó
            clean_idx = None
            for idx, content_obj in enumerate(content.parent._content):
                if method == content_obj.method:
                    clean_idx = idx
                    break
            if clean_idx is not None:
                del content.parent._content[clean_idx]

    def __init__(self, loop, cbpi):
        """
        Inicializa o Event Bus.
        
        Args:
            loop: Event loop asyncio
            cbpi: Instância principal do CraftBeerPi
        """
        self.logger = logging.getLogger(__name__)
        self.cbpi = cbpi
        self._root = self.Node()  # Raiz da árvore de tópicos
        self.registry = {}  # Dicionário para busca rápida de métodos registrados
        self.docs = {}  # Documentação dos handlers
        if loop is not None:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()


    def sync_fire(self,topic: str,timeout=1, **kwargs):
        """
        Dispara um evento de forma assíncrona (não bloqueia).
        
        Args:
            topic: Tópico do evento
            timeout: Timeout em segundos
            **kwargs: Dados do evento
        """
        self.loop.create_task(self.fire(topic=topic, timeout=timeout, **kwargs))

    async def fire(self, topic: str, timeout=0.5, **kwargs):
        """
        Dispara um evento e executa todos os handlers registrados.
        
        Este método:
        1. Encontra todos os handlers que correspondem ao tópico (incluindo wildcards)
        2. Executa handlers assíncronos
        3. Remove handlers "once" após execução
        4. Espera por resultados de handlers que retornam valores (com timeout)
        
        Args:
            topic: Tópico do evento (ex: "actor/update/123")
            timeout: Timeout para esperar resultados (None = não espera)
            **kwargs: Dados do evento passados para os handlers
        
        Returns:
            ResultContainer com resultados dos handlers (se timeout não for None)
        """
        futures = {}  # Futures para handlers que retornam valores

        async def wait(futures):
            """Aguarda conclusão de todos os futures"""
            if(len(futures) > 0):
                await asyncio.wait(futures.values())

        # Itera sobre todos os handlers que correspondem ao tópico
        for e in self.iter_match(topic):
            content_array = e
            keep_idx = []  # Índices de handlers a manter (não são "once")
            
            for idx, content_obj in enumerate(content_array):
                # Executa handler se for função assíncrona
                if inspect.iscoroutinefunction(content_obj.method):
                    if content_obj.supports_future is True:
                        # Handler retorna valor via future
                        fut = self.loop.create_future()
                        futures["%s.%s" % (content_obj.method.__module__, content_obj.name)] = fut
                        self.loop.create_task(content_obj.method(**kwargs, topic = topic, future=fut))
                    else:
                        # Handler normal (não retorna valor)
                        self.loop.create_task(content_obj.method(**kwargs, topic=topic))
                else:
                    # Apenas funções assíncronas são suportadas
                    pass
                
                # Mantém handler se não for "once"
                if content_obj.once is False:
                    keep_idx.append(idx)

            # Remove handlers "once" que foram executados
            if len(keep_idx) < len(e):
                e[0].parent._content = [e[0].parent._content[i] for i in keep_idx]

        # Aguarda resultados se timeout foi especificado
        if timeout is not None:
            try:
                await asyncio.wait_for(wait(futures), timeout=timeout)
                is_timedout = False
            except asyncio.TimeoutError:
                is_timedout = True
            return self.ResultContainer(futures, is_timedout)


    def dump(self):
        """
        Retorna lista de todos os handlers registrados.
        
        Útil para debug e documentação da API.
        
        Returns:
            Lista de dicionários com informações dos handlers
        """
        def rec(node, i=0):
            """Recursão para percorrer a árvore"""
            result = []
            if node._content is not None:
                for c in node._content:
                    result.append(dict(topic=c.topic, supports_future=c.supports_future, 
                                    method=c.method.__name__, path=c.method.__module__, once=c.once))

            if node._children is not None:
                for c in node._children:
                    result = result + rec(node._children[c], i + 1)
            return result

        result = rec(self._root)
        return result

    def iter_match(self, topic):
        """
        Itera sobre todos os handlers que correspondem a um tópico.
        
        Suporta wildcards:
        - '+': corresponde a um nível (ex: "actor/+/update" corresponde a "actor/123/update")
        - '#': corresponde a múltiplos níveis (ex: "actor/#" corresponde a "actor/123/update/status")
        
        Args:
            topic: Tópico a ser pesquisado
        
        Yields:
            Lista de objetos Content (handlers) que correspondem ao tópico
        """
        lst = topic.split('/')
        normal = not topic.startswith('$')  # Tópicos começando com '$' têm comportamento especial

        def rec(node, i=0):
            """Recursão para encontrar handlers correspondentes"""
            if i == len(lst):
                # Chegou ao final do tópico - retorna handlers deste nó
                if node._content is not None:
                    yield node._content
            else:
                part = lst[i]
                # Match exato
                if part in node._children:
                    for content in rec(node._children[part], i + 1):
                        yield content
                # Wildcard '+' (single level)
                if '+' in node._children and (normal or i > 0):
                    for content in rec(node._children['+'], i + 1):
                        yield content
            # Wildcard '#' (multi level)
            if '#' in node._children and (normal or i > 0):
                content = node._children['#']._content
                if content is not None:
                    yield content

        return rec(self._root)

    def register_object(self, obj):
        """
        Registra automaticamente todos os métodos de um objeto que têm decorador @eventbus.
        
        Args:
            obj: Objeto a ser analisado
        """
        # Procura métodos com atributo "eventbus" (decorador @eventbus)
        for method in [getattr(obj, f) for f in dir(obj) if callable(getattr(obj, f)) and hasattr(getattr(obj, f), "eventbus")]:
            doc = None
            # Tenta extrair documentação YAML se disponível
            if method.__doc__ is not None:
                try:
                    doc = yaml.load(method.__doc__)
                    doc["topic"] = method.__getattribute__("topic")
                except:
                    pass
            # Registra o handler
            self.register(method.__getattribute__("topic"), method)