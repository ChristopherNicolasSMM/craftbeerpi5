# Criando Endpoints HTTP

Este guia detalha como criar endpoints HTTP customizados para a API REST do CraftBeerPi 5.

## Visão Geral

Endpoints HTTP permitem criar APIs REST customizadas que podem ser acessadas via HTTP ou integradas ao frontend.

## Decorador @request_mapping

Use o decorador `@request_mapping` para registrar endpoints automaticamente:

```python
from cbpi.api import *

class MeusEndpoints:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.register(self, "/meu-prefixo")
    
    @request_mapping(path="/", method="GET", auth_required=False)
    async def minha_rota(self, request):
        return web.json_response(data={"message": "Hello"})
```

## Parâmetros do Decorador

### path

Caminho da rota (obrigatório).

```python
@request_mapping(path="/", ...)           # Rota raiz
@request_mapping(path="/{id}", ...)      # Rota com parâmetro
@request_mapping(path="/list", ...)      # Rota específica
```

### method

Método HTTP (padrão: "GET").

```python
@request_mapping(path="/", method="GET")
@request_mapping(path="/", method="POST")
@request_mapping(path="/", method="PUT")
@request_mapping(path="/", method="DELETE")
```

### auth_required

Se requer autenticação (padrão: True).

```python
@request_mapping(path="/", auth_required=True)   # Requer login
@request_mapping(path="/", auth_required=False)  # Público
```

### json_schema

Schema para validação do corpo JSON (opcional).

```python
from voluptuous import Schema

schema = Schema({
    "name": str,
    "value": int
})

@request_mapping(path="/", method="POST", json_schema=schema)
async def minha_rota(self, request):
    pass
```

## Registrando Endpoints

### Método 1: Classe com __init__

```python
class MeusEndpoints:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        # Registrar com prefixo
        self.cbpi.register(self, "/api/meus-endpoints")
    
    @request_mapping(path="/", method="GET")
    async def listar(self, request):
        return web.json_response(data=[])
```

### Método 2: Função setup()

```python
def setup(cbpi):
    # Criar instância
    endpoints = MeusEndpoints(cbpi)
    # Endpoints são registrados automaticamente
```

## Exemplo: Endpoints de Ator Customizado

```python
# -*- coding: utf-8 -*-
from aiohttp import web
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

class ActorCustomEndpoints:
    """
    Endpoints HTTP customizados para atores.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.controller = cbpi.actor
        # Registrar endpoints em /api/actor-custom
        self.cbpi.register(self, "/actor-custom")
    
    @request_mapping(path="/", method="GET", auth_required=False)
    async def listar_atores(self, request):
        """
        GET /api/actor-custom/
        
        Lista todos os atores.
        """
        atores = self.controller.data
        data = [ator.to_dict() for ator in atores]
        return web.json_response(data=data)
    
    @request_mapping(path="/{id}", method="GET", auth_required=False)
    async def obter_ator(self, request):
        """
        GET /api/actor-custom/{id}
        
        Obtém um ator específico.
        """
        ator_id = request.match_info['id']
        ator = self.controller.find_by_id(ator_id)
        
        if ator is None:
            return web.json_response(
                status=404,
                data={"error": "Ator não encontrado"}
            )
        
        return web.json_response(data=ator.to_dict())
    
    @request_mapping(path="/", method="POST", auth_required=False)
    async def criar_ator(self, request):
        """
        POST /api/actor-custom/
        
        Cria um novo ator.
        """
        data = await request.json()
        
        # Validar dados
        if "name" not in data or "type" not in data:
            return web.json_response(
                status=400,
                data={"error": "Campos 'name' e 'type' são obrigatórios"}
            )
        
        # Criar ator
        from cbpi.api.dataclasses import Actor, Props
        ator = Actor(
            name=data.get("name"),
            type=data.get("type"),
            props=Props(data.get("props", {}))
        )
        
        # Adicionar ao controller
        resultado = await self.controller.add(ator)
        
        return web.json_response(data=resultado.to_dict(), status=201)
    
    @request_mapping(path="/{id}/toggle", method="POST", auth_required=False)
    async def alternar_ator(self, request):
        """
        POST /api/actor-custom/{id}/toggle
        
        Alterna estado do ator (liga/desliga).
        """
        ator_id = request.match_info['id']
        ator = self.controller.find_by_id(ator_id)
        
        if ator is None:
            return web.json_response(
                status=404,
                data={"error": "Ator não encontrado"}
            )
        
        # Alternar estado
        if ator.instance and ator.instance.state:
            await self.controller.stop(ator_id)
        else:
            await self.controller.start(ator_id)
        
        return web.json_response(data={"message": "Estado alternado"})

def setup(cbpi):
    # Endpoints são registrados automaticamente no __init__
    ActorCustomEndpoints(cbpi)
    logger.info("Endpoints customizados de ator registrados")
```

## Exemplo: Endpoint com Validação

```python
from voluptuous import Schema

# Schema de validação
create_sensor_schema = Schema({
    "name": str,
    "type": str,
    "props": dict
})

class SensorEndpoints:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.controller = cbpi.sensor
        self.cbpi.register(self, "/sensor-custom")
    
    @request_mapping(
        path="/",
        method="POST",
        auth_required=False,
        json_schema=create_sensor_schema
    )
    async def criar_sensor(self, request):
        """
        POST /api/sensor-custom/
        
        Cria um novo sensor com validação.
        """
        # Dados já foram validados pelo decorador
        data = await request.json()
        
        from cbpi.api.dataclasses import Sensor, Props
        sensor = Sensor(
            name=data["name"],
            type=data["type"],
            props=Props(data.get("props", {}))
        )
        
        resultado = await self.controller.add(sensor)
        return web.json_response(data=resultado.to_dict(), status=201)
```

## Exemplo: Endpoint com Parâmetros de Query

```python
class DataEndpoints:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.register(self, "/data")
    
    @request_mapping(path="/sensor/{id}", method="GET", auth_required=False)
    async def dados_sensor(self, request):
        """
        GET /api/data/sensor/{id}?limit=100&start=0
        
        Obtém dados históricos de um sensor.
        """
        sensor_id = request.match_info['id']
        
        # Obter parâmetros de query
        limit = int(request.query.get("limit", 100))
        start = int(request.query.get("start", 0))
        
        # Obter dados do log
        dados = self.cbpi.log.get_data(sensor_id, limit=limit, start=start)
        
        return web.json_response(data=dados)
```

## Exemplo: Endpoint com Upload de Arquivo

```python
class UploadEndpoints:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.register(self, "/upload")
    
    @request_mapping(path="/file", method="POST", auth_required=False)
    async def upload_arquivo(self, request):
        """
        POST /api/upload/file
        
        Faz upload de um arquivo.
        """
        # Obter dados multipart
        reader = await request.multipart()
        
        # Processar cada campo
        while True:
            field = await reader.next()
            if field is None:
                break
            
            if field.name == "file":
                # Salvar arquivo
                filename = field.filename
                upload_path = self.cbpi.config_folder.get_upload_file(filename)
                
                with open(upload_path, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        f.write(chunk)
                
                return web.json_response(data={
                    "message": "Arquivo enviado",
                    "filename": filename
                })
        
        return web.json_response(
            status=400,
            data={"error": "Nenhum arquivo enviado"}
        )
```

## Acessando Request

### Parâmetros de Rota

```python
@request_mapping(path="/{id}", method="GET")
async def minha_rota(self, request):
    item_id = request.match_info['id']  # Obter {id} da rota
    return web.json_response(data={"id": item_id})
```

### Query Parameters

```python
@request_mapping(path="/search", method="GET")
async def buscar(self, request):
    query = request.query.get("q", "")  # ?q=termo
    limit = int(request.query.get("limit", 10))
    return web.json_response(data={"query": query, "limit": limit})
```

### Corpo JSON

```python
@request_mapping(path="/", method="POST")
async def criar(self, request):
    data = await request.json()  # Obter JSON do corpo
    name = data.get("name")
    return web.json_response(data={"name": name})
```

### Headers

```python
@request_mapping(path="/", method="GET")
async def minha_rota(self, request):
    user_agent = request.headers.get("User-Agent")
    return web.json_response(data={"user_agent": user_agent})
```

## Respostas HTTP

### JSON Response

```python
# Resposta 200 OK
return web.json_response(data={"message": "Sucesso"})

# Resposta 201 Created
return web.json_response(data={"id": 123}, status=201)

# Resposta 404 Not Found
return web.json_response(
    status=404,
    data={"error": "Não encontrado"}
)

# Resposta 400 Bad Request
return web.json_response(
    status=400,
    data={"error": "Dados inválidos"}
)
```

### Text Response

```python
return web.Response(text="Hello World")
```

### File Response

```python
return web.FileResponse("/path/to/file.txt")
```

## Autenticação

### Endpoint Público

```python
@request_mapping(path="/public", auth_required=False)
async def publico(self, request):
    return web.json_response(data={"message": "Público"})
```

### Endpoint Protegido

```python
@request_mapping(path="/private", auth_required=True)
async def privado(self, request):
    # Usuário está autenticado
    return web.json_response(data={"message": "Privado"})
```

## Integração com Frontend

Endpoints registrados são automaticamente disponíveis no frontend:

```javascript
// No frontend (React)
const response = await fetch('/api/meus-endpoints/');
const data = await response.json();
```

## Boas Práticas

1. **Use validação** com `json_schema`
2. **Trate erros** adequadamente
3. **Retorne status codes** apropriados
4. **Documente** endpoints com docstrings
5. **Use prefixos** consistentes
6. **Valide entrada** antes de processar

## Recursos Adicionais

- [Criando Plugins](02-criando-plugins.md)
- [Event Bus](09-event-bus.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

