# Notas de Atualização - CraftBeerPi 4 para 5

Este documento contém todas as mudanças realizadas durante a migração do CraftBeerPi 4 para o CraftBeerPi 5.

**Data de Início**: 2024  
**Versão Base**: CraftBeerPi 4.0.5.a12  
**Versão Alvo**: CraftBeerPi 5.0.0

---

## 📋 Índice

- [Mudanças de Versão](#mudanças-de-versão)
- [Atualizações de Referências](#atualizações-de-referências)
- [Atualizações de Dependências](#atualizações-de-dependências)
- [Correções de Compatibilidade](#correções-de-compatibilidade)
- [Mudanças de Arquivos](#mudanças-de-arquivos)
- [Melhorias e Adições](#melhorias-e-adições)
- [Documentação](#documentação)

---

## Mudanças de Versão

### Versão Principal

- **Versão Anterior**: 4.0.5.a12
- **Nova Versão**: 5.0.0
- **Arquivos Afetados**:
  - `cbpi/__init__.py` - Atualizado `__version__` para "5.0.0"
  - `cbpi/config/config.yaml` - Atualizado `version` de "4.0.8" para "5.0.0"
  - `tests/cbpi-test-config/config.yaml` - Atualizado `version` de "4.0.8" para "5.0.0"

### Codename

- Mantido como "BrewPi" (sem alteração)

---

## Atualizações de Referências

### Repositório GitHub

- **Antes**: `craftbeerpi/craftbeerpi4`
- **Depois**: `ChristopherNicolasSMM/craftbeerpi5`
- **Arquivos Afetados**:
  - `README.md` - Badges e links atualizados

### Nomes de Arquivos e Diretórios

- **Arquivo de Boot**:
  - `craftbeerpi4boot` → `craftbeerpi5boot`
  - Atualizado `DAEMON_NAME` de `CraftBeerPI4` para `CraftBeerPI5`

### Referências em Código

- **Prefixo de Plugins**:
  - `cbpi4_` → `cbpi5_`
  - **Arquivo**: `cbpi/cli.py`

- **Template de Plugin**:
  - `Manuel83/craftbeerpi4-plugin-template` → `Manuel83/craftbeerpi5-plugin-template`
  - **Arquivo**: `cbpi/cli.py`

- **Documentação de Desenvolvedor**:
  - `craftbeerpi4_support` → `craftbeerpi5_support`
  - **Arquivo**: `cbpi/cli.py`

### Nomes de Arquivos de Backup/Log

- **Backup de Configuração**:
  - `cbpi4_config.zip` → `cbpi5_config.zip`
  - **Arquivo**: `cbpi/http_endpoints/http_system.py`

- **Backup de Logs**:
  - `cbpi4_log.zip` → `cbpi5_log.zip`
  - **Arquivo**: `cbpi/http_endpoints/http_system.py`

- **Backups de Sistema**:
  - `cbpi4_config.zip` → `cbpi5_config.zip`
  - `cbpi4_log.zip` → `cbpi5_log.zip`
  - `cbpi4_plugins.zip` → `cbpi5_plugins.zip`
  - `cbpi4_actors.zip` → `cbpi5_actors.zip`
  - `cbpi4_sensors.zip` → `cbpi5_sensors.zip`
  - `cbpi4_kettles.zip` → `cbpi5_kettles.zip`
  - **Arquivo**: `cbpi/controller/system_controller.py`

### Banco de Dados InfluxDB

- **Nome Padrão do Banco**:
  - `cbpi4` → `cbpi5`
  - **Arquivo**: `cbpi/extension/ConfigUpdate/__init__.py`

### Interface Web

- **Título da Página de Teste**:
  - "CraftBeerPi 4.0" → "CraftBeerPi 5.0"
  - **Arquivo**: `cbpi/static/test.html`

---

## Atualizações de Dependências

### Python

- **Versão Base**:
  - Python 3.9 → Python 3.11
  - **Arquivo**: `Dockerfile`

### Bibliotecas Python Atualizadas

Todas as bibliotecas foram atualizadas para versões compatíveis com Python 3.11+:

#### Core

- `aiohttp`: Atualizado para versão mais recente
- `aiohttp-session`: Atualizado
- `aiosqlite`: Atualizado
- `cryptography`: Atualizado
- `requests`: Atualizado
- `voluptuous`: Atualizado

#### Data Science

- `pandas`: Atualizado
- `numpy`: Atualizado para `>=2.1.0,<3.0.0` (compatível com Python 3.13)

#### CLI e Utilitários

- `click`: Atualizado
- `importlib_metadata`: Atualizado
- `colorama`: Atualizado

#### MQTT

- `asyncio-mqtt`: Atualizado

#### Sistema

- `psutil`: Atualizado
- `zipp`: Atualizado

#### Testes

- `pytest-aiohttp`: Atualizado
- `coverage`: Atualizado

#### Build Tools

- `setuptools`: Adicionado `>=70.0.0` (necessário para Python 3.13)

### Bibliotecas Removidas/Comentadas

- **PyInquirer**: Removido devido à incompatibilidade com Python 3.13
  - **Motivo**: `collections.Mapping` foi movido para `collections.abc.Mapping` no Python 3.13
  - **Substituição**: Uso de `input()` padrão do Python em `cbpi/cli.py`
  - **Arquivos Afetados**:
    - `requirements.txt`
    - `setup.py`
    - `cbpi/cli.py`

---

## Correções de Compatibilidade

### Python 3.13

#### 1. Import de collections.Mapping

- **Problema**: `PyInquirer` e `prompt_toolkit` usavam `collections.Mapping` que foi movido para `collections.abc.Mapping` no Python 3.13
- **Solução**: Removido `PyInquirer` e substituído por `input()` padrão
- **Arquivos**: `requirements.txt`, `setup.py`, `cbpi/cli.py`

#### 2. pkg_resources

- **Problema**: `pkg_resources` não está automaticamente disponível no Python 3.13
- **Solução**: Adicionado `setuptools>=70.0.0` explicitamente
- **Arquivos**: `requirements.txt`, `setup.py`

#### 3. Regex Patterns (SyntaxWarning)

- **Problema**: Python 3.13 trata backslashes em strings literais como inválidos se não reconhecidos
- **Solução**: Convertidas strings para raw strings (adicionado prefixo `r`)
- **Arquivos Afetados**:
  - `cbpi/http_endpoints/http_actor.py`: `r"/{id:\w+}"`
  - `cbpi/http_endpoints/http_dashboard.py`: `r"/{id:\d+}/content"`
  - `cbpi/http_endpoints/http_system.py`: `r"^(\w+.).log(.?\d*)"`

#### 4. asyncio.Queue e asyncio.gather

- **Problema**: Parâmetro `loop` foi removido de `asyncio.Queue()` e `asyncio.gather()` no Python 3.13
- **Solução**: Removidos parâmetros `loop=loop` e `loop=self._loop`
- **Arquivo**: `cbpi/job/_scheduler.py`
- **Mudanças**:
  ```python
  # Antes
  self._failed_tasks = asyncio.Queue(loop=loop)
  await asyncio.gather(*tasks, loop=self._loop)
  
  # Depois
  self._failed_tasks = asyncio.Queue()
  await asyncio.gather(*tasks)
  ```

### NumPy no Windows

- **Problema**: Erro ao compilar numpy no Windows devido a caminhos longos
- **Solução**: Especificada versão `numpy>=2.1.0,<3.0.0` com wheels pré-compilados
- **Instalação**: `pip install --only-binary :all: numpy`

---

## Mudanças de Arquivos

### Arquivos Renomeados

1. `craftbeerpi4boot` → `craftbeerpi5boot`
   - Conteúdo atualizado com novo nome do daemon

### Arquivos Modificados

#### Core

- `cbpi/__init__.py` - Versão atualizada
- `cbpi/cli.py` - Removido PyInquirer, atualizado referências
- `cbpi/config/config.yaml` - Versão atualizada
- `cbpi/craftbeerpi.py` - (sem mudanças estruturais)

#### Controllers

- `cbpi/controller/system_controller.py` - Nomes de arquivos de backup atualizados

#### HTTP Endpoints

- `cbpi/http_endpoints/http_actor.py` - Regex patterns corrigidos
- `cbpi/http_endpoints/http_dashboard.py` - Regex patterns corrigidos
- `cbpi/http_endpoints/http_system.py` - Nomes de arquivos e regex patterns corrigidos

#### Extensions

- `cbpi/extension/ConfigUpdate/__init__.py` - Nome do banco InfluxDB atualizado

#### Job Scheduler

- `cbpi/job/_scheduler.py` - Parâmetros `loop` removidos

#### Static

- `cbpi/static/test.html` - Título atualizado

#### Configuração

- `tests/cbpi-test-config/config.yaml` - Versão atualizada

#### Build

- `Dockerfile` - Python 3.9 → Python 3.11
- `requirements.txt` - Dependências atualizadas, PyInquirer removido
- `setup.py` - Dependências atualizadas, PyInquirer removido

#### Documentação

- `README.md` - Referências atualizadas, manual completo adicionado

---

## Melhorias e Adições

### Documentação em Português

Adicionados comentários explicativos em português em todos os arquivos principais:

#### Arquivos Documentados

- `cbpi/eventbus.py` - Sistema de Event Bus
- `cbpi/websocket.py` - Gerenciamento de WebSocket
- `cbpi/configFolder.py` - Gerenciamento de configuração
- `cbpi/utils/utils.py` - Funções utilitárias
- `cbpi/controller/basic_controller2.py` - Controller base
- `cbpi/controller/sensor_controller.py` - Controller de sensores
- `cbpi/controller/kettle_controller.py` - Controller de panelas
- `cbpi/controller/step_controller.py` - Controller de etapas
- `cbpi/controller/plugin_controller.py` - Controller de plugins
- `cbpi/controller/fermentation_controller.py` - Controller de fermentação
- `cbpi/api/actor.py` - Classe base de atores
- `cbpi/api/sensor.py` - Classe base de sensores
- `cbpi/api/step.py` - Classe base de etapas
- `cbpi/api/kettle_logic.py` - Lógica de panelas
- `cbpi/api/fermenter_logic.py` - Lógica de fermentadores
- `cbpi/api/dataclasses.py` - Estruturas de dados
- `cbpi/api/decorator.py` - Decoradores
- `cbpi/http_endpoints/http_actor.py` - Endpoints HTTP de atores
- `cbpi/job/_scheduler.py` - Gerenciador de tarefas
- `cbpi/job/_job.py` - Representação de tarefa

### Manual do Usuário

Adicionado manual completo no `README.md` incluindo:
- Acesso Rápido
- Manual de Uso (com índice)
- Instalação
- Configuração
- Iniciando o Servidor
- Navegação na Interface
- Comandos CLI
- Troubleshooting
- Links Úteis
- Notas de Versão

### Documentação para Desenvolvedores

Criada pasta `docs/` com documentação completa:

1. **README.md** - Índice principal
2. **01-inicio-rapido.md** - Guia de início rápido
3. **02-criando-plugins.md** - Manual de plugins
4. **03-criando-atores.md** - Manual de atores
5. **04-criando-sensores.md** - Manual de sensores
6. **05-criando-etapas.md** - Manual de etapas
7. **06-criando-logicas.md** - Manual de lógicas
8. **07-criando-endpoints.md** - Manual de endpoints HTTP
9. **08-propriedades-configuracao.md** - Manual de propriedades
10. **09-event-bus.md** - Manual do Event Bus
11. **10-tarefas-background.md** - Manual de tarefas em background
12. **11-extensoes-avancadas.md** - Manual de extensões
13. **12-boas-praticas.md** - Boas práticas
14. **13-api-reference.md** - Referência da API

### Correções de Bugs

- Corrigido import faltante de `yaml` em `cbpi/eventbus.py`
- Corrigidos todos os warnings de regex patterns
- Corrigidas incompatibilidades com Python 3.13

---

## Documentação

### Estrutura de Documentação Criada

```
docs/
├── README.md                          # Índice principal
├── 01-inicio-rapido.md                # Guia de início rápido
├── 02-criando-plugins.md              # Manual de plugins
├── 03-criando-atores.md               # Manual de atores
├── 04-criando-sensores.md             # Manual de sensores
├── 05-criando-etapas.md               # Manual de etapas
├── 06-criando-logicas.md              # Manual de lógicas
├── 07-criando-endpoints.md            # Manual de endpoints
├── 08-propriedades-configuracao.md    # Manual de propriedades
├── 09-event-bus.md                    # Manual do Event Bus
├── 10-tarefas-background.md           # Manual de tarefas
├── 11-extensoes-avancadas.md          # Manual de extensões
├── 12-boas-praticas.md                 # Boas práticas
├── 13-api-reference.md                # Referência da API
└── NOTAS_ATUALIZACAO_V5.md            # Este arquivo
```

### Conteúdo da Documentação

- **Exemplos Práticos**: Cada manual contém exemplos de código completos e funcionais
- **Passo a Passo**: Tutoriais detalhados para cada tipo de componente
- **Referências Cruzadas**: Links entre manuais relacionados
- **Boas Práticas**: Guias de melhores práticas
- **Troubleshooting**: Soluções para problemas comuns

---

## Resumo de Mudanças por Categoria

### 🔢 Versão
- 4.0.5.a12 → 5.0.0

### 🔄 Referências
- craftbeerpi4 → craftbeerpi5
- cbpi4 → cbpi5
- craftbeerpi4boot → craftbeerpi5boot

### 📦 Dependências
- Python 3.9 → Python 3.11
- Bibliotecas atualizadas para versões compatíveis
- PyInquirer removido
- setuptools adicionado

### 🐛 Correções
- Compatibilidade com Python 3.13
- Regex patterns corrigidos
- Parâmetros asyncio atualizados
- Import faltante corrigido

### 📝 Documentação
- Comentários em português adicionados
- Manual do usuário completo
- Documentação para desenvolvedores (14 manuais)

### ✨ Melhorias
- Código mais documentado
- Melhor estrutura de documentação
- Exemplos práticos em todos os manuais

---

## Próximas Atualizações

Este arquivo será atualizado conforme novas mudanças forem realizadas. Use este documento como referência para:

- Rastrear mudanças entre versões
- Entender o que foi alterado e por quê
- Planejar futuras atualizações
- Documentar novas funcionalidades

---

## Histórico de Atualizações

### 2024 - Versão 5.0.0

#### Migração Inicial
- ✅ Atualização de versão de 4.0.5.a12 para 5.0.0
- ✅ Atualização de todas as referências de craftbeerpi4 para craftbeerpi5
- ✅ Atualização de dependências Python
- ✅ Correção de incompatibilidades com Python 3.13
- ✅ Remoção de PyInquirer
- ✅ Adição de setuptools
- ✅ Correção de regex patterns
- ✅ Atualização de parâmetros asyncio
- ✅ Adição de comentários em português
- ✅ Criação de documentação completa para desenvolvedores
- ✅ Criação de manual do usuário

---

**Última Atualização**: 2024  
**Versão do Documento**: 1.0.0

