import logging
import weakref
from collections import defaultdict

import aiohttp
from aiohttp import web
from voluptuous import Schema

from cbpi.utils import json_dumps

"""
================================================================================
CLASSE: CBPiWebSocket
================================================================================
Gerencia conexões WebSocket para comunicação em tempo real com o frontend.

Funcionalidades:
- Mantém conexões WebSocket ativas com clientes
- Envia atualizações em tempo real (broadcast)
- Recebe comandos do frontend e dispara eventos no Event Bus
- Usa WeakSet para gerenciar clientes (limpeza automática de desconectados)

Fluxo:
1. Cliente conecta via /ws
2. Servidor envia confirmação de conexão
3. Cliente pode enviar comandos (tópicos + dados)
4. Servidor dispara eventos no Event Bus
5. Servidor envia atualizações para todos os clientes conectados
"""
class CBPiWebSocket:
    def __init__(self, cbpi) -> None:
        """
        Inicializa o gerenciador de WebSocket.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
        """
        self.cbpi = cbpi
        self._callbacks = defaultdict(set)  # Callbacks por tópico (não usado atualmente)
        self._clients = weakref.WeakSet()  # Conjunto de clientes conectados (WeakSet para limpeza automática)
        self.logger = logging.getLogger(__name__)
        
        # Registra rota WebSocket
        self.cbpi.app.add_routes([web.get('/ws', self.websocket_handler)])
        
        # Registra este objeto no Event Bus para receber eventos
        self.cbpi.bus.register_object(self)
        
        # Registra listener para todos os eventos (wildcard '#')
        # Quando qualquer evento é disparado, envia via WebSocket
        self.cbpi.bus.register("#", self.listen)


    async def listen(self, topic, **kwargs):
        """
        Handler do Event Bus - recebe eventos e envia via WebSocket.
        
        Este método é registrado no Event Bus com wildcard '#' para receber
        todos os eventos do sistema e enviá-los para os clientes WebSocket.
        
        Args:
            topic: Tópico do evento
            **kwargs: Dados do evento
        """
        data = dict(topic=topic, data=dict(**kwargs))
        self.logger.debug("PUSH %s " % data)
        self.send(data)

    def send(self, data, sorting=False):
        """
        Envia dados para todos os clientes WebSocket conectados (broadcast).
        
        Args:
            data: Dados a serem enviados (deve ter estrutura {topic: str, data: dict})
            sorting: Se True, ordena lista de dados por nome (útil para listas)
        """
        self.logger.debug("broadcast to ws clients. Data: %s" % data)
        for ws in self._clients:
            async def send_data(ws, data):
                """Função auxiliar para enviar dados a um cliente específico"""
                try:
                    # Ordena dados se solicitado (útil para listas de atores, sensores, etc.)
                    if sorting:
                        try:
                            data['data'].sort(key=lambda x: x.get('name').upper())
                        except:
                            pass
                    await ws.send_json(data=data, dumps=json_dumps)
                except Exception as e:
                    self.logger.error("Error with client %s: %s" % (ws, str(e)))

            # Cria task assíncrona para enviar a cada cliente
            self.cbpi.app.loop.create_task(send_data(ws, data))

    async def websocket_handler(self, request):
        """
        Handler principal para conexões WebSocket.
        
        Gerencia o ciclo de vida de uma conexão WebSocket:
        1. Aceita conexão
        2. Adiciona cliente à lista
        3. Envia confirmação de conexão
        4. Recebe mensagens do cliente e dispara eventos
        5. Remove cliente ao desconectar
        
        Args:
            request: Requisição HTTP que será upgradeada para WebSocket
        
        Returns:
            WebSocketResponse
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)  # Faz upgrade HTTP para WebSocket
        self._clients.add(ws)  # Adiciona à lista de clientes
        
        # Tenta obter informações do cliente (IP e porta)
        try:
            peername = request.transport.get_extra_info('peername')
            if peername is not None:
                host = peername[0]
                port = peername[1]
            else:
                host, port = "Unknowen"
            self.logger.info("Client Connected - Host: %s Port: %s  - client count: %s " % (host, port, len(self._clients)))
        except Exception as e:
            pass
        
        try:
            # Envia confirmação de conexão bem-sucedida
            await ws.send_json(data=dict(topic="connection/success"))
            
            # Loop principal - recebe mensagens do cliente
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Mensagem de texto recebida
                    msg_obj = msg.json()
                    
                    # Valida estrutura da mensagem (deve ter topic e data)
                    schema = Schema({"topic": str, "data": dict})
                    schema(msg_obj)

                    topic = msg_obj.get("topic")
                    data = msg_obj.get("data")
                    
                    if topic == "close":
                        # Cliente solicita fechamento
                        await ws.close()
                    else:
                        # Dispara evento no Event Bus com os dados recebidos
                        if data is not None:
                            await self.cbpi.bus.fire(topic=topic, **data)
                        else:
                            await self.cbpi.bus.fire(topic=topic)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error('ws connection closed with exception %s' % ws.exception())

        except Exception as e:
            self.logger.error("%s - Received Data %s" % (str(e), msg.data))

        finally:
            # Remove cliente da lista ao desconectar
            self._clients.discard(ws)

        self.logger.info("Web Socket Close")
        return ws
        
