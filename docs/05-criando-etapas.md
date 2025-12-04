# Criando Etapas (Steps)

Este guia detalha como criar novos tipos de etapas para processos de brassagem e fermentação.

## Visão Geral

Uma etapa (Step) representa uma fase do processo, como:
- **Brassagem**: MashIn, Mash, Boil, Cooldown
- **Fermentação**: FermenterStep, RampTempStep
- **Ações**: Wait, Toggle, Notification

## Tipos de Etapas

### 1. Etapas de Brassagem (CBPiStep)

Etapas usadas no processo de brassagem.

### 2. Etapas de Fermentação (CBPiFermentationStep)

Etapas usadas no processo de fermentação.

## Classe Base: CBPiStep

```python
from cbpi.api import *
from cbpi.api.step import StepResult, StepState

class MinhaEtapa(CBPiStep):
    pass
```

## Métodos Obrigatórios

### run()

Método principal de execução da etapa.

```python
async def run(self):
    """
    Execução principal da etapa.
    
    Returns:
        StepResult: Resultado da etapa
    """
    while self.running:
        # Lógica da etapa
        await asyncio.sleep(1)
    
    return StepResult.DONE
```

**Retorno:**
- `StepResult.DONE`: Etapa completou
- `StepResult.NEXT`: Avança para próxima etapa
- `StepResult.STOP`: Para a sequência
- `StepResult.ERROR`: Erro ocorreu

## Estados da Etapa

### StepState

- `INITIAL ("I")`: Etapa não iniciada
- `ACTIVE ("A")`: Etapa em execução
- `DONE ("D")`: Etapa completada
- `ERROR ("E")`: Erro ocorreu
- `STOP ("S")`: Etapa parada

### StepResult

- `DONE`: Todas as etapas completaram
- `NEXT`: Avança para próxima etapa
- `STOP`: Para a sequência
- `ERROR`: Erro ocorreu

## Métodos Disponíveis

### next()

Avança para a próxima etapa.

```python
await self.next()
```

### stop()

Para a etapa atual.

```python
await self.stop()
```

### push_update()

Envia atualização de estado via WebSocket.

```python
await self.push_update()
```

## Propriedades Disponíveis

### self.cbpi

Instância principal do CraftBeerPi.

### self.id

ID único da etapa.

### self.name

Nome da etapa.

### self.props

Propriedades configuráveis.

### self.running

Se a etapa está em execução.

### self.summary

Resumo da etapa (exibido na UI).

### self.timer

Timer opcional para etapas com duração.

## Exemplo: Etapa de Espera (Wait)

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
from cbpi.api.step import StepResult
import asyncio
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Number(label="Duration", configurable=True, description="Duração em minutos")
])
class WaitStep(CBPiStep):
    """
    Etapa que aguarda um período de tempo.
    """
    
    async def on_start(self):
        """
        Inicialização da etapa.
        """
        self.duration = int(self.props.get("Duration", 10))  # minutos
        self.remaining = self.duration * 60  # converter para segundos
        self.summary = "Aguardando %s minutos" % self.duration
        await self.push_update()
    
    async def run(self):
        """
        Loop de espera.
        """
        while self.running and self.remaining > 0:
            # Atualizar resumo
            minutes = self.remaining // 60
            seconds = self.remaining % 60
            self.summary = "Aguardando: %02d:%02d" % (minutes, seconds)
            await self.push_update()
            
            # Aguardar 1 segundo
            await asyncio.sleep(1)
            self.remaining -= 1
        
        if self.remaining <= 0:
            self.summary = "Espera concluída"
            await self.push_update()
            return StepResult.DONE
        
        return StepResult.STOP
```

## Exemplo: Etapa de Notificação

```python
from cbpi.api.dataclasses import NotificationType, NotificationAction

@parameters([
    Property.Text(label="Notification", configurable=True, description="Texto da notificação"),
    Property.Select(label="AutoNext", options=["Yes", "No"], description="Avançar automaticamente?")
])
class NotificationStep(CBPiStep):
    """
    Etapa que exibe uma notificação.
    """
    
    async def NextStep(self, **kwargs):
        """
        Callback para avançar etapa.
        """
        await self.next()
    
    async def on_timer_done(self, timer):
        """
        Callback quando timer completa.
        """
        self.summary = self.props.get("Notification", "")
        auto_next = self.props.get("AutoNext", "No") == "Yes"
        
        if auto_next:
            # Avançar automaticamente
            self.cbpi.notify(
                self.name,
                self.props.get("Notification", ""),
                NotificationType.INFO
            )
            await self.next()
        else:
            # Mostrar notificação com botão
            self.cbpi.notify(
                self.name,
                self.props.get("Notification", ""),
                NotificationType.INFO,
                action=[NotificationAction("Next Step", self.NextStep)]
            )
            await self.push_update()
    
    async def on_start(self):
        """
        Inicia etapa.
        """
        self.summary = ""
        if self.timer is None:
            self.timer = Timer(1, on_done=self.on_timer_done)
        await self.push_update()
    
    async def on_stop(self):
        """
        Para etapa.
        """
        if self.timer:
            await self.timer.stop()
        self.summary = ""
        await self.push_update()
    
    async def run(self):
        """
        Execução principal.
        """
        while self.running:
            await asyncio.sleep(1)
            if self.timer and not self.timer.is_running:
                self.timer.start()
                self.timer.is_running = True
        
        return StepResult.DONE
```

## Exemplo: Etapa de Aquecimento (MashIn)

```python
@parameters([
    Property.Number(label="Temp", configurable=True, description="Temperatura alvo"),
    Property.Sensor(label="Sensor", description="Sensor de temperatura"),
    Property.Kettle(label="Kettle", description="Panela"),
    Property.Text(label="Notification", configurable=True, description="Notificação quando atingir temperatura"),
    Property.Select(label="AutoMode", options=["Yes", "No"], description="Ativar lógica automaticamente?")
])
class MashInStep(CBPiStep):
    """
    Etapa que aquece a panela até temperatura alvo.
    """
    
    async def NextStep(self, **kwargs):
        """
        Callback para avançar etapa.
        """
        await self.next()
    
    async def on_timer_done(self, timer):
        """
        Callback quando temperatura é atingida.
        """
        self.summary = ""
        self.kettle.target_temp = 0
        await self.push_update()
        
        if self.AutoMode:
            await self.setAutoMode(False)
        
        self.cbpi.notify(
            self.name,
            self.props.get("Notification", "Temperatura atingida!"),
            NotificationType.INFO,
            action=[NotificationAction("Next Step", self.NextStep)]
        )
    
    async def on_timer_update(self, timer, seconds):
        """
        Callback de atualização do timer.
        """
        await self.push_update()
    
    async def on_start(self):
        """
        Inicia etapa.
        """
        self.AutoMode = self.props.get("AutoMode", "No") == "Yes"
        self.kettle = self.get_kettle(self.props.get("Kettle", None))
        
        if self.kettle is not None:
            self.kettle.target_temp = int(self.props.get("Temp", 0))
        
        if self.AutoMode:
            await self.setAutoMode(True)
        
        self.summary = "Aguardando temperatura alvo"
        
        if self.timer is None:
            self.timer = Timer(1, on_update=self.on_timer_update, on_done=self.on_timer_done)
        
        await self.push_update()
    
    async def on_stop(self):
        """
        Para etapa.
        """
        if self.timer:
            await self.timer.stop()
        self.summary = ""
        if self.AutoMode:
            await self.setAutoMode(False)
        await self.push_update()
    
    async def run(self):
        """
        Execução principal.
        """
        while self.running:
            await asyncio.sleep(1)
            
            # Verificar se temperatura foi atingida
            sensor_id = self.props.get("Sensor")
            if sensor_id:
                sensor_value = self.get_sensor_value(sensor_id)
                target_temp = int(self.props.get("Temp", 0))
                
                if sensor_value and sensor_value.get("value", 0) >= target_temp:
                    if self.timer and not self.timer.is_running:
                        self.timer.start()
                        self.timer.is_running = True
            
            if self.timer and not self.timer.is_running:
                self.timer.start()
                self.timer.is_running = True
        
        return StepResult.DONE
```

## Exemplo: Etapa de Fervura (Boil)

```python
@parameters([
    Property.Number(label="Duration", configurable=True, description="Duração em minutos"),
    Property.Kettle(label="Kettle", description="Panela"),
    Property.Number(label="Temp", configurable=True, default_value=100, description="Temperatura de fervura")
])
class BoilStep(CBPiStep):
    """
    Etapa de fervura.
    """
    
    async def on_start(self):
        """
        Inicia fervura.
        """
        self.duration = int(self.props.get("Duration", 60))
        self.remaining = self.duration * 60
        self.kettle = self.get_kettle(self.props.get("Kettle", None))
        
        if self.kettle:
            self.kettle.target_temp = int(self.props.get("Temp", 100))
            await self.setAutoMode(True)
        
        self.summary = "Fervura: %s minutos" % self.duration
        await self.push_update()
    
    async def on_stop(self):
        """
        Para fervura.
        """
        if self.kettle:
            await self.setAutoMode(False)
        self.summary = ""
        await self.push_update()
    
    async def run(self):
        """
        Execução da fervura.
        """
        while self.running and self.remaining > 0:
            minutes = self.remaining // 60
            seconds = self.remaining % 60
            self.summary = "Fervura: %02d:%02d" % (minutes, seconds)
            await self.push_update()
            
            await asyncio.sleep(1)
            self.remaining -= 1
        
        if self.remaining <= 0:
            self.summary = "Fervura concluída"
            await self.push_update()
            return StepResult.DONE
        
        return StepResult.STOP
```

## Métodos Auxiliares

### Controlar Panela

```python
# Obter panela
kettle = self.get_kettle(kettle_id)

# Definir temperatura alvo
kettle.target_temp = 65

# Ativar/desativar lógica
await self.setAutoMode(True)
await self.setAutoMode(False)
```

### Ler Sensores

```python
# Obter valor do sensor
sensor_value = self.get_sensor_value(sensor_id)
temp = sensor_value.get("value", 0)
```

### Controlar Atores

```python
# Ligar ator
await self.actor_on(ator_id, power=100)

# Desligar ator
await self.actor_off(ator_id)
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
    action=[NotificationAction("Ação", callback_function)]
)
```

## Etapas de Fermentação (CBPiFermentationStep)

Similar a `CBPiStep`, mas para processos de fermentação:

```python
from cbpi.api.step import CBPiFermentationStep

class FermenterStep(CBPiFermentationStep):
    async def run(self):
        # Lógica da etapa
        return StepResult.DONE
```

## Boas Práticas

1. **Sempre atualize `self.summary`** para feedback visual
2. **Use `push_update()`** para atualizar a UI
3. **Trate cancelamentos** adequadamente
4. **Use timers** para etapas com duração
5. **Documente** propriedades e comportamento

## Recursos Adicionais

- [Propriedades e Configuração](08-propriedades-configuracao.md)
- [Event Bus](09-event-bus.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

