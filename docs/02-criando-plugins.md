# Criando Plugins

Este guia detalha como criar e estruturar plugins para o CraftBeerPi 5.

## Visão Geral

Um plugin é um módulo Python que estende as funcionalidades do CraftBeerPi. Plugins podem adicionar:
- Novos tipos de componentes (atores, sensores, etapas, etc.)
- Endpoints HTTP customizados
- Handlers de eventos
- Tarefas em background
- Extensões do sistema

## Tipos de Plugins

### 1. Plugins Internos

Plugins internos são incluídos no código-fonte do CraftBeerPi e ficam em `cbpi/extension/`.

**Estrutura:**
```
cbpi/extension/meu_plugin/
├── __init__.py
└── config.yaml
```

**Vantagens:**
- Fácil desenvolvimento e teste
- Não requer instalação separada
- Ideal para desenvolvimento

**Desvantagens:**
- Não podem ser instalados/desinstalados facilmente
- Requerem modificação do código-fonte

### 2. Plugins Externos

Plugins externos são pacotes Python instalados via pip. O nome deve começar com `cbpi`.

**Estrutura:**
```
cbpi5_meu_plugin/
├── setup.py
├── README.md
├── cbpi5_meu_plugin/
│   ├── __init__.py
│   └── ...
└── ...
```

**Vantagens:**
- Podem ser distribuídos via PyPI
- Fácil instalação/desinstalação
- Versionamento independente

**Desvantagens:**
- Requerem estrutura de pacote Python
- Mais complexos de desenvolver

## Estrutura de um Plugin

### Estrutura Mínima

```
meu_plugin/
├── __init__.py          # Código principal
└── config.yaml          # Configuração
```

### Estrutura Completa

```
meu_plugin/
├── __init__.py          # Código principal
├── config.yaml          # Configuração do plugin
├── README.md            # Documentação
├── requirements.txt     # Dependências (opcional)
└── static/             # Arquivos estáticos (opcional)
    └── ...
```

## Arquivo config.yaml

O arquivo `config.yaml` define as configurações do plugin:

```yaml
name: Nome do Plugin
version: 4              # Versão do CraftBeerPi (4 ou 5)
active: true            # Se o plugin está ativo
```

### Campos

- **name**: Nome do plugin (obrigatório)
- **version**: Versão do CraftBeerPi compatível (4 ou 5)
- **active**: Se `true`, o plugin será carregado (padrão: `true`)

### Exemplo

```yaml
name: GPIO Actor Plugin
version: 4
active: true
```

## Função setup()

A função `setup(cbpi)` é obrigatória e é chamada durante a inicialização do sistema.

### Assinatura

```python
def setup(cbpi):
    """
    Função chamada durante a inicialização do CraftBeerPi.
    
    Args:
        cbpi: Instância principal do CraftBeerPi
    """
    pass
```

### Responsabilidades

1. **Registrar Componentes**: Use `cbpi.plugin.register()` para registrar seus componentes
2. **Configuração Inicial**: Execute qualquer configuração necessária
3. **Registrar Eventos**: Registre handlers de eventos se necessário
4. **Registrar Endpoints**: Registre endpoints HTTP se necessário

### Exemplo Básico

```python
def setup(cbpi):
    # Registrar um atuador
    cbpi.plugin.register("MeuAtor", MeuAtor)
    
    # Registrar um sensor
    cbpi.plugin.register("MeuSensor", MeuSensor)
    
    # Registrar uma etapa
    cbpi.plugin.register("MinhaEtapa", MinhaEtapa)
```

### Exemplo Avançado

```python
def setup(cbpi):
    # Verificar se uma configuração está habilitada
    if cbpi.static_config.get("meu_plugin_enabled", False):
        cbpi.plugin.register("MeuAtor", MeuAtor)
    
    # Registrar extensão
    cbpi.plugin.register("MinhaExtensao", MinhaExtensao)
    
    # Registrar handler de evento
    @cbpi.bus.register("actor/update")
    async def on_actor_update(actor_id, **kwargs):
        logger.info("Ator atualizado: %s" % actor_id)
```

## Registrando Componentes

Use `cbpi.plugin.register(nome, classe)` para registrar componentes:

```python
cbpi.plugin.register("Nome do Componente", ClasseDoComponente)
```

O sistema automaticamente detecta o tipo baseado na classe:

- `CBPiActor` → Registrado como atuador
- `CBPiSensor` → Registrado como sensor
- `CBPiStep` → Registrado como etapa
- `CBPiKettleLogic` → Registrado como lógica de panela
- `CBPiFermenterLogic` → Registrado como lógica de fermentador
- `CBPiExtension` → Registrado como extensão

## Exemplo Completo de Plugin

### __init__.py

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([Property.Number(label="GPIO Pin", configurable=True, description="Número do pino GPIO")])
class GPIOActor(CBPiActor):
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.pin = int(props.get("GPIO Pin", 18))
    
    async def on(self, power=100):
        logger.info("GPIO %s ON" % self.pin)
        self.state = True
    
    async def off(self):
        logger.info("GPIO %s OFF" % self.pin)
        self.state = False
    
    def get_state(self):
        return dict(state=self.state)

def setup(cbpi):
    cbpi.plugin.register("GPIO Actor", GPIOActor)
    logger.info("GPIO Actor Plugin carregado")
```

### config.yaml

```yaml
name: GPIO Actor Plugin
version: 4
active: true
```

## Criando Plugin Externo (Pacote Python)

### Estrutura

```
cbpi5_meu_plugin/
├── setup.py
├── README.md
├── requirements.txt
└── cbpi5_meu_plugin/
    ├── __init__.py
    └── config.yaml
```

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="cbpi5-meu-plugin",
    version="1.0.0",
    description="Meu plugin para CraftBeerPi 5",
    author="Seu Nome",
    packages=find_packages(),
    install_requires=[
        "craftbeerpi5",
    ],
)
```

### __init__.py

```python
from cbpi.api import *

def setup(cbpi):
    cbpi.plugin.register("MeuComponente", MinhaClasse)
```

### Instalação

```bash
pip install cbpi5-meu-plugin
```

O CraftBeerPi automaticamente descobre e carrega plugins instalados que começam com `cbpi`.

## Boas Práticas

### 1. Nomenclatura

- Use nomes descritivos
- Evite espaços em nomes de classes
- Use PascalCase para classes
- Use snake_case para funções

### 2. Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Mensagem informativa")
logger.warning("Aviso")
logger.error("Erro")
logger.debug("Debug")
```

### 3. Tratamento de Erros

```python
try:
    # Código que pode falhar
    pass
except Exception as e:
    logger.error("Erro: %s" % e)
    # Tratar erro adequadamente
```

### 4. Documentação

```python
class MeuAtor(CBPiActor):
    """
    Descrição do atuador.
    
    Este atuador faz...
    """
    pass
```

### 5. Versionamento

- Use versionamento semântico (1.0.0, 1.1.0, 2.0.0)
- Documente mudanças entre versões
- Mantenha compatibilidade quando possível

## Debugging

### Verificar se Plugin foi Carregado

Verifique os logs durante a inicialização:

```
INFO - Trying to load plugin meu_plugin
INFO - Plugin meu_plugin loaded successfully
```

### Verificar Registro de Componentes

Use o endpoint da API:

```bash
curl http://localhost:8000/api/actor/types
```

### Logs de Erro

Erros são logados automaticamente:

```
ERROR - Failed to load plugin meu_plugin
ERROR - Traceback (most recent call last):
...
```

## Distribuição

### Plugin Interno

1. Faça commit no repositório
2. Crie pull request
3. Após merge, estará disponível para todos

### Plugin Externo

1. Crie pacote Python
2. Publique no PyPI
3. Usuários instalam via `pip install`

## Recursos Adicionais

- [Guia de Início Rápido](01-inicio-rapido.md)
- [Criando Atores](03-criando-atores.md)
- [Criando Sensores](04-criando-sensores.md)
- [Boas Práticas](12-boas-praticas.md)

