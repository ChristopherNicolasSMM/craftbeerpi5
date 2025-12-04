# Event Bus e Comunicação

Este guia detalha como usar o sistema de Event Bus do CraftBeerPi 5 para comunicação entre componentes.

## Visão Geral

O Event Bus permite comunicação desacoplada entre componentes usando o padrão pub/sub (publicar/inscrever).

## Decorador @on_event

Use o decorador `@on_event` para registrar handlers de eventos:

```python
from cbpi.api import *

@on_event("actor/update")
async def on_actor_update(self, actor_id, **kwargs):
    """
    Handler chamado quando um ator é atualizado.
    """
    logger.info("Ator atualizado: %s" % actor_id)
```

## Publicando Eventos

### fire()

Dispara um evento e executa todos os handlers registrados.

```python
# Disparar evento
await self.cbpi.bus.fire(topic="actor/update", actor_id="123", state=True)

# Disparar evento sem aguardar
self.cbpi.bus.sync_fire(topic="actor/update", actor_id="123")
```

### Parâmetros

```python
await self.cbpi.bus.fire(
    topic="meu/evento",      # Tópico do evento
    timeout=0.5,             # Timeout para aguardar resultados
    **kwargs                 # Dados do evento
)
```

## Escutando Eventos

### Handler Simples

```python
@on_event("actor/update")
async def on_actor_update(self, actor_id, **kwargs):
    """
    Handler para evento actor/update.
    """
    logger.info("Ator %s atualizado" % actor_id)
```

### Handler com Future

Para handlers que retornam valores:

```python
@on_event("sensor/reading")
async def on_sensor_reading(self, sensor_id, future, **kwargs):
    """
    Handler que retorna valor.
    """
    value = self.get_sensor_value(sensor_id)
    future.set_result(value)
```

### Registrar Handler Manualmente

```python
def setup(cbpi):
    # Registrar handler manualmente
    cbpi.bus.register("meu/evento", minha_funcao_handler)
```

## Tópicos Comuns

### Atores

- `actor/update` - Ator atualizado
- `actor/{id}/on` - Ator ligado
- `actor/{id}/off` - Ator desligado

### Sensores

- `sensor/update` - Sensor atualizado
- `sensor/{id}/reading` - Leitura do sensor

### Panelas

- `kettle/update` - Panela atualizada
- `kettle/{id}/target_temp` - Temperatura alvo alterada

### Etapas

- `step/update` - Etapa atualizada
- `step/{id}/start` - Etapa iniciada
- `step/{id}/done` - Etapa completada

### Jobs

- `job/{type}/done` - Job completado

## Wildcards

### Single Level (+)

Corresponde a um nível do tópico:

```python
@on_event("actor/+/update")
async def on_any_actor_update(self, **kwargs):
    """
    Handler para qualquer ator atualizado.
    """
    pass
```

### Multi Level (#)

Corresponde a múltiplos níveis:

```python
@on_event("actor/#")
async def on_any_actor_event(self, **kwargs):
    """
    Handler para qualquer evento de ator.
    """
    pass
```

## Exemplo: Handler de Ator

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

class ActorMonitor:
    """
    Monitor que escuta eventos de atores.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        # Registrar handlers
        self.cbpi.bus.register_object(self)
    
    @on_event("actor/update")
    async def on_actor_update(self, actor_id, **kwargs):
        """
        Handler quando ator é atualizado.
        """
        logger.info("Ator %s foi atualizado" % actor_id)
        state = kwargs.get("state", False)
        logger.info("Estado: %s" % state)
    
    @on_event("actor/+/on")
    async def on_actor_on(self, **kwargs):
        """
        Handler quando qualquer ator é ligado.
        """
        actor_id = kwargs.get("actor_id")
        logger.info("Ator %s foi ligado" % actor_id)
    
    @on_event("actor/+/off")
    async def on_actor_off(self, **kwargs):
        """
        Handler quando qualquer ator é desligado.
        """
        actor_id = kwargs.get("actor_id")
        logger.info("Ator %s foi desligado" % actor_id)

def setup(cbpi):
    ActorMonitor(cbpi)
```

## Exemplo: Handler de Sensor

```python
class SensorLogger:
    """
    Logger que registra todas as leituras de sensores.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.bus.register_object(self)
    
    @on_event("sensor/#")
    async def on_sensor_event(self, topic, **kwargs):
        """
        Handler para qualquer evento de sensor.
        """
        sensor_id = kwargs.get("id")
        value = kwargs.get("value")
        
        logger.info("Sensor %s: %s (tópico: %s)" % (sensor_id, value, topic))
        
        # Fazer algo com o valor
        if value and value > 100:
            self.cbpi.notify(
                "Alerta",
                "Sensor %s acima de 100!" % sensor_id,
                NotificationType.WARNING
            )

def setup(cbpi):
    SensorLogger(cbpi)
```

## Exemplo: Evento Customizado

```python
class MeuPlugin:
    """
    Plugin que publica e escuta eventos customizados.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.bus.register_object(self)
    
    @on_event("meu/plugin/evento")
    async def on_meu_evento(self, data, **kwargs):
        """
        Handler para evento customizado.
        """
        logger.info("Evento recebido: %s" % data)
    
    async def publicar_evento(self):
        """
        Publica um evento customizado.
        """
        await self.cbpi.bus.fire(
            topic="meu/plugin/evento",
            data="dados do evento"
        )

def setup(cbpi):
    plugin = MeuPlugin(cbpi)
```

## Exemplo: Handler com Future

```python
@on_event("sensor/reading")
async def on_sensor_reading(self, sensor_id, future, **kwargs):
    """
    Handler que retorna valor do sensor.
    """
    try:
        sensor = self.cbpi.sensor.find_by_id(sensor_id)
        if sensor and sensor.instance:
            value = sensor.instance.get_value()
            future.set_result(value)
        else:
            future.set_exception(ValueError("Sensor não encontrado"))
    except Exception as e:
        future.set_exception(e)

# Chamar evento e aguardar resultado
result = await self.cbpi.bus.fire(
    topic="sensor/reading",
    sensor_id="123",
    timeout=5
)
value = result.get("sensor.reading")[0]  # Obter resultado
```

## Registrando Objeto

Registre todos os métodos `@on_event` de um objeto:

```python
class MeuObjeto:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        # Registrar todos os métodos @on_event
        self.cbpi.bus.register_object(self)
    
    @on_event("evento1")
    async def handler1(self, **kwargs):
        pass
    
    @on_event("evento2")
    async def handler2(self, **kwargs):
        pass
```

## Desregistrando Handler

```python
# Desregistrar método específico
self.cbpi.bus.unregister(minha_funcao_handler)
```

## Listando Handlers

```python
# Listar todos os handlers registrados
handlers = self.cbpi.bus.dump()
for handler in handlers:
    print("Tópico: %s, Método: %s" % (handler["topic"], handler["method"]))
```

## Boas Práticas

1. **Use tópicos descritivos** (ex: `actor/update` em vez de `update`)
2. **Documente eventos** que seu plugin publica
3. **Trate exceções** em handlers
4. **Use wildcards** com cuidado (podem ser lentos)
5. **Evite loops infinitos** (não publique eventos em handlers do mesmo evento)

## Recursos Adicionais

- [Criando Plugins](02-criando-plugins.md)
- [Tarefas em Background](10-tarefas-background.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

