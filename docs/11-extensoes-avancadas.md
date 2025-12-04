# Extensões e Funcionalidades Avançadas

Este guia detalha funcionalidades avançadas do CraftBeerPi 5, incluindo extensões, páginas customizadas e integração com frontend.

## Visão Geral

Extensões permitem adicionar funcionalidades avançadas ao sistema, como:
- Páginas customizadas na interface web
- Widgets personalizados
- Integrações com serviços externos
- Funcionalidades complexas

## Classe CBPiExtension

Use `CBPiExtension` para criar extensões avançadas:

```python
from cbpi.api import *

class MinhaExtensao(CBPiExtension):
    def __init__(self, cbpi):
        super().__init__(cbpi)
        # Inicialização
```

## Exemplo: Extensão Básica

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

class MinhaExtensao(CBPiExtension):
    """
    Extensão de exemplo.
    """
    
    def __init__(self, cbpi):
        super().__init__(cbpi)
        logger.info("MinhaExtensao inicializada")
    
    async def init(self):
        """
        Inicialização assíncrona.
        """
        logger.info("MinhaExtensao inicializada (async)")

def setup(cbpi):
    cbpi.plugin.register("MinhaExtensao", MinhaExtensao)
```

## Adicionando Endpoints HTTP

Extensões podem adicionar endpoints HTTP:

```python
class MinhaExtensao(CBPiExtension):
    def __init__(self, cbpi):
        super().__init__(cbpi)
        # Registrar endpoints
        self.cbpi.register(self, "/minha-extensao")
    
    @request_mapping(path="/", method="GET", auth_required=False)
    async def minha_rota(self, request):
        return web.json_response(data={"message": "Hello from extension"})
```

## Integração com Frontend

### Servir Arquivos Estáticos

```python
class MinhaExtensao(CBPiExtension):
    def __init__(self, cbpi):
        super().__init__(cbpi)
        # Servir arquivos estáticos
        self.cbpi.app.router.add_static('/static/minha-extensao', path='static')
```

### Adicionar Rotas Frontend

O frontend do CraftBeerPi 5 é um projeto React separado. Para adicionar páginas customizadas:

1. **Criar componente React** no projeto frontend
2. **Registrar rota** no router do frontend
3. **Criar endpoint API** no backend

## Exemplo: Extensão com Endpoints

```python
# -*- coding: utf-8 -*-
from aiohttp import web
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

class DataExportExtension(CBPiExtension):
    """
    Extensão para exportar dados.
    """
    
    def __init__(self, cbpi):
        super().__init__(cbpi)
        # Registrar endpoints
        self.cbpi.register(self, "/export")
    
    @request_mapping(path="/sensors", method="GET", auth_required=False)
    async def export_sensors(self, request):
        """
        Exporta dados de sensores.
        """
        import json
        from datetime import datetime, timedelta
        
        # Obter parâmetros
        days = int(request.query.get("days", 7))
        sensor_id = request.query.get("sensor_id")
        
        # Obter dados
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # (implementar lógica de exportação)
        data = {
            "sensor_id": sensor_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": []
        }
        
        return web.json_response(data=data)
    
    @request_mapping(path="/actors", method="GET", auth_required=False)
    async def export_actors(self, request):
        """
        Exporta dados de atores.
        """
        atores = self.cbpi.actor.data
        data = [ator.to_dict() for ator in atores]
        return web.json_response(data=data)

def setup(cbpi):
    cbpi.plugin.register("DataExportExtension", DataExportExtension)
```

## Exemplo: Extensão com Event Handlers

```python
class MonitoringExtension(CBPiExtension):
    """
    Extensão de monitoramento.
    """
    
    def __init__(self, cbpi):
        super().__init__(cbpi)
        self.cbpi.bus.register_object(self)
        self.alerts = []
    
    @on_event("sensor/#")
    async def on_sensor_event(self, topic, **kwargs):
        """
        Monitora eventos de sensores.
        """
        sensor_id = kwargs.get("id")
        value = kwargs.get("value")
        
        # Verificar limites
        if value and value > 100:
            alert = {
                "sensor_id": sensor_id,
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            self.alerts.append(alert)
            
            # Notificar
            self.cbpi.notify(
                "Alerta",
                "Sensor %s acima de 100!" % sensor_id,
                NotificationType.WARNING
            )
    
    @request_mapping(path="/alerts", method="GET", auth_required=False)
    async def get_alerts(self, request):
        """
        Retorna alertas.
        """
        return web.json_response(data=self.alerts)

def setup(cbpi):
    cbpi.plugin.register("MonitoringExtension", MonitoringExtension)
```

## Exemplo: Integração com Serviço Externo

```python
import aiohttp

class CloudSyncExtension(CBPiExtension):
    """
    Sincroniza dados com serviço na nuvem.
    """
    
    def __init__(self, cbpi):
        super().__init__(cbpi)
        self.api_url = cbpi.static_config.get("cloud_api_url", "")
        self.api_key = cbpi.static_config.get("cloud_api_key", "")
        self.cbpi.bus.register_object(self)
    
    @background_task(name="Cloud Sync", interval=300)
    async def sync_to_cloud(self):
        """
        Sincroniza dados a cada 5 minutos.
        """
        if not self.api_url or not self.api_key:
            return
        
        try:
            # Preparar dados
            data = {
                "actors": [a.to_dict() for a in self.cbpi.actor.data],
                "sensors": [s.to_dict() for s in self.cbpi.sensor.data],
                "kettles": [k.to_dict() for k in self.cbpi.kettle.data]
            }
            
            # Enviar para API
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": "Bearer %s" % self.api_key}
                async with session.post(
                    "%s/sync" % self.api_url,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info("Dados sincronizados com sucesso")
                    else:
                        logger.error("Erro na sincronização: %s" % response.status)
        
        except Exception as e:
            logger.error("Erro ao sincronizar: %s" % e)
    
    @on_event("actor/update")
    async def on_actor_update(self, actor_id, **kwargs):
        """
        Sincroniza ator imediatamente quando atualizado.
        """
        # Sincronizar apenas este ator
        # (implementar lógica)

def setup(cbpi):
    cbpi.plugin.register("CloudSyncExtension", CloudSyncExtension)
```

## Adicionando Páginas Customizadas

Para adicionar páginas customizadas na interface web:

### 1. Criar Endpoint API

```python
class CustomPageExtension(CBPiExtension):
    def __init__(self, cbpi):
        super().__init__(cbpi)
        self.cbpi.register(self, "/custom-page")
    
    @request_mapping(path="/data", method="GET", auth_required=False)
    async def get_data(self, request):
        """
        Retorna dados para a página customizada.
        """
        return web.json_response(data={"message": "Dados da página customizada"})
```

### 2. Criar Componente React (no projeto frontend)

```javascript
// No projeto craftbeerpi5-ui
import React from 'react';

const CustomPage = () => {
  const [data, setData] = React.useState(null);

  React.useEffect(() => {
    fetch('/api/custom-page/data')
      .then(res => res.json())
      .then(data => setData(data));
  }, []);

  return (
    <div>
      <h1>Página Customizada</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

export default CustomPage;
```

### 3. Registrar Rota (no frontend)

```javascript
// No router do frontend
import CustomPage from './components/CustomPage';

<Route path="/custom-page" component={CustomPage} />
```

## Widgets Customizados

Para criar widgets customizados no dashboard:

1. **Criar componente React** no projeto frontend
2. **Registrar widget** no sistema de widgets
3. **Criar endpoint API** se necessário

## Boas Práticas

1. **Separe responsabilidades** (backend vs frontend)
2. **Use async/await** para operações assíncronas
3. **Trate erros** adequadamente
4. **Documente APIs** que você cria
5. **Use logging** para debug
6. **Considere performance** ao criar extensões

## Recursos Adicionais

- [Criando Endpoints HTTP](07-criando-endpoints.md)
- [Event Bus](09-event-bus.md)
- [Tarefas em Background](10-tarefas-background.md)
- [Boas Práticas](12-boas-praticas.md)

