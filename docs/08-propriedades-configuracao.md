# Propriedades e Configuração

Este guia detalha como usar propriedades configuráveis e o sistema de configuração do CraftBeerPi 5.

## Visão Geral

Propriedades permitem que componentes (atores, sensores, etapas, etc.) tenham configurações que podem ser ajustadas pelo usuário através da interface web.

## Decorador @parameters

Use o decorador `@parameters` para definir propriedades de um componente:

```python
from cbpi.api import *

@parameters([
    Property.Number(label="GPIO Pin", configurable=True),
    Property.Text(label="Name", configurable=True)
])
class MeuComponente(CBPiActor):
    pass
```

## Tipos de Propriedades

### Property.Number

Campo numérico.

```python
Property.Number(
    label="GPIO Pin",                    # Rótulo exibido
    configurable=True,                   # Se pode ser configurado
    default_value=18,                    # Valor padrão
    unit="",                             # Unidade (ex: "C", "V")
    description="Número do pino GPIO"   # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Number(label="Temperature", configurable=True, default_value=20, unit="C")
])
class MeuSensor(CBPiSensor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.temp = float(props.get("Temperature", 20))
```

### Property.Text

Campo de texto.

```python
Property.Text(
    label="MQTT Topic",                  # Rótulo
    configurable=True,                   # Se pode ser configurado
    default_value="cbpi/actor",          # Valor padrão
    description="Tópico MQTT"            # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Text(label="URL", configurable=True, default_value="http://example.com")
])
class HTTPSensor(CBPiSensor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.url = props.get("URL", "http://example.com")
```

### Property.Select

Lista de seleção (dropdown).

```python
Property.Select(
    label="Mode",                        # Rótulo
    options=["ON/OFF", "PWM", "Analog"], # Opções disponíveis
    description="Modo de operação"       # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Select(
        label="Interval",
        options=[1, 5, 10, 30, 60],
        description="Intervalo de leitura em segundos"
    )
])
class MeuSensor(CBPiSensor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.interval = int(props.get("Interval", 10))
```

### Property.Actor

Seleção de ator existente.

```python
Property.Actor(
    label="Heater",                      # Rótulo
    description="Aquecedor"              # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Actor(label="Heater", description="Aquecedor da panela")
])
class KettleLogic(CBPiKettleLogic):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.heater_id = props.get("Heater")
```

### Property.Sensor

Seleção de sensor existente.

```python
Property.Sensor(
    label="Temperature Sensor",          # Rótulo
    description="Sensor de temperatura" # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Sensor(label="Sensor", description="Sensor de temperatura")
])
class KettleLogic(CBPiKettleLogic):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.sensor_id = props.get("Sensor")
```

### Property.Kettle

Seleção de panela existente.

```python
Property.Kettle(
    label="Kettle",                     # Rótulo
    description="Panela de brassagem"    # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Kettle(label="Kettle", description="Panela")
])
class Step(CBPiStep):
    def __init__(self, cbpi, id, name, props, on_done):
        super().__init__(cbpi, id, name, props, on_done)
        self.kettle_id = props.get("Kettle")
```

### Property.Fermenter

Seleção de fermentador existente.

```python
Property.Fermenter(
    label="Fermenter",                   # Rótulo
    description="Fermentador"            # Descrição
)
```

**Exemplo:**
```python
@parameters([
    Property.Fermenter(label="Fermenter", description="Fermentador")
])
class FermenterStep(CBPiFermentationStep):
    def __init__(self, cbpi, id, name, props, on_done):
        super().__init__(cbpi, id, name, props, on_done)
        self.fermenter_id = props.get("Fermenter")
```

## Acessando Propriedades

### No __init__

```python
class MeuAtor(CBPiActor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        # Ler propriedade
        self.pin = int(props.get("GPIO Pin", 18))
        self.mode = props.get("Mode", "ON/OFF")
```

### Durante Execução

```python
async def run(self):
    # Ler propriedade durante execução
    interval = int(self.props.get("Interval", 10))
    await asyncio.sleep(interval)
```

### Escrever Propriedade

```python
# Atualizar propriedade
self.props["GPIO Pin"] = 20
```

## Exemplo Completo

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Number(
        label="GPIO Pin",
        configurable=True,
        default_value=18,
        description="Número do pino GPIO"
    ),
    Property.Select(
        label="Mode",
        options=["ON/OFF", "PWM"],
        description="Modo de operação"
    ),
    Property.Number(
        label="Frequency",
        configurable=True,
        default_value=1000,
        unit="Hz",
        description="Frequência PWM"
    ),
    Property.Actor(
        label="Backup Actor",
        description="Ator de backup (opcional)"
    )
])
class AdvancedGPIOActor(CBPiActor):
    """
    Atuador GPIO avançado com múltiplas propriedades.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        
        # Ler propriedades numéricas
        self.pin = int(props.get("GPIO Pin", 18))
        self.frequency = int(props.get("Frequency", 1000))
        
        # Ler propriedade de seleção
        self.mode = props.get("Mode", "ON/OFF")
        
        # Ler propriedade de ator (pode ser None)
        self.backup_actor_id = props.get("Backup Actor")
        
        logger.info("GPIO Actor inicializado: pin=%s, mode=%s" % (self.pin, self.mode))
    
    async def on(self, power=100):
        """
        Liga o atuador.
        """
        if self.mode == "PWM":
            # Modo PWM
            logger.info("GPIO %s ON (PWM): power=%s, freq=%s" % (self.pin, power, self.frequency))
        else:
            # Modo ON/OFF
            logger.info("GPIO %s ON" % self.pin)
        
        self.state = True
        
        # Se houver ator de backup, ligá-lo também
        if self.backup_actor_id:
            await self.actor_on(self.backup_actor_id)
    
    async def off(self):
        """
        Desliga o atuador.
        """
        logger.info("GPIO %s OFF" % self.pin)
        self.state = False
        
        # Desligar ator de backup também
        if self.backup_actor_id:
            await self.actor_off(self.backup_actor_id)
    
    def get_state(self):
        return dict(state=self.state, mode=self.mode)

def setup(cbpi):
    cbpi.plugin.register("Advanced GPIO Actor", AdvancedGPIOActor)
```

## Propriedades Dinâmicas

Você pode gerar opções dinamicamente:

```python
def get_available_sensors():
    """
    Lista sensores disponíveis.
    """
    # Lógica para listar sensores
    return ["sensor1", "sensor2", "sensor3"]

@parameters([
    Property.Select(
        label="Sensor",
        options=get_available_sensors(),
        description="Sensor disponível"
    )
])
class MeuComponente(CBPiSensor):
    pass
```

## Validação de Propriedades

Valide propriedades no `__init__`:

```python
class MeuAtor(CBPiActor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        
        # Validar propriedade
        pin = int(props.get("GPIO Pin", 18))
        if pin < 1 or pin > 40:
            raise ValueError("GPIO Pin deve estar entre 1 e 40")
        
        self.pin = pin
```

## Sistema de Configuração

### Acessar Configuração Global

```python
# Obter valor de configuração
temp_unit = self.get_config_value("TEMP_UNIT", "C")

# Definir valor de configuração
await self.set_config_value("TEMP_UNIT", "F")

# Obter configuração estática
mqtt_enabled = self.get_static_config_value("mqtt", False)
```

### Adicionar Configuração

```python
from cbpi.api.config import ConfigType

# Adicionar nova configuração
await self.add_config_value(
    name="MEU_SETTING",
    value="default",
    type=ConfigType.STRING,
    description="Minha configuração",
    options=None
)
```

## Boas Práticas

1. **Sempre forneça valores padrão** com `props.get("key", default)`
2. **Valide propriedades** no `__init__`
3. **Use descrições claras** para ajudar usuários
4. **Forneça valores padrão** sensatos
5. **Documente** o que cada propriedade faz
6. **Use tipos apropriados** (Number para números, Text para texto)

## Recursos Adicionais

- [Criando Atores](03-criando-atores.md)
- [Criando Sensores](04-criando-sensores.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

