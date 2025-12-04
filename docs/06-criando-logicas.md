# Criando Lógicas de Controle

Este guia detalha como criar lógicas de controle para panelas e fermentadores.

## Visão Geral

Uma lógica de controle define como um dispositivo (panela ou fermentador) se comporta, como:
- **Hysteresis**: Liga/desliga baseado em temperatura
- **PID**: Controle proporcional-integral-derivativo
- **Manual**: Controle manual
- **Spunding**: Controle de pressão

## Tipos de Lógicas

### 1. Lógicas de Panela (CBPiKettleLogic)

Controlam o aquecimento de panelas de brassagem.

### 2. Lógicas de Fermentador (CBPiFermenterLogic)

Controlam temperatura e pressão de fermentadores.

## Classe Base: CBPiKettleLogic

```python
from cbpi.api import *

class MinhaLogica(CBPiKettleLogic):
    pass
```

## Métodos Obrigatórios

### run()

Método principal de controle (executado em loop).

```python
async def run(self):
    """
    Loop principal de controle.
    """
    while self.running:
        # Lógica de controle
        await asyncio.sleep(1)
```

## Propriedades Disponíveis

### self.cbpi

Instância principal do CraftBeerPi.

### self.id

ID da panela/fermentador.

### self.props

Propriedades configuráveis.

### self.state

Estado atual (True = controle ativo).

### self.running

Se o controle está em execução.

## Métodos Auxiliares

### get_kettle(kettle_id)

Obtém panela por ID.

```python
kettle = self.get_kettle(self.id)
```

### get_kettle_target_temp(kettle_id)

Obtém temperatura alvo da panela.

```python
target_temp = self.get_kettle_target_temp(self.id)
```

### get_sensor_value(sensor_id)

Obtém valor do sensor.

```python
sensor_data = self.get_sensor_value(sensor_id)
temp = sensor_data.get("value", 0)
```

### actor_on(actor_id, power=100)

Liga um ator.

```python
await self.actor_on(self.heater, power=100)
```

### actor_off(actor_id)

Desliga um ator.

```python
await self.actor_off(self.heater)
```

### get_actor_state(actor_id)

Obtém estado de um ator.

```python
state = self.get_actor_state(self.heater)
```

## Exemplo: Lógica Hysteresis (Panela)

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import asyncio
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Number(label="OffsetOn", configurable=True, description="Offset para ligar aquecedor"),
    Property.Number(label="OffsetOff", configurable=True, description="Offset para desligar aquecedor")
])
class Hysteresis(CBPiKettleLogic):
    """
    Lógica de controle Hysteresis para panela.
    
    Liga o aquecedor quando temperatura está abaixo de (alvo - OffsetOn)
    Desliga quando temperatura atinge (alvo - OffsetOff)
    """
    
    async def run(self):
        """
        Loop principal de controle.
        """
        try:
            # Obter propriedades
            self.offset_on = float(self.props.get("OffsetOn", 2))
            self.offset_off = float(self.props.get("OffsetOff", 1))
            
            # Obter panela e aquecedor
            self.kettle = self.get_kettle(self.id)
            self.heater = self.kettle.heater
            
            logger.info("Hysteresis iniciado: offset_on=%s, offset_off=%s" % (self.offset_on, self.offset_off))
            
            while self.running:
                # Obter temperatura atual
                sensor_value = self.get_sensor_value(self.kettle.sensor)
                current_temp = sensor_value.get("value", 0)
                
                # Obter temperatura alvo
                target_temp = self.get_kettle_target_temp(self.id)
                
                # Lógica de controle
                if current_temp < target_temp - self.offset_on:
                    # Temperatura muito baixa - ligar aquecedor
                    await self.actor_on(self.heater)
                elif current_temp >= target_temp - self.offset_off:
                    # Temperatura adequada - desligar aquecedor
                    await self.actor_off(self.heater)
                
                # Aguardar 1 segundo antes da próxima verificação
                await asyncio.sleep(1)
        
        except asyncio.CancelledError:
            # Cancelamento normal
            pass
        except Exception as e:
            logger.error("Erro na lógica Hysteresis: %s" % e)
        finally:
            # Garantir que aquecedor está desligado
            self.running = False
            await self.actor_off(self.heater)

def setup(cbpi):
    cbpi.plugin.register("Hysteresis", Hysteresis)
```

## Exemplo: Lógica PID (Panela)

```python
@parameters([
    Property.Number(label="Kp", configurable=True, default_value=1.0, description="Ganho proporcional"),
    Property.Number(label="Ki", configurable=True, default_value=0.1, description="Ganho integral"),
    Property.Number(label="Kd", configurable=True, default_value=0.01, description="Ganho derivativo")
])
class PIDLogic(CBPiKettleLogic):
    """
    Lógica de controle PID para panela.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.integral = 0
        self.last_error = 0
        self.last_time = None
    
    async def run(self):
        """
        Loop principal de controle PID.
        """
        import time
        
        try:
            # Obter parâmetros PID
            self.kp = float(self.props.get("Kp", 1.0))
            self.ki = float(self.props.get("Ki", 0.1))
            self.kd = float(self.props.get("Kd", 0.01))
            
            # Obter panela e aquecedor
            self.kettle = self.get_kettle(self.id)
            self.heater = self.kettle.heater
            
            self.last_time = time.time()
            
            while self.running:
                # Obter temperatura atual e alvo
                sensor_value = self.get_sensor_value(self.kettle.sensor)
                current_temp = sensor_value.get("value", 0)
                target_temp = self.get_kettle_target_temp(self.id)
                
                # Calcular erro
                error = target_temp - current_temp
                
                # Calcular tempo decorrido
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time
                
                # Termo proporcional
                p_term = self.kp * error
                
                # Termo integral
                self.integral += error * dt
                i_term = self.ki * self.integral
                
                # Termo derivativo
                d_term = self.kd * ((error - self.last_error) / dt)
                self.last_error = error
                
                # Calcular potência (0-100)
                power = p_term + i_term + d_term
                power = max(0, min(100, power))  # Limitar entre 0 e 100
                
                # Aplicar potência
                if power > 0:
                    await self.actor_on(self.heater, power=int(power))
                else:
                    await self.actor_off(self.heater)
                
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error("Erro na lógica PID: %s" % e)
        finally:
            await self.actor_off(self.heater)

def setup(cbpi):
    cbpi.plugin.register("PID Logic", PIDLogic)
```

## Exemplo: Lógica de Fermentador (Hysteresis)

```python
from cbpi.api import CBPiFermenterLogic

@parameters([
    Property.Number(label="HeaterOffsetOn", configurable=True, description="Offset para ligar aquecedor"),
    Property.Number(label="HeaterOffsetOff", configurable=True, description="Offset para desligar aquecedor"),
    Property.Number(label="CoolerOffsetOn", configurable=True, description="Offset para ligar resfriador"),
    Property.Number(label="CoolerOffsetOff", configurable=True, description="Offset para desligar resfriador"),
    Property.Sensor(label="Sensor", description="Sensor de temperatura"),
    Property.Actor(label="Heater", description="Aquecedor"),
    Property.Actor(label="Cooler", description="Resfriador")
])
class FermenterHysteresis(CBPiFermenterLogic):
    """
    Lógica Hysteresis para fermentador (controle de temperatura).
    """
    
    async def run(self):
        """
        Loop principal de controle.
        """
        try:
            # Obter propriedades
            heater_on = float(self.props.get("HeaterOffsetOn", 2))
            heater_off = float(self.props.get("HeaterOffsetOff", 1))
            cooler_on = float(self.props.get("CoolerOffsetOn", 2))
            cooler_off = float(self.props.get("CoolerOffsetOff", 1))
            
            # Obter componentes
            sensor_id = self.props.get("Sensor")
            heater_id = self.props.get("Heater")
            cooler_id = self.props.get("Cooler")
            
            fermenter = self.get_fermenter(self.id)
            target_temp = fermenter.target_temp
            
            while self.running:
                # Obter temperatura atual
                sensor_value = self.get_sensor_value(sensor_id)
                current_temp = sensor_value.get("value", 0)
                
                # Controle de aquecedor
                if current_temp < target_temp - heater_on:
                    await self.actor_on(heater_id)
                elif current_temp >= target_temp - heater_off:
                    await self.actor_off(heater_id)
                
                # Controle de resfriador
                if current_temp > target_temp + cooler_on:
                    await self.actor_on(cooler_id)
                elif current_temp <= target_temp + cooler_off:
                    await self.actor_off(cooler_id)
                
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error("Erro na lógica de fermentador: %s" % e)
        finally:
            await self.actor_off(heater_id)
            await self.actor_off(cooler_id)

def setup(cbpi):
    cbpi.plugin.register("Fermenter Hysteresis", FermenterHysteresis)
```

## Exemplo: Controle de Pressão (Spunding)

```python
@parameters([
    Property.Number(label="SpundingOffsetOpen", configurable=True, description="Offset para abrir válvula"),
    Property.Number(label="SpundingOffsetClose", configurable=True, description="Offset para fechar válvula"),
    Property.Sensor(label="PressureSensor", description="Sensor de pressão"),
    Property.Actor(label="Valve", description="Válvula de alívio"),
    Property.Number(label="ValveRelease", configurable=True, default_value=2, description="Tempo de abertura em segundos"),
    Property.Number(label="Pause", configurable=True, default_value=5, description="Pausa entre aberturas em segundos")
])
class FermenterSpunding(CBPiFermenterLogic):
    """
    Lógica de controle de pressão (Spunding) para fermentador.
    """
    
    async def run(self):
        """
        Loop principal de controle de pressão.
        """
        try:
            # Obter propriedades
            offset_open = float(self.props.get("SpundingOffsetOpen", 1))
            offset_close = float(self.props.get("SpundingOffsetClose", 0.5))
            valve_release = int(self.props.get("ValveRelease", 2))
            pause = int(self.props.get("Pause", 5))
            
            # Obter componentes
            pressure_sensor_id = self.props.get("PressureSensor")
            valve_id = self.props.get("Valve")
            
            fermenter = self.get_fermenter(self.id)
            target_pressure = fermenter.target_pressure
            
            while self.running:
                # Obter pressão atual
                sensor_value = self.get_sensor_value(pressure_sensor_id)
                current_pressure = sensor_value.get("value", 0)
                
                # Controle de válvula
                if current_pressure > target_pressure + offset_open:
                    # Pressão muito alta - abrir válvula
                    await self.actor_on(valve_id)
                    await asyncio.sleep(valve_release)
                    await self.actor_off(valve_id)
                    await asyncio.sleep(pause)
                elif current_pressure <= target_pressure + offset_close:
                    # Pressão adequada - fechar válvula
                    await self.actor_off(valve_id)
                
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error("Erro no controle de pressão: %s" % e)
        finally:
            await self.actor_off(valve_id)

def setup(cbpi):
    cbpi.plugin.register("Fermenter Spunding", FermenterSpunding)
```

## Métodos Auxiliares para Fermentadores

### get_fermenter(fermenter_id)

Obtém fermentador por ID.

```python
fermenter = self.get_fermenter(self.id)
target_temp = fermenter.target_temp
target_pressure = fermenter.target_pressure
```

## Boas Práticas

1. **Sempre desligue atores** no `finally`
2. **Use intervalos apropriados** (1 segundo é comum)
3. **Trate exceções** adequadamente
4. **Log valores** para debug
5. **Valide propriedades** antes de usar
6. **Documente** comportamento da lógica

## Recursos Adicionais

- [Propriedades e Configuração](08-propriedades-configuracao.md)
- [Event Bus](09-event-bus.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

