"""
Módulo principal do CraftBeerPi 5
Gerencia a inicialização e configuração do servidor web e todos os controladores do sistema.
"""

import asyncio
import sys
# Configuração específica para Windows - necessário para compatibilidade com asyncio
try:
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
except ImportError:
    pass
import json
from voluptuous.schema_builder import message
from cbpi.api.dataclasses import NotificationType
from cbpi.controller.notification_controller import NotificationController
import logging
from os import urandom
import os
from cbpi import __version__, __codename__
from aiohttp import web
from aiohttp_auth import auth
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_swagger import setup_swagger
from cbpi.api.exceptions import CBPiException
from voluptuous import MultipleInvalid

from cbpi.controller.dashboard_controller import DashboardController
from cbpi.controller.job_controller import JobController
from cbpi.controller.actor_controller import ActorController
from cbpi.controller.config_controller import ConfigController
from cbpi.controller.kettle_controller import KettleController
from cbpi.controller.plugin_controller import PluginController
from cbpi.controller.sensor_controller import SensorController
from cbpi.controller.step_controller import StepController
from cbpi.controller.recipe_controller import RecipeController
from cbpi.controller.fermenter_recipe_controller import FermenterRecipeController
from cbpi.controller.upload_controller import UploadController
from cbpi.controller.fermentation_controller import FermentationController

from cbpi.controller.system_controller import SystemController
from cbpi.controller.satellite_controller import SatelliteController

from cbpi.controller.log_file_controller import LogController

from cbpi.eventbus import CBPiEventBus
from cbpi.http_endpoints.http_login import Login
from cbpi.utils import *
from cbpi.websocket import CBPiWebSocket
from cbpi.http_endpoints.http_actor import ActorHttpEndpoints

from cbpi.http_endpoints.http_config import ConfigHttpEndpoints
from cbpi.http_endpoints.http_dashboard import DashBoardHttpEndpoints
from cbpi.http_endpoints.http_kettle import KettleHttpEndpoints
from cbpi.http_endpoints.http_sensor import SensorHttpEndpoints
from cbpi.http_endpoints.http_step import StepHttpEndpoints
from cbpi.http_endpoints.http_recipe import RecipeHttpEndpoints
from cbpi.http_endpoints.http_fermenterrecipe import FermenterRecipeHttpEndpoints
from cbpi.http_endpoints.http_plugin import PluginHttpEndpoints
from cbpi.http_endpoints.http_system import SystemHttpEndpoints
from cbpi.http_endpoints.http_log import LogHttpEndpoints
from cbpi.http_endpoints.http_notification import NotificationHttpEndpoints
from cbpi.http_endpoints.http_upload import UploadHttpEndpoints
from cbpi.http_endpoints.http_fermentation import FermentationHttpEndpoints

import shortuuid
logger = logging.getLogger(__name__)

"""
================================================================================
MIDDLEWARE DE TRATAMENTO DE ERROS
================================================================================
Este middleware intercepta todas as requisições HTTP e trata erros de forma
centralizada, retornando respostas JSON padronizadas para diferentes tipos de
exceções.
"""
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = response.message
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
        message = ex.reason
    except CBPiException as ex:
        message = str(ex)
        return web.json_response(status=500, data={'error': message})
    except MultipleInvalid as ex:
        return web.json_response(status=500, data={'error': str(ex)})
    except Exception as ex:
        return web.json_response(status=500, data={'error': str(ex)})

    return web.json_response(status=500, data={'error': message})


"""
================================================================================
CLASSE PRINCIPAL: CraftBeerPi
================================================================================
Esta é a classe central do sistema CraftBeerPi 5. Ela coordena todos os
componentes do sistema, incluindo:
- Controllers (atores, sensores, panelas, fermentadores, etc.)
- Endpoints HTTP (API REST)
- Sistema de plugins
- Event bus (comunicação entre componentes)
- WebSocket (comunicação em tempo real)
- Sistema de autenticação e sessões

Responsabilidades:
1. Inicializar todos os componentes do sistema
2. Configurar a aplicação web (aiohttp)
3. Registrar endpoints HTTP automaticamente
4. Gerenciar o ciclo de vida do sistema
5. Fornecer acesso centralizado aos controllers
"""
class CraftBeerPi:

    def __init__(self, configFolder):
        """
        Inicializa a instância principal do CraftBeerPi.
        
        Args:
            configFolder: Objeto ConfigFolder que gerencia a pasta de configuração
                         do sistema (geralmente './config')
        
        Processo de inicialização:
        1. Configura o event loop para Windows (se necessário)
        2. Carrega configurações estáticas do arquivo config.yaml
        3. Cria a aplicação web aiohttp com middlewares de segurança
        4. Inicializa todos os controllers do sistema
        5. Registra todos os endpoints HTTP
        6. Configura autenticação e sessões
        """

        # Configuração específica para Windows - ajusta o event loop policy
        # para melhor compatibilidade com asyncio no Windows
        operationsystem= sys.platform
        if operationsystem.startswith('win'):
            set_event_loop_policy(WindowsSelectorEventLoopPolicy())

        # Caminho do diretório do pacote cbpi
        self.path = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
        
        # Informações de versão do sistema
        self.version = __version__
        self.codename = __codename__

        # Configurações do sistema
        self.config_folder = configFolder  # Gerenciador de pasta de configuração
        self.static_config = load_config(configFolder.get_file_path("config.yaml"))  # Configurações do config.yaml
        
        logger.info("Init CraftBeerPI")

        # Configuração de autenticação e sessões
        # SessionTktAuthentication: autenticação baseada em tickets de sessão
        # urandom(32): gera uma chave secreta aleatória de 32 bytes para segurança
        # 60: timeout da sessão em segundos
        # include_ip=True: inclui o IP do cliente na validação da sessão
        policy = auth.SessionTktAuthentication(urandom(32), 60, include_ip=True)
        
        # Middlewares da aplicação web (executados em ordem):
        # 1. normalize_path_middleware: normaliza caminhos de URL
        # 2. session_middleware: gerencia sessões HTTP com cookies criptografados
        # 3. auth.auth_middleware: middleware de autenticação
        # 4. error_middleware: tratamento centralizado de erros
        middlewares = [web.normalize_path_middleware(), session_middleware(EncryptedCookieStorage(urandom(32))),
                       auth.auth_middleware(policy), error_middleware]
        
        # Cria a aplicação web aiohttp
        # client_max_size: tamanho máximo de upload aumentado para 5MB 
        # (padrão é 1MB) para permitir upload de configurações e arquivos SVG
        self.app = web.Application(middlewares=middlewares, client_max_size=5*1024*1024)
        self.app["cbpi"] = self  # Armazena referência à instância principal na app

        # Configura hook de shutdown para limpeza ao encerrar
        self._setup_shutdownhook()
        self.initializer = []  # Lista de métodos a serem executados na inicialização

        # ========================================================================
        # INICIALIZAÇÃO DOS CONTROLLERS (Componentes Principais do Sistema)
        # ========================================================================
        
        # Event Bus: Sistema de comunicação por eventos entre componentes
        # Permite que componentes publiquem e subscrevam eventos
        self.bus = CBPiEventBus(self.app.loop, self)
        
        # Job Controller: Gerencia tarefas em background e agendamento
        self.job = JobController(self)
        
        # Config Controller: Gerencia configurações dinâmicas do sistema
        self.config = ConfigController(self)
        
        # WebSocket: Comunicação em tempo real com o frontend
        self.ws = CBPiWebSocket(self)
        
        # Actor Controller: Gerencia atuadores (bombas, aquecedores, válvulas, etc.)
        self.actor = ActorController(self)
        
        # Sensor Controller: Gerencia sensores (temperatura, pressão, etc.)
        self.sensor = SensorController(self)
        
        # Plugin Controller: Gerencia plugins e extensões do sistema
        self.plugin = PluginController(self)
        
        # Log Controller: Gerencia logs do sistema
        self.log = LogController(self)
        
        # System Controller: Operações do sistema (backup, restart, etc.)
        self.system = SystemController(self)
        
        # Kettle Controller: Gerencia panelas de brassagem
        self.kettle = KettleController(self)
        
        # Fermentation Controller: Gerencia fermentadores
        self.fermenter : FermentationController = FermentationController(self)
        
        # Step Controller: Gerencia etapas do processo de brassagem
        self.step : StepController = StepController(self)
        
        # Recipe Controller: Gerencia receitas de cerveja
        self.recipe : RecipeController = RecipeController(self)
        
        # Fermenter Recipe Controller: Gerencia receitas de fermentação
        self.fermenterrecipe : FermenterRecipeController = FermenterRecipeController(self)
        
        # Upload Controller: Gerencia uploads de arquivos
        self.upload : UploadController = UploadController(self)
        
        # Notification Controller: Gerencia notificações do sistema
        self.notification : NotificationController = NotificationController(self)
        
        # Satellite Controller: Comunicação MQTT (opcional, só se habilitado)
        self.satellite = None
        if str(self.static_config.get("mqtt", False)).lower() == "true":
            self.satellite: SatelliteController = SatelliteController(self)
        
        # Dashboard Controller: Gerencia dashboards personalizados
        self.dashboard = DashboardController(self)

        # ========================================================================
        # INICIALIZAÇÃO DOS ENDPOINTS HTTP (API REST)
        # ========================================================================
        # Cada endpoint HTTP expõe uma API REST para interação com os controllers
        # Os endpoints são registrados automaticamente na aplicação web
        
        self.http_step = StepHttpEndpoints(self)  # API para etapas de brassagem
        self.http_recipe = RecipeHttpEndpoints(self)  # API para receitas
        self.http_fermenterrecipe = FermenterRecipeHttpEndpoints(self)  # API para receitas de fermentação
        self.http_sensor = SensorHttpEndpoints(self)  # API para sensores
        self.http_config = ConfigHttpEndpoints(self)  # API para configurações
        self.http_actor = ActorHttpEndpoints(self)  # API para atuadores
        self.http_kettle = KettleHttpEndpoints(self)  # API para panelas
        self.http_dashboard = DashBoardHttpEndpoints(self)  # API para dashboards
        self.http_plugin = PluginHttpEndpoints(self)  # API para plugins
        self.http_system = SystemHttpEndpoints(self)  # API para operações do sistema
        self.http_log = LogHttpEndpoints(self)  # API para logs
        self.http_notification = NotificationHttpEndpoints(self)  # API para notificações
        self.http_upload = UploadHttpEndpoints(self)  # API para uploads
        self.http_fermenter = FermentationHttpEndpoints(self)  # API para fermentadores

        # Sistema de login e autenticação
        self.login = Login(self)

    def _setup_shutdownhook(self):
        """
        Configura o hook de shutdown do sistema.
        
        Este método registra uma função de limpeza que será executada quando
        a aplicação for encerrada, permitindo que componentes façam limpeza
        adequada de recursos.
        """
        self.shutdown = False

        async def on_cleanup(app):
            """Callback executado durante o shutdown da aplicação"""
            self.shutdown = True

        self.app.on_cleanup.append(on_cleanup)

    def register_on_startup(self, obj):
        """
        Registra métodos que devem ser executados durante a inicialização do sistema.
        
        Este método procura por métodos no objeto que tenham o decorador @on_startup
        e os adiciona à lista de inicializadores, que serão executados em ordem
        durante o processo de inicialização.
        
        Args:
            obj: Objeto a ser analisado para métodos de inicialização
        """
        # Procura por métodos que tenham o atributo "on_startup" (decorador)
        for method in [getattr(obj, f) for f in dir(obj) if
                       callable(getattr(obj, f)) and hasattr(getattr(obj, f), "on_startup")]:
            name = method.__getattribute__("name")  # Nome do inicializador
            order = method.__getattribute__("order")  # Ordem de execução
            self.initializer.append(dict(name=name, method=method, order=order))

    def register(self, obj, url_prefix=None, static=None):
        """
        Registra um objeto no sistema CraftBeerPi.
        
        Este é o método principal de registro de componentes. Ele automaticamente:
        1. Registra endpoints HTTP do objeto
        2. Registra o objeto no event bus
        3. Registra tarefas em background
        4. Registra métodos de inicialização
        
        Args:
            obj: Objeto a ser registrado (geralmente um controller ou plugin)
            url_prefix: Prefixo da URL para endpoints HTTP (ex: '/api/actor')
            static: Caminho para arquivos estáticos (opcional)
        
        Exemplo:
            cbpi.register(MeuController(), url_prefix='/api/meu')
        """
        self.register_http_endpoints(obj, url_prefix, static)  # Registra endpoints HTTP
        self.bus.register_object(obj)  # Registra no event bus
        # self.ws.register_object(obj)  # WebSocket (comentado)
        self.job.register_background_task(obj)  # Registra tarefas em background
        self.register_on_startup(obj)  # Registra métodos de inicialização

    def register_http_endpoints(self, obj, url_prefix=None, static=None):
        """
        Registra automaticamente endpoints HTTP de um objeto.
        
        Este método analisa um objeto procurando por métodos decorados com
        @request_mapping e os registra como rotas HTTP na aplicação web.
        
        Processo:
        1. Procura métodos com decorador @request_mapping
        2. Extrai método HTTP (GET, POST, PUT, DELETE) e caminho
        3. Cria rotas apropriadas
        4. Adiciona à aplicação principal ou sub-aplicação
        
        Args:
            obj: Objeto contendo métodos com decorador @request_mapping
            url_prefix: Prefixo da URL (ex: '/api/actor')
            static: Caminho para servir arquivos estáticos (opcional)
        """
        if url_prefix is None:
            logger.debug(
                "URL Prefix is None for %s. No endpoints will be registered. Please set / explicit if you want to add it to the root path" % obj)
            return
        
        routes = []
        # Procura métodos que tenham o atributo "route" (decorador @request_mapping)
        for method in [getattr(obj, f) for f in dir(obj) if
                       callable(getattr(obj, f)) and hasattr(getattr(obj, f), "route")]:
            http_method = method.__getattribute__("method")  # GET, POST, PUT, DELETE
            path = method.__getattribute__("path")  # Caminho da rota
            class_name = method.__self__.__class__.__name__
            logger.debug(
                "Register Endpoint : %s.%s %s %s%s " % (class_name, method.__name__, http_method, url_prefix, path))

            # Funções auxiliares para adicionar rotas conforme o método HTTP
            def add_post():
                routes.append(web.post(method.__getattribute__("path"), method))

            def add_get():
                routes.append(web.get(method.__getattribute__("path"), method, allow_head=False))

            def add_delete():
                routes.append(web.delete(path, method))

            def add_put():
                routes.append(web.put(path, method))

            # Switch para adicionar a rota conforme o método HTTP
            switcher = {
                "POST": add_post,
                "GET": add_get,
                "DELETE": add_delete,
                "PUT": add_put
            }
            switcher[http_method]()

        # Se o prefixo não for "/", cria uma sub-aplicação
        if url_prefix != "/":
            logger.debug("URL Prefix: %s " % (url_prefix,))
            sub = web.Application()
            sub.add_routes(routes)
            # Adiciona rota para arquivos estáticos se fornecido
            if static is not None:
                sub.add_routes([web.static('/static', static, show_index=True)])
            self.app.add_subapp(url_prefix, sub)
        else:
            # Adiciona rotas diretamente à aplicação principal
            self.app.add_routes(routes)

    def _swagger_setup(self):
        """
        Configura a documentação Swagger da API REST.
        
        Este método expõe automaticamente a documentação interativa da API
        através do Swagger UI, disponível em /api/doc após a inicialização.
        
        A documentação é gerada automaticamente a partir dos docstrings e
        decoradores @request_mapping dos endpoints.
        """
        long_description = """
        This is the api for CraftBeerPi
        """
        setup_swagger(self.app,
                      description=long_description,
                      title="CraftBeerPi",
                      api_version=self.version,
                      contact="info@craftbeerpi.com")


    def notify(self, title: str, message: str, type: NotificationType = NotificationType.INFO, action=[]) -> None:
        """
        Envia uma notificação para o sistema.
        
        Args:
            title: Título da notificação
            message: Mensagem da notificação
            type: Tipo da notificação (INFO, WARNING, ERROR, SUCCESS)
            action: Lista de ações disponíveis (opcional)
        """
        self.notification.notify(title, message, type, action)
        
    def push_update(self, topic, data, retain=False) -> None:
        """
        Publica uma atualização via MQTT (se habilitado).
        
        Args:
            topic: Tópico MQTT
            data: Dados a serem publicados (será convertido para JSON)
            retain: Se True, a mensagem será retida pelo broker MQTT
        """
        if self.satellite is not None:
            asyncio.create_task(self.satellite.publish(topic=topic, message=json.dumps(data), retain=retain))

    async def call_initializer(self, app):
        """
        Executa todos os métodos de inicialização registrados.
        
        Os inicializadores são executados em ordem (baseado no atributo 'order')
        durante o processo de inicialização do sistema. Isso permite que
        componentes configurem o sistema na ordem correta.
        
        Args:
            app: Aplicação web aiohttp
        """
        # Ordena inicializadores por ordem de execução
        self.initializer = sorted(self.initializer, key=lambda k: k['order'])
        for i in self.initializer:
            logger.info("CALL INITIALIZER %s - %s " % (i["name"], i["method"].__name__))
            await i["method"]()

    def _print_logo(self):
        """
        Imprime o logo ASCII do CraftBeerPi no log de inicialização.
        
        Usa a biblioteca pyfiglet para criar um logo em ASCII art
        com informações de versão e créditos.
        """
        from pyfiglet import Figlet
        f = Figlet(font='big')
        logger.info("\n%s" % f.renderText("CraftBeerPi %s " % self.version))
        logger.info("www.CraftBeerPi.com")
        logger.info("(c) 2021/2022 Manuel Fritsch / Alexander Vollkopf")

    def _setup_http_index(self):
        """
        Configura a rota raiz (/) e arquivos estáticos.
        
        A rota raiz redireciona para a URL configurada em config.yaml (index_url),
        ou retorna uma mensagem simples se não configurado.
        Também configura o servimento de arquivos estáticos da pasta cbpi/static.
        """
        async def http_index(request):
            """Handler para a rota raiz - redireciona para a interface web"""
            url = self.config.static.get("index_url")

            if url is not None:
                # Redireciona para a URL configurada (geralmente /cbpi_ui/static/index.html)
                raise web.HTTPFound(url)
            else:
                return web.Response(text="Hello from CraftbeerPi!")

        # Registra rota raiz e arquivos estáticos
        self.app.add_routes([web.get('/', http_index),
                             web.static('/static', os.path.join(os.path.dirname(__file__), "static"), show_index=True)])

    async def init_serivces(self):
        """
        Inicializa todos os serviços do sistema na ordem correta.
        
        Este método é chamado antes de iniciar o servidor web e garante que
        todos os componentes estejam prontos. A ordem de inicialização é importante
        pois alguns componentes dependem de outros.
        
        Ordem de inicialização:
        1. Logo e informações
        2. Job controller (tarefas em background)
        3. Config controller (configurações)
        4. Satellite/MQTT (se habilitado)
        5. Rotas HTTP básicas
        6. Plugins (carregamento)
        7. Controllers de domínio (fermenter, sensor, step, actor, kettle)
        8. Inicializadores customizados
        9. Dashboard
        10. Swagger (documentação API)
        11. Configuração de logging
        
        Returns:
            web.Application: Aplicação web aiohttp configurada e pronta
        """
        self._print_logo()

        # Inicialização dos controllers na ordem correta
        await self.job.init()  # Sistema de jobs/tarefas
        
        await self.config.init()  # Configurações dinâmicas
        
        # MQTT/Satellite (opcional)
        if self.satellite is not None:
            await self.satellite.init()
        
        # Configura rotas HTTP básicas (raiz e estáticos)
        self._setup_http_index()
        
        # Carrega plugins do sistema e do ambiente
        self.plugin.load_plugins()  # Plugins internos (cbpi/extension)
        self.plugin.load_plugins_from_evn()  # Plugins externos instalados
        
        # Inicializa controllers de domínio
        await self.fermenter.init()  # Fermentadores
        await self.sensor.init()  # Sensores
        await self.step.init()  # Etapas de brassagem
        await self.actor.init()  # Atuadores
        await self.kettle.init()  # Panelas
        
        # Executa inicializadores customizados (plugins podem registrar aqui)
        await self.call_initializer(self.app)
        
        # Dashboard (deve ser inicializado por último)
        await self.dashboard.init()

        # Configura documentação Swagger da API
        self._swagger_setup()

        # Configura nível de logging
        level = logging.INFO
        logger = logging.getLogger()
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

        return self.app

    def start(self):
        """
        Inicia o servidor web do CraftBeerPi.
        
        Este método:
        1. Inicializa todos os serviços (init_serivces)
        2. Inicia o servidor web aiohttp na porta configurada
        3. Bloqueia até que o servidor seja encerrado
        
        A porta é lida do arquivo config.yaml (padrão: 2202, mas geralmente 8000)
        """
        web.run_app(self.init_serivces(), port=self.static_config.get("port", 2202))
