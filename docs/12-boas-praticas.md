# Boas Práticas

Este guia lista boas práticas para desenvolver plugins e componentes para o CraftBeerPi 5.

## Código

### 1. Nomenclatura

- **Classes**: Use PascalCase (ex: `GPIOActor`, `TemperatureSensor`)
- **Funções/Métodos**: Use snake_case (ex: `get_sensor_value`, `actor_on`)
- **Variáveis**: Use snake_case (ex: `sensor_id`, `target_temp`)
- **Constantes**: Use UPPER_SNAKE_CASE (ex: `MAX_TEMPERATURE`, `DEFAULT_INTERVAL`)

### 2. Documentação

Sempre documente seu código:

```python
class MeuAtor(CBPiActor):
    """
    Descrição do atuador.
    
    Este atuador controla...
    """
    
    async def on(self, power=100):
        """
        Liga o atuador.
        
        Args:
            power: Potência entre 0 e 100
        """
        pass
```

### 3. Type Hints

Use type hints quando possível:

```python
from typing import Optional, Dict, Any

async def get_sensor_value(self, sensor_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém valor do sensor.
    
    Args:
        sensor_id: ID do sensor
    
    Returns:
        Dicionário com valor ou None
    """
    pass
```

### 4. Tratamento de Erros

Sempre trate erros adequadamente:

```python
async def run(self):
    try:
        # Código que pode falhar
        value = await self.ler_sensor()
    except SensorError as e:
        logger.error("Erro ao ler sensor: %s" % e)
        # Tratar erro específico
    except Exception as e:
        logger.error("Erro inesperado: %s" % e)
        # Tratar erro genérico
    finally:
        # Código de limpeza (sempre executado)
        await self.cleanup()
```

### 5. Logging

Use logging adequadamente:

```python
import logging

logger = logging.getLogger(__name__)

# Níveis de log
logger.debug("Mensagem de debug")      # Detalhado
logger.info("Mensagem informativa")     # Informação geral
logger.warning("Aviso")                 # Aviso
logger.error("Erro")                    # Erro
logger.critical("Erro crítico")         # Erro crítico
```

## Estrutura de Plugins

### 1. Organização

Organize seu código em módulos quando apropriado:

```
meu_plugin/
├── __init__.py          # Código principal
├── config.yaml          # Configuração
├── utils.py             # Funções auxiliares (opcional)
└── models.py            # Modelos de dados (opcional)
```

### 2. Separação de Responsabilidades

Separe lógica de negócio de implementação:

```python
# Bom
class GPIOActor(CBPiActor):
    async def on(self, power=100):
        self._ligar_gpio(power)
    
    def _ligar_gpio(self, power):
        # Lógica específica do GPIO
        pass

# Ruim
class GPIOActor(CBPiActor):
    async def on(self, power=100):
        # Toda a lógica misturada
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        # ...
```

## Propriedades

### 1. Valores Padrão

Sempre forneça valores padrão:

```python
# Bom
self.pin = int(props.get("GPIO Pin", 18))
self.interval = int(props.get("Interval", 10))

# Ruim
self.pin = int(props.get("GPIO Pin"))  # Pode falhar se não existir
```

### 2. Validação

Valide propriedades no `__init__`:

```python
def __init__(self, cbpi, id, props):
    super().__init__(cbpi, id, props)
    
    # Validar propriedade
    pin = int(props.get("GPIO Pin", 18))
    if pin < 1 or pin > 40:
        raise ValueError("GPIO Pin deve estar entre 1 e 40")
    
    self.pin = pin
```

## Assíncrono

### 1. Use async/await

Sempre use async/await para operações assíncronas:

```python
# Bom
async def run(self):
    while self.running:
        value = await self.ler_sensor()
        await asyncio.sleep(1)

# Ruim
async def run(self):
    while self.running:
        value = self.ler_sensor()  # Bloqueante
        time.sleep(1)  # Bloqueante
```

### 2. Evite Operações Bloqueantes

Evite operações bloqueantes em código assíncrono:

```python
# Bom
async def ler_sensor(self):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Ruim
async def ler_sensor(self):
    response = requests.get(url)  # Bloqueante
    return response.json()
```

## Performance

### 1. Intervalos Apropriados

Use intervalos apropriados para leituras:

```python
# Bom - sensor de temperatura
await asyncio.sleep(1)  # 1 segundo é suficiente

# Ruim - muito frequente
await asyncio.sleep(0.1)  # 10x por segundo é excessivo
```

### 2. Cache Quando Apropriado

Cache valores quando apropriado:

```python
class MeuSensor(CBPiSensor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self._cached_value = None
        self._cache_time = None
    
    async def run(self):
        while self.running:
            # Ler apenas se cache expirou
            if not self._cached_value or time.time() - self._cache_time > 5:
                self._cached_value = await self.ler_sensor()
                self._cache_time = time.time()
            
            self.push_update(self._cached_value)
            await asyncio.sleep(1)
```

## Segurança

### 1. Validação de Entrada

Sempre valide entrada de usuário:

```python
@request_mapping(path="/", method="POST")
async def criar_ator(self, request):
    data = await request.json()
    
    # Validar entrada
    if "name" not in data or not data["name"]:
        return web.json_response(
            status=400,
            data={"error": "Nome é obrigatório"}
        )
    
    # Continuar processamento
```

### 2. Sanitização

Sanitize dados quando necessário:

```python
def sanitize_filename(filename):
    """
    Remove caracteres perigosos do nome do arquivo.
    """
    import re
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename)
```

## Testes

### 1. Teste Seu Código

Teste seu plugin antes de distribuir:

```python
# test_meu_plugin.py
import pytest
from cbpi.api import *

def test_meu_ator():
    # Criar instância
    ator = MeuAtor(cbpi, "test-id", Props({"GPIO Pin": 18}))
    
    # Testar métodos
    assert ator.pin == 18
```

### 2. Teste Casos Extremos

Teste casos extremos:

```python
# Testar com valores inválidos
with pytest.raises(ValueError):
    ator = MeuAtor(cbpi, "test-id", Props({"GPIO Pin": 999}))
```

## Versionamento

### 1. Use Versionamento Semântico

Use versionamento semântico (MAJOR.MINOR.PATCH):

- **MAJOR**: Mudanças incompatíveis
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs

### 2. Documente Mudanças

Documente mudanças entre versões:

```markdown
## Changelog

### 1.1.0
- Adicionado suporte para PWM
- Corrigido bug na leitura de sensores

### 1.0.0
- Versão inicial
```

## Distribuição

### 1. README Completo

Inclua README completo:

```markdown
# Meu Plugin

Descrição do plugin.

## Instalação

pip install cbpi5-meu-plugin

## Uso

[Exemplos de uso]

## Configuração

[Configurações necessárias]
```

### 2. Licença

Inclua licença no seu plugin.

### 3. Dependências

Liste dependências em `requirements.txt`:

```
requests>=2.25.0
aiohttp>=3.7.0
```

## Recursos Adicionais

- [Criando Plugins](02-criando-plugins.md)
- [API Reference](13-api-reference.md)
- [Guia de Início Rápido](01-inicio-rapido.md)

