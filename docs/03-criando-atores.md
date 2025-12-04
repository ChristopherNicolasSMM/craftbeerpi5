# Criando Atores (Actors)

Este guia detalha como criar novos tipos de atuadores para o CraftBeerPi 5.

## Visão Geral

Um atuador (Actor) é um dispositivo que pode ser controlado pelo sistema, como:
- Bombas
- Aquecedores
- Válvulas
- Agitadores
- Relés GPIO
- Dispositivos MQTT

## Classe Base: CBPiActor

Todos os atuadores devem herdar de `CBPiActor`:

```python
from cbpi.api import *

class MeuAtor(CBPiActor):
    pass
```

## Métodos Obrigatórios

### on(power)

Liga o atuador com potência especificada.

```python
async def on(self, power=100):
    """
    Liga o atuador.
    
    Args:
        power: Potência entre 0 e 100
    """
    self.state = True
```

**Parâmetros:**
- `power` (int): Potência entre 0 e 100

**Responsabilidades:**
- Ligar fisicamente o dispositivo
- Atualizar `self.state = True`
- Implementar controle de potência se necessário

### off()

Desliga o atuador.

```python
async def off(self):
    """
    Desliga o atuador.
    """
    self.state = False
```

**Responsabilidades:**
- Desligar fisicamente o dispositivo
- Atualizar `self.state = False`

### get_state()

Retorna o estado atual do atuador.

```python
def get_state(self):
    """
    Retorna estado atual do atuador.
    
    Returns:
        dict: Dicionário com estado
    """
    return dict(state=self.state)
```

**Retorno:**
- `dict`: Dicionário com informações do estado

## Métodos Opcionais

### init()

Chamado após a criação do atuador para inicialização.

```python
def init(self):
    """
    Inicialização do atuador.
    """
    pass
```

### start()

Inicia o atuador (cria task assíncrona).

```python
async def start(self):
    """
    Inicia o atuador.
    """
    await super().start()
```

### stop()

Para o atuador.

```python
async def stop(self):
    """
    Para o atuador.
    """
    await super().stop()
```

### on_start()

Callback chamado quando o atuador é iniciado.

```python
async def on_start(self):
    """
    Callback de início.
    """
    pass
```

### on_stop()

Callback chamado quando o atuador é parado.

```python
async def on_stop(self):
    """
    Callback de parada.
    """
    pass
```

### run()

Método principal de execução (executado em loop).

```python
async def run(self):
    """
    Execução principal do atuador.
    """
    while self.running:
        # Lógica do atuador
        await asyncio.sleep(1)
```

### set_power(power)

Define potência do atuador sem ligar/desligar.

```python
async def set_power(self, power):
    """
    Define potência do atuador.
    
    Args:
        power: Potência entre 0 e 100
    """
    self.power = power
    return dict(power=self.power)
```

## Propriedades Disponíveis

### self.cbpi

Instância principal do CraftBeerPi.

```python
# Acessar controllers
self.cbpi.actor
self.cbpi.sensor
self.cbpi.kettle

# Acessar Event Bus
self.cbpi.bus

# Acessar WebSocket
self.cbpi.ws

# Acessar configuração
self.cbpi.config
```

### self.id

ID único do atuador.

### self.props

Propriedades configuráveis do atuador (objeto `Props`).

```python
# Ler propriedade
pin = self.props.get("GPIO Pin", 18)

# Escrever propriedade
self.props["GPIO Pin"] = 20
```

### self.state

Estado atual (True = ligado, False = desligado).

### self.power

Potência atual (0-100).

### self.running

Se o atuador está em execução.

## Decorador @parameters

Use o decorador `@parameters` para definir propriedades configuráveis:

```python
@parameters([
    Property.Number(label="GPIO Pin", configurable=True, description="Número do pino GPIO"),
    Property.Select(label="Mode", options=["ON/OFF", "PWM"], description="Modo de operação")
])
class GPIOActor(CBPiActor):
    pass
```

## Exemplo: Atuador GPIO Simples

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Number(label="GPIO Pin", configurable=True, description="Número do pino GPIO")
])
class GPIOActor(CBPiActor):
    """
    Atuador GPIO simples.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.pin = int(props.get("GPIO Pin", 18))
        logger.info("GPIO Actor inicializado: pin=%s" % self.pin)
    
    async def on(self, power=100):
        """
        Liga o GPIO.
        """
        logger.info("GPIO %s ON (power=%s)" % (self.pin, power))
        # Aqui você implementaria a lógica real do GPIO
        # Exemplo: GPIO.output(self.pin, GPIO.HIGH)
        self.state = True
    
    async def off(self):
        """
        Desliga o GPIO.
        """
        logger.info("GPIO %s OFF" % self.pin)
        # Aqui você implementaria a lógica real do GPIO
        # Exemplo: GPIO.output(self.pin, GPIO.LOW)
        self.state = False
    
    def get_state(self):
        """
        Retorna estado atual.
        """
        return dict(state=self.state)

def setup(cbpi):
    cbpi.plugin.register("GPIO Actor", GPIOActor)
```

## Exemplo: Atuador com PWM

```python
@parameters([
    Property.Number(label="GPIO Pin", configurable=True),
    Property.Number(label="Frequency", configurable=True, default_value=1000, description="Frequência PWM em Hz")
])
class GPIOPWMActor(CBPiActor):
    """
    Atuador GPIO com controle PWM.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.pin = int(props.get("GPIO Pin", 18))
        self.frequency = int(props.get("Frequency", 1000))
        self.pwm = None
    
    async def on(self, power=100):
        """
        Liga PWM com potência especificada.
        """
        self.power = power
        duty_cycle = int((power / 100.0) * 1023)
        logger.info("GPIO PWM %s ON: power=%s, duty_cycle=%s" % (self.pin, power, duty_cycle))
        # Implementar PWM real aqui
        self.state = True
    
    async def off(self):
        """
        Desliga PWM.
        """
        logger.info("GPIO PWM %s OFF" % self.pin)
        # Parar PWM aqui
        self.state = False
    
    async def set_power(self, power):
        """
        Ajusta potência do PWM.
        """
        self.power = power
        duty_cycle = int((power / 100.0) * 1023)
        logger.info("Ajustando potência: %s (duty_cycle=%s)" % (power, duty_cycle))
        # Ajustar PWM aqui
        return dict(power=self.power)
    
    def get_state(self):
        return dict(state=self.state, power=self.power)

def setup(cbpi):
    cbpi.plugin.register("GPIO PWM Actor", GPIOPWMActor)
```

## Exemplo: Atuador com Ações Customizadas

```python
@parameters([
    Property.Number(label="GPIO Pin", configurable=True)
])
class GPIOActorComAcoes(CBPiActor):
    """
    Atuador GPIO com ações customizadas.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.pin = int(props.get("GPIO Pin", 18))
    
    @action("PULSAR", {})
    async def pulsar(self, **kwargs):
        """
        Ação: Pulsa o atuador (liga e desliga rapidamente).
        """
        await self.on()
        await asyncio.sleep(0.5)
        await self.off()
        self.cbpi.notify("Pulso", "Atuador pulsado", NotificationType.INFO)
    
    @action("TESTAR", {})
    async def testar(self, **kwargs):
        """
        Ação: Testa o atuador.
        """
        logger.info("Testando atuador %s" % self.id)
        await self.on()
        await asyncio.sleep(2)
        await self.off()
    
    async def on(self, power=100):
        self.state = True
    
    async def off(self):
        self.state = False
    
    def get_state(self):
        return dict(state=self.state)

def setup(cbpi):
    cbpi.plugin.register("GPIO Actor com Ações", GPIOActorComAcoes)
```

## Exemplo: Atuador MQTT

```python
@parameters([
    Property.Text(label="MQTT Topic", configurable=True, description="Tópico MQTT"),
    Property.Text(label="ON Message", configurable=True, default_value="ON", description="Mensagem para ligar"),
    Property.Text(label="OFF Message", configurable=True, default_value="OFF", description="Mensagem para desligar")
])
class MQTTActor(CBPiActor):
    """
    Atuador controlado via MQTT.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.topic = props.get("MQTT Topic", "cbpi/actor/%s" % id)
        self.on_message = props.get("ON Message", "ON")
        self.off_message = props.get("OFF Message", "OFF")
    
    async def on(self, power=100):
        """
        Publica mensagem MQTT para ligar.
        """
        self.cbpi.push_update(self.topic, self.on_message)
        self.state = True
        logger.info("MQTT Actor %s ON via topic %s" % (self.id, self.topic))
    
    async def off(self):
        """
        Publica mensagem MQTT para desligar.
        """
        self.cbpi.push_update(self.topic, self.off_message)
        self.state = False
        logger.info("MQTT Actor %s OFF via topic %s" % (self.id, self.topic))
    
    def get_state(self):
        return dict(state=self.state)

def setup(cbpi):
    # Só registrar se MQTT estiver habilitado
    if str(cbpi.static_config.get("mqtt", False)).lower() == "true":
        cbpi.plugin.register("MQTT Actor", MQTTActor)
```

## Métodos Auxiliares Úteis

### Acessar Outros Componentes

```python
# Obter ator por ID
ator = self.get_actor(ator_id)
estado = self.get_actor_state(ator_id)

# Obter sensor por ID
sensor = self.get_sensor(sensor_id)
valor = self.get_sensor_value(sensor_id)

# Obter panela por ID
panela = self.get_kettle(panela_id)
temp_alvo = self.get_kettle_target_temp(panela_id)
```

### Controlar Outros Atores

```python
# Ligar outro ator
await self.actor_on(ator_id, power=100)

# Desligar outro ator
await self.actor_off(ator_id)
```

### Notificações

```python
from cbpi.api.dataclasses import NotificationType

# Enviar notificação
self.cbpi.notify("Título", "Mensagem", NotificationType.INFO)
self.cbpi.notify("Erro", "Algo deu errado", NotificationType.ERROR)
```

### Logging de Dados

```python
# Logar valor
self.log_data(valor)
```

## Boas Práticas

1. **Sempre atualize `self.state`** ao ligar/desligar
2. **Use logging** para debug e monitoramento
3. **Trate exceções** adequadamente
4. **Documente** métodos e propriedades
5. **Valide** propriedades no `__init__`
6. **Use async/await** para operações assíncronas

## Recursos Adicionais

- [Propriedades e Configuração](08-propriedades-configuracao.md)
- [Event Bus](09-event-bus.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

