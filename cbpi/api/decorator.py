from functools import wraps

from voluptuous import Schema

__all__ = ["request_mapping", "on_startup", "on_event", "action", "background_task", "parameters"]

from aiohttp_auth import auth

"""
================================================================================
DECORADORES DO CRAFTBEERPI
================================================================================
Este módulo contém decoradores que facilitam o registro automático de:
- Endpoints HTTP (request_mapping)
- Handlers de eventos (on_event)
- Tarefas em background (background_task)
- Inicializadores (on_startup)
- Ações customizadas (action)
"""

def composed(*decs):
    """
    Combina múltiplos decoradores em um único decorador.
    
    Útil para aplicar vários decoradores ao mesmo tempo.
    """
    def deco(f):
        for dec in reversed(decs):
            f = dec(f)
        return f
    return deco

def request_mapping(path, name=None, method="GET", auth_required=True, json_schema=None):
    """
    Decorador para registrar endpoints HTTP automaticamente.
    
    Este decorador marca métodos para serem registrados como rotas HTTP
    na aplicação web. O CraftBeerPi automaticamente descobre e registra
    esses métodos durante a inicialização.
    
    Args:
        path: Caminho da rota (ex: "/{id}", "/list")
        name: Nome da rota (opcional, para documentação)
        method: Método HTTP (GET, POST, PUT, DELETE)
        auth_required: Se True, requer autenticação
        json_schema: Schema para validação do corpo JSON (opcional)
    
    Exemplo:
        @request_mapping(path="/{id}", method="GET", auth_required=False)
        async def get_item(self, request):
            # Este método será registrado como GET /api/item/{id}
            pass
    """

    def on_http_request(path, name=None):
        def real_decorator(func):
            func.route = True
            func.path = path
            func.name = name
            func.method = method
            return func

        return real_decorator

    def validate_json_body(func):


        @wraps(func)
        async def wrapper(*args):

            if json_schema is not None:
                data = await args[-1].json()
                schema = Schema(json_schema)
                schema(data)

            return await func(*args)

        return wrapper



    if auth_required is True:
        return composed(
            on_http_request(path, name),
            auth.auth_required,
            validate_json_body

        )
    else:
        return composed(
            on_http_request(path, name),
            validate_json_body
        )

def on_event(topic):
    """
    Decorador para registrar handlers de eventos no Event Bus.
    
    Métodos decorados serão chamados automaticamente quando o evento
    correspondente for disparado.
    
    Args:
        topic: Tópico do evento (ex: "actor/update", "sensor/reading")
              Suporta wildcards: '+' (single level) e '#' (multi level)
    
    Exemplo:
        @on_event("actor/update")
        async def on_actor_update(self, actor_id, **kwargs):
            # Será chamado quando evento "actor/update" for disparado
            pass
    """
    def real_decorator(func):
        func.eventbus = True  # Marca como handler de evento
        func.topic = topic
        func.c = None
        return func

    return real_decorator

def action(key, parameters):
    """
    Decorador para registrar ações customizadas em recursos.
    
    Ações são métodos que podem ser chamados dinamicamente em recursos
    (atores, sensores, etc.) através da API.
    
    Args:
        key: Chave/nome da ação (ex: "reset", "calibrate")
        parameters: Schema de validação dos parâmetros
    
    Exemplo:
        @action("reset", {"confirm": bool})
        async def reset_sensor(self, confirm=False):
            # Esta ação pode ser chamada via API
            pass
    """
    def real_decorator(func):
        func.action = True  # Marca como ação
        func.key = key
        func.parameters = parameters
        return func

    return real_decorator

def parameters(parameter):
    """
    Decorador para definir parâmetros de configuração de um componente.
    
    Args:
        parameter: Schema de parâmetros
    """
    def real_decorator(func):
        func.cbpi_p = True
        func.cbpi_parameters = parameter
        return func
    return real_decorator

def background_task(name, interval):
    """
    Decorador para registrar tarefas em background.
    
    Tarefas decoradas serão executadas periodicamente em intervalos
    definidos, mesmo quando não há requisições HTTP.
    
    Args:
        name: Nome da tarefa
        interval: Intervalo em segundos entre execuções
    
    Exemplo:
        @background_task("cleanup_logs", 3600)
        async def cleanup_old_logs(self):
            # Executado a cada hora (3600 segundos)
            pass
    """
    def real_decorator(func):
        func.background_task = True  # Marca como tarefa em background
        func.name = name
        func.interval = interval
        return func
    return real_decorator

def on_startup(name, order=0):
    """
    Decorador para registrar métodos de inicialização.
    
    Métodos decorados serão executados durante a inicialização do sistema,
    na ordem especificada (menor order = executa primeiro).
    
    Args:
        name: Nome do inicializador
        order: Ordem de execução (0 = primeiro, maior = depois)
    
    Exemplo:
        @on_startup("init_database", order=1)
        async def init_database(self):
            # Executado durante inicialização, após inicializadores com order=0
            pass
    """
    def real_decorator(func):
        func.on_startup = True  # Marca como inicializador
        func.name = name
        func.order = order
        return func
    return real_decorator


def entry_exit(f):
    def new_f():

        f()

    return new_f