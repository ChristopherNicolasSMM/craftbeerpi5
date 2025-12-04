# Criando Sensores

Este guia detalha como criar novos tipos de sensores para o CraftBeerPi 5.

## Visão Geral

Um sensor é um dispositivo que lê valores do ambiente, como:
- Sensores de temperatura (DS18B20, PT100, etc.)
- Sensores de pressão
- Sensores de nível
- Sensores HTTP/API
- Sensores MQTT
- Sensores customizados

## Classe Base: CBPiSensor

Todos os sensores devem herdar de `CBPiSensor`:

```python
from cbpi.api import *

class MeuSensor(CBPiSensor):
    pass
```

## Métodos Obrigatórios

### get_state()

Retorna o estado atual do sensor (valor e unidade).

```python
def get_state(self):
    """
    Retorna estado atual do sensor.
    
    Returns:
        dict: Dicionário com valor e unidade
    """
    return dict(value=self.value, unit="C")
```

**Retorno:**
- `dict`: Dicionário com informações do sensor (geralmente `value` e `unit`)

### get_value()

Retorna apenas o valor numérico do sensor.

```python
def get_value(self):
    """
    Retorna valor atual do sensor.
    
    Returns:
        float: Valor numérico
    """
    return self.value
```

### get_unit()

Retorna a unidade de medida.

```python
def get_unit(self):
    """
    Retorna unidade de medida.
    
    Returns:
        str: Unidade (ex: "C", "F", "PSI", "%")
    """
    return "C"
```

## Métodos Opcionais

### init()

Inicialização do sensor.

```python
def init(self):
    """
    Inicialização do sensor.
    """
    pass
```

### start()

Inicia a leitura contínua do sensor.

```python
async def start(self):
    """
    Inicia leitura do sensor.
    """
    await super().start()
```

### stop()

Para a leitura do sensor.

```python
async def stop(self):
    """
    Para leitura do sensor.
    """
    await super().stop()
```

### run()

Método principal de leitura (executado em loop).

```python
async def run(self):
    """
    Loop principal de leitura.
    """
    while self.running:
        # Ler sensor
        valor = self.ler_sensor()
        
        # Atualizar valor
        self.push_update(valor)
        
        # Logar valor
        self.log_data(valor)
        
        await asyncio.sleep(1)
```

## Métodos Auxiliares

### push_update(value, mqtt=True)

Envia atualização do valor via WebSocket e MQTT.

```python
self.push_update(25.5)  # Envia valor atual
```

**Parâmetros:**
- `value`: Valor a ser enviado
- `mqtt`: Se True, também publica via MQTT

### log_data(value)

Registra valor no log do sensor.

```python
self.log_data(25.5)  # Loga valor
```

## Propriedades Disponíveis

### self.cbpi

Instância principal do CraftBeerPi.

### self.id

ID único do sensor.

### self.props

Propriedades configuráveis.

### self.value

Valor atual do sensor (geralmente numérico).

### self.running

Se o sensor está em execução.

## Exemplo: Sensor Simples (Dummy)

```python
# -*- coding: utf-8 -*-
import asyncio
import random
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([])
class CustomSensor(CBPiSensor):
    """
    Sensor simples que gera valores aleatórios.
    """
    
    def __init__(self, cbpi, id, props):
        super(CustomSensor, self).__init__(cbpi, id, props)
        self.value = 0
    
    async def run(self):
        """
        Loop de leitura: gera valor aleatório a cada segundo.
        """
        while self.running:
            # Gerar valor aleatório entre 10 e 100
            self.value = random.randint(10, 100)
            
            # Logar valor
            self.log_data(self.value)
            
            # Enviar atualização via WebSocket
            self.push_update(self.value)
            
            # Aguardar 1 segundo
            await asyncio.sleep(1)
    
    def get_state(self):
        """
        Retorna estado atual.
        """
        return dict(value=self.value)
    
    def get_value(self):
        return self.value
    
    def get_unit(self):
        return ""

def setup(cbpi):
    cbpi.plugin.register("CustomSensor", CustomSensor)
```

## Exemplo: Sensor de Temperatura DS18B20 (OneWire)

```python
# -*- coding: utf-8 -*-
import asyncio
import os
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

def getSensors():
    """
    Lista sensores OneWire disponíveis.
    """
    try:
        arr = []
        for dirname in os.listdir('/sys/bus/w1/devices'):
            if dirname.startswith("28") or dirname.startswith("10"):
                arr.append(dirname)
        return arr
    except:
        return []

@parameters([
    Property.Select(label="Sensor", options=getSensors(), description="Sensor OneWire"),
    Property.Number(label="offset", configurable=True, default_value=0, description="Offset de calibração"),
    Property.Select(label="Interval", options=[1, 5, 10, 30, 60], description="Intervalo de leitura em segundos")
])
class OneWire(CBPiSensor):
    """
    Sensor de temperatura OneWire (DS18B20).
    """
    
    def __init__(self, cbpi, id, props):
        super(OneWire, self).__init__(cbpi, id, props)
        self.value = 0
        self.sensor_name = None
        self.interval = 60
        self.offset = 0
    
    async def start(self):
        """
        Inicia leitura do sensor.
        """
        await super().start()
        self.sensor_name = self.props.get("Sensor")
        self.interval = int(self.props.get("Interval", 60))
        self.offset = float(self.props.get("offset", 0))
    
    async def run(self):
        """
        Loop de leitura do sensor.
        """
        while self.running:
            try:
                if self.sensor_name is None:
                    await asyncio.sleep(1)
                    continue
                
                # Ler arquivo do sensor
                path = '/sys/bus/w1/devices/%s/w1_slave' % self.sensor_name
                with open(path, 'r') as f:
                    content = f.read()
                    if content.split('\n')[0].split(' ')[11] == "YES":
                        # Converter temperatura (valor vem em milésimos de grau)
                        temp = float(content.split("=")[-1]) / 1000
                        
                        # Aplicar offset
                        self.value = round((temp + self.offset), 2)
                        
                        # Logar e atualizar
                        self.log_data(self.value)
                        self.push_update(self.value)
            except Exception as e:
                logger.error("Erro ao ler sensor OneWire: %s" % e)
            
            await asyncio.sleep(self.interval)
    
    def get_state(self):
        return dict(value=self.value)
    
    def get_value(self):
        return self.value
    
    def get_unit(self):
        # Obter unidade de temperatura configurada
        unit = self.get_config_value("TEMP_UNIT", "C")
        return unit

def setup(cbpi):
    cbpi.plugin.register("OneWire", OneWire)
    # Carregar módulos do kernel se necessário
    try:
        import subprocess
        subprocess.call(["modprobe", "w1-gpio"])
        subprocess.call(["modprobe", "w1-therm"])
    except:
        pass
```

## Exemplo: Sensor HTTP

```python
# -*- coding: utf-8 -*-
import asyncio
import aiohttp
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Text(label="URL", configurable=True, description="URL do endpoint HTTP"),
    Property.Number(label="Interval", configurable=True, default_value=10, description="Intervalo em segundos"),
    Property.Text(label="JSON Path", configurable=True, default_value="temperature", description="Caminho JSON para o valor")
])
class HTTPSensor(CBPiSensor):
    """
    Sensor que lê valores de uma API HTTP.
    """
    
    def __init__(self, cbpi, id, props):
        super(HTTPSensor, self).__init__(cbpi, id, props)
        self.value = 0
        self.url = props.get("URL", "")
        self.interval = int(props.get("Interval", 10))
        self.json_path = props.get("JSON Path", "temperature")
    
    async def run(self):
        """
        Loop de leitura via HTTP.
        """
        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extrair valor do JSON
                            keys = self.json_path.split(".")
                            value = data
                            for key in keys:
                                value = value[key]
                            
                            self.value = float(value)
                            
                            # Logar e atualizar
                            self.log_data(self.value)
                            self.push_update(self.value)
                        else:
                            logger.warning("HTTP Sensor: Status %s" % response.status)
            except Exception as e:
                logger.error("Erro ao ler sensor HTTP: %s" % e)
            
            await asyncio.sleep(self.interval)
    
    def get_state(self):
        return dict(value=self.value)
    
    def get_value(self):
        return self.value
    
    def get_unit(self):
        return ""

def setup(cbpi):
    cbpi.plugin.register("HTTP Sensor", HTTPSensor)
```

## Exemplo: Sensor com Múltiplos Valores

```python
@parameters([
    Property.Number(label="Temperature", configurable=True, default_value=20),
    Property.Number(label="Humidity", configurable=True, default_value=50)
])
class MultiValueSensor(CBPiSensor):
    """
    Sensor que retorna múltiplos valores.
    """
    
    def __init__(self, cbpi, id, props):
        super(MultiValueSensor, self).__init__(cbpi, id, props)
        self.temperature = float(props.get("Temperature", 20))
        self.humidity = float(props.get("Humidity", 50))
    
    def get_state(self):
        """
        Retorna múltiplos valores.
        """
        return dict(
            temperature=self.temperature,
            humidity=self.humidity,
            unit_temp="C",
            unit_humidity="%"
        )
    
    def get_value(self):
        """
        Retorna valor principal (temperatura).
        """
        return self.temperature
    
    def get_unit(self):
        return "C"
```

## Métodos Auxiliares Úteis

### Acessar Configuração

```python
# Obter valor de configuração
unit = self.get_config_value("TEMP_UNIT", "C")

# Obter valor de configuração estática
mqtt_enabled = self.get_static_config_value("mqtt", False)
```

### Acessar Outros Componentes

```python
# Obter ator
ator = self.get_actor(ator_id)
estado = self.get_actor_state(ator_id)

# Obter panela
panela = self.get_kettle(panela_id)
temp_alvo = self.get_kettle_target_temp(panela_id)
```

## Boas Práticas

1. **Sempre use `push_update()`** após ler novo valor
2. **Use `log_data()`** para histórico
3. **Trate exceções** adequadamente
4. **Use intervalos apropriados** (não leia muito frequentemente)
5. **Valide valores** antes de atualizar
6. **Documente unidades** de medida

## Recursos Adicionais

- [Propriedades e Configuração](08-propriedades-configuracao.md)
- [Event Bus](09-event-bus.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

