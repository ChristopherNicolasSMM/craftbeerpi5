# Referência da API

Referência completa da API do CraftBeerPi 5 para desenvolvedores.

## Classes Principais

### CBPiActor

Classe base para atuadores.

**Métodos obrigatórios:**
- `async def on(self, power=100)`: Liga o atuador
- `async def off(self)`: Desliga o atuador
- `def get_state(self)`: Retorna estado atual

**Métodos opcionais:**
- `def init(self)`: Inicialização
- `async def start(self)`: Inicia atuador
- `async def stop(self)`: Para atuador
- `async def run(self)`: Loop principal
- `async def set_power(self, power)`: Define potência

**Propriedades:**
- `self.cbpi`: Instância do CraftBeerPi
- `self.id`: ID do atuador
- `self.props`: Propriedades configuráveis
- `self.state`: Estado (True/False)
- `self.power`: Potência (0-100)
- `self.running`: Se está em execução

### CBPiSensor

Classe base para sensores.

**Métodos obrigatórios:**
- `def get_state(self)`: Retorna estado atual
- `def get_value(self)`: Retorna valor numérico
- `def get_unit(self)`: Retorna unidade

**Métodos opcionais:**
- `def init(self)`: Inicialização
- `async def start(self)`: Inicia leitura
- `async def stop(self)`: Para leitura
- `async def run(self)`: Loop principal

**Métodos auxiliares:**
- `def push_update(self, value, mqtt=True)`: Envia atualização
- `def log_data(self, value)`: Loga valor

### CBPiStep

Classe base para etapas.

**Métodos obrigatórios:**
- `async def run(self)`: Execução principal (retorna StepResult)

**Métodos disponíveis:**
- `async def next(self)`: Avança para próxima etapa
- `async def stop(self)`: Para etapa
- `async def push_update(self)`: Atualiza estado

**Propriedades:**
- `self.name`: Nome da etapa
- `self.summary`: Resumo (exibido na UI)
- `self.running`: Se está em execução
- `self.timer`: Timer opcional

### CBPiKettleLogic

Classe base para lógicas de panela.

**Métodos obrigatórios:**
- `async def run(self)`: Loop principal de controle

**Métodos auxiliares:**
- `get_kettle(kettle_id)`: Obtém panela
- `get_kettle_target_temp(kettle_id)`: Obtém temperatura alvo
- `get_sensor_value(sensor_id)`: Obtém valor do sensor
- `actor_on(actor_id, power=100)`: Liga ator
- `actor_off(actor_id)`: Desliga ator

### CBPiFermenterLogic

Classe base para lógicas de fermentador.

Similar a `CBPiKettleLogic`, mas para fermentadores.

**Métodos auxiliares:**
- `get_fermenter(fermenter_id)`: Obtém fermentador

## Decoradores

### @parameters

Define propriedades configuráveis.

```python
@parameters([
    Property.Number(label="GPIO Pin", configurable=True),
    Property.Text(label="Name", configurable=True)
])
```

### @request_mapping

Registra endpoint HTTP.

```python
@request_mapping(path="/", method="GET", auth_required=False)
async def minha_rota(self, request):
    pass
```

### @on_event

Registra handler de evento.

```python
@on_event("actor/update")
async def on_actor_update(self, actor_id, **kwargs):
    pass
```

### @action

Registra ação customizada.

```python
@action("RESET", {})
async def reset(self, **kwargs):
    pass
```

### @background_task

Registra tarefa em background.

```python
@background_task(name="Tarefa", interval=60)
async def minha_tarefa(self):
    pass
```

### @on_startup

Registra inicializador.

```python
@on_startup(name="Inicialização", order=0)
async def inicializar(self):
    pass
```

## Propriedades

### Property.Number

Campo numérico.

```python
Property.Number(
    label="GPIO Pin",
    configurable=True,
    default_value=18,
    unit="",
    description="Número do pino"
)
```

### Property.Text

Campo de texto.

```python
Property.Text(
    label="URL",
    configurable=True,
    default_value="",
    description="URL do endpoint"
)
```

### Property.Select

Lista de seleção.

```python
Property.Select(
    label="Mode",
    options=["ON/OFF", "PWM"],
    description="Modo de operação"
)
```

### Property.Actor

Seleção de ator.

```python
Property.Actor(
    label="Heater",
    description="Aquecedor"
)
```

### Property.Sensor

Seleção de sensor.

```python
Property.Sensor(
    label="Temperature Sensor",
    description="Sensor de temperatura"
)
```

### Property.Kettle

Seleção de panela.

```python
Property.Kettle(
    label="Kettle",
    description="Panela"
)
```

### Property.Fermenter

Seleção de fermentador.

```python
Property.Fermenter(
    label="Fermenter",
    description="Fermentador"
)
```

## Event Bus

### fire()

Dispara um evento.

```python
await self.cbpi.bus.fire(topic="meu/evento", data="valor")
```

### sync_fire()

Dispara evento sem aguardar.

```python
self.cbpi.bus.sync_fire(topic="meu/evento", data="valor")
```

### register()

Registra handler manualmente.

```python
self.cbpi.bus.register("meu/evento", minha_funcao)
```

### unregister()

Remove handler.

```python
self.cbpi.bus.unregister(minha_funcao)
```

## Controllers

### ActorController

Gerencia atores.

```python
# Adicionar ator
ator = Actor(name="Meu Ator", type="GPIOActor", props=Props({}))
await self.cbpi.actor.add(ator)

# Obter ator
ator = self.cbpi.actor.find_by_id(ator_id)

# Atualizar ator
await self.cbpi.actor.update(ator)

# Deletar ator
await self.cbpi.actor.delete(ator_id)

# Ligar ator
await self.cbpi.actor.start(ator_id)

# Desligar ator
await self.cbpi.actor.stop(ator_id)
```

### SensorController

Gerencia sensores.

```python
# Similar ao ActorController
await self.cbpi.sensor.add(sensor)
sensor = self.cbpi.sensor.find_by_id(sensor_id)
await self.cbpi.sensor.update(sensor)
await self.cbpi.sensor.delete(sensor_id)
```

### KettleController

Gerencia panelas.

```python
# Similar aos outros controllers
await self.cbpi.kettle.add(kettle)
kettle = self.cbpi.kettle.find_by_id(kettle_id)
await self.cbpi.kettle.set_target_temp(kettle_id, 65)
```

## Métodos Auxiliares

### Acessar Componentes

```python
# Obter ator
ator = self.get_actor(ator_id)
estado = self.get_actor_state(ator_id)

# Obter sensor
sensor = self.get_sensor(sensor_id)
valor = self.get_sensor_value(sensor_id)

# Obter panela
panela = self.get_kettle(panela_id)
temp_alvo = self.get_kettle_target_temp(panela_id)

# Obter fermentador
fermentador = self.get_fermenter(fermenter_id)
```

### Controlar Atores

```python
# Ligar ator
await self.actor_on(ator_id, power=100)

# Desligar ator
await self.actor_off(ator_id)
```

### Configuração

```python
# Obter configuração
valor = self.get_config_value("TEMP_UNIT", "C")

# Definir configuração
await self.set_config_value("TEMP_UNIT", "F")

# Obter configuração estática
valor = self.get_static_config_value("mqtt", False)
```

### Notificações

```python
from cbpi.api.dataclasses import NotificationType, NotificationAction

# Notificação simples
self.cbpi.notify("Título", "Mensagem", NotificationType.INFO)

# Notificação com ação
self.cbpi.notify(
    "Título",
    "Mensagem",
    NotificationType.INFO,
    action=[NotificationAction("Ação", callback)]
)
```

### WebSocket

```python
# Enviar dados via WebSocket
self.cbpi.ws.send({
    "topic": "meu/evento",
    "data": {"valor": 123}
})
```

### MQTT

```python
# Publicar no MQTT
self.cbpi.push_update("cbpi/topic", {"data": "valor"}, retain=True)
```

## Enums

### StepResult

Resultado de uma etapa.

```python
StepResult.DONE    # Etapa completou
StepResult.NEXT    # Avança para próxima
StepResult.STOP    # Para sequência
StepResult.ERROR   # Erro ocorreu
```

### StepState

Estado de uma etapa.

```python
StepState.INITIAL  # "I" - Não iniciada
StepState.ACTIVE   # "A" - Em execução
StepState.DONE     # "D" - Completa
StepState.ERROR    # "E" - Erro
StepState.STOP     # "S" - Parada
```

### NotificationType

Tipo de notificação.

```python
NotificationType.INFO     # Informação
NotificationType.WARNING   # Aviso
NotificationType.ERROR    # Erro
NotificationType.SUCCESS   # Sucesso
```

## Recursos Adicionais

- [Guia de Início Rápido](01-inicio-rapido.md)
- [Criando Plugins](02-criando-plugins.md)
- [Boas Práticas](12-boas-praticas.md)

