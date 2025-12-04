# CraftBeerPi 5

[![Build](https://github.com/ChristopherNicolasSMM/craftbeerpi5/actions/workflows/build.yml/badge.svg)](https://github.com/ChristopherNicolasSMM/craftbeerpi5/actions/workflows/build.yml)
[![GitHub license](https://img.shields.io/github/license/ChristopherNicolasSMM/craftbeerpi5)](https://github.com/ChristopherNicolasSMM/craftbeerpi5/blob/master/LICENSE)
![GitHub issues](https://img.shields.io/github/issues-raw/ChristopherNicolasSMM/craftbeerpi5)
![PyPI](https://img.shields.io/pypi/v/cbpi)
![Happy Brewing](https://img.shields.io/badge/CraftBeerPi%205-Happy%20Brewing-%23FBB117)

<p align="center">
  <img src="https://github.com/craftbeerpi/craftbeerpi5-ui/blob/main/cbpi5ui/public/logo192.png?raw=true" alt="CraftBeerPi Logo"/>
</p>

CraftBeerPi 5 is an open source software solution to control the brewing and
fermentation of beer :beer:.

---

## 🚀 Acesso Rápido

### 🌐 Link de Acesso

Após iniciar o servidor, acesse a interface web:

**URL Principal:** [http://localhost:8000](http://localhost:8000)

**Interface Web:** [http://localhost:8000/cbpi_ui/static/index.html](http://localhost:8000/cbpi_ui/static/index.html)

### 🔐 Credenciais Padrão

- **Usuário:** `cbpi`
- **Senha:** `123`

> ⚠️ **Importante:** Altere a senha padrão após o primeiro acesso em Configurações > Sistema.

---

## 📖 Manual de Uso

### 📋 Índice

1. [Instalação](#-instalação)
2. [Configuração Inicial](#-configuração-inicial)
3. [Iniciando o Servidor](#-iniciando-o-servidor)
4. [Navegação na Interface](#-navegação-na-interface)
5. [Comandos CLI](#-comandos-cli)
6. [Troubleshooting](#-troubleshooting)

---

## 💻 Instalação

### Pré-requisitos

- Python 3.11 ou superior (testado com Python 3.13)
- pip (gerenciador de pacotes Python)
- Ambiente virtual (recomendado)

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/ChristopherNicolasSMM/craftbeerpi5.git
   cd craftbeerpi5
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # Windows
   python -m venv venvCraftbeerPi
   .\venvCraftbeerPi\Scripts\Activate.ps1
   
   # Linux/Mac
   python3 -m venv venvCraftbeerPi
   source venvCraftbeerPi/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuração Inicial

### Primeira Configuração

Execute o comando de setup para criar a estrutura de configuração:

```bash
python run.py setup
```

Isso criará:
- Pasta `config/` com arquivos de configuração
- Arquivo `config/config.yaml` com configurações padrão
- Estrutura de pastas necessária (dashboard, recipes, upload, etc.)

### Configuração do Servidor

Edite o arquivo `config/config.yaml` para personalizar:

```yaml
name: CraftBeerPi
version: 5.0.0
port: 8000                    # Porta do servidor web
username: cbpi                # Usuário de acesso
password: 123                 # Senha de acesso
mqtt: false                   # Habilitar MQTT
mqtt_host: localhost          # Host MQTT
mqtt_port: 1883               # Porta MQTT
```

---

## 🎯 Iniciando o Servidor

### Modo Desenvolvimento

```bash
# Com ambiente virtual ativado
python run.py start
```

O servidor iniciará na porta configurada (padrão: 8000).

### Verificar se está Rodando

Após iniciar, você verá:
```
---------------------
Welcome to CBPi
---------------------
START
INFO: Init CraftBeerPI
INFO: Topic #
```

### Acessar a Interface

Abra seu navegador e acesse:
- **Interface Principal:** [http://localhost:8000](http://localhost:8000)
- **Interface Completa:** [http://localhost:8000/cbpi_ui/static/index.html](http://localhost:8000/cbpi_ui/static/index.html)

---

## 🧭 Navegação na Interface

### Menu Principal

A interface web do CraftBeerPi 5 oferece as seguintes seções:

#### 🏠 Dashboard
- **Acesso:** Menu lateral > Dashboard
- **Função:** Visualização geral do sistema, gráficos e status dos equipamentos
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/dashboard`

#### 🍺 Kettle (Panela)
- **Acesso:** Menu lateral > Kettle
- **Função:** Controle da panela de brassagem
- **Recursos:** Configuração de temperatura, controle de aquecimento, receitas
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/kettle`

#### 🌡️ Fermenter (Fermentador)
- **Acesso:** Menu lateral > Fermenter
- **Função:** Controle de fermentação
- **Recursos:** Controle de temperatura, etapas de fermentação, histórico
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/fermenter`

#### ⚙️ Actors (Atuadores)
- **Acesso:** Menu lateral > Actors
- **Função:** Gerenciamento de atuadores (bombas, aquecedores, válvulas)
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/actor`

#### 📊 Sensors (Sensores)
- **Acesso:** Menu lateral > Sensors
- **Função:** Gerenciamento de sensores de temperatura e outros
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/sensor`

#### 📝 Steps (Etapas)
- **Acesso:** Menu lateral > Steps
- **Função:** Configuração de etapas do processo de brassagem
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/step`

#### 📋 Recipes (Receitas)
- **Acesso:** Menu lateral > Recipes
- **Função:** Gerenciamento de receitas de cerveja
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/recipe`

#### 🔌 Plugins
- **Acesso:** Menu lateral > Plugins
- **Função:** Instalação e gerenciamento de plugins
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/plugin`

#### ⚙️ Config (Configurações)
- **Acesso:** Menu lateral > Config
- **Função:** Configurações do sistema
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/config`

#### 📡 System (Sistema)
- **Acesso:** Menu lateral > System
- **Função:** Informações do sistema, backup, logs
- **URL:** `http://localhost:8000/cbpi_ui/static/index.html#/system`

### API REST

O CraftBeerPi 5 também oferece uma API REST para integração:

- **Documentação Swagger:** [http://localhost:8000/api/doc](http://localhost:8000/api/doc)
- **Endpoint Base:** `http://localhost:8000/api/`

#### Principais Endpoints:

- `GET /api/system/` - Estado do sistema
- `GET /api/actor/` - Lista de atuadores
- `GET /api/sensor/` - Lista de sensores
- `GET /api/kettle/` - Lista de panelas
- `GET /api/fermenter/` - Lista de fermentadores
- `GET /api/recipe/` - Lista de receitas

---

## 🖥️ Comandos CLI

### Comandos Disponíveis

```bash
# Setup inicial (criar estrutura de configuração)
python run.py setup

# Iniciar servidor
python run.py start

# Listar plugins instalados
python run.py plugins

# Criar novo plugin
python run.py create

# Configurar 1-Wire (Raspberry Pi)
python run.py onewire --setup

# Listar dispositivos 1-Wire
python run.py onewire --list

# Gerenciar autostart (Linux)
python run.py autostart on      # Habilitar
python run.py autostart off     # Desabilitar
python run.py autostart status  # Ver status

# Gerenciar modo Kiosk (Raspberry Pi)
python run.py chromium on       # Habilitar
python run.py chromium off      # Desabilitar
python run.py chromium status  # Ver status
```

### Opções de Configuração

```bash
# Especificar pasta de configuração personalizada
python run.py --config-folder-path /caminho/personalizado start
```

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro: "Config File not found"
**Solução:**
```bash
python run.py setup
```

#### 2. Erro: "ModuleNotFoundError: No module named 'pkg_resources'"
**Solução:**
```bash
pip install setuptools
```

#### 3. Porta 8000 já em uso
**Solução:** Altere a porta no arquivo `config/config.yaml`:
```yaml
port: 8001  # Use outra porta
```

#### 4. Erro ao iniciar no Windows
**Solução:** Certifique-se de que o ambiente virtual está ativado:
```powershell
.\venvCraftbeerPi\Scripts\Activate.ps1
python run.py start
```

#### 5. Aviso sobre asyncio-mqtt
**Informação:** Este é apenas um aviso informativo. O `asyncio-mqtt` foi renomeado para `aiomqtt`, mas ainda funciona. Pode ser ignorado ou atualizado futuramente.

### Verificar Status do Servidor

**Windows:**
```powershell
Get-NetTCPConnection -LocalPort 8000
```

**Linux/Mac:**
```bash
netstat -an | grep 8000
# ou
lsof -i :8000
```

### Logs

Os logs do sistema podem ser acessados via:
- Interface Web: System > Logs
- API: `GET /api/system/logs/`

---

## 📚 Documentação Adicional

Instructions on how to install CraftBeerPi and use its plugins is described
in the documentation, that can be found here: [gitbook.io](https://openbrewing.gitbook.io/craftbeerpi5_support/).

### Plugins
Plugins extend the base functionality of CraftBeerPi 5.
You can find a list of available plugins [here](https://openbrewing.gitbook.io/craftbeerpi5_support/master/plugin-installation#plugin-list).

---

## 🔗 Links Úteis

### Acesso Local
- **Interface Web:** [http://localhost:8000](http://localhost:8000)
- **Interface Completa:** [http://localhost:8000/cbpi_ui/static/index.html](http://localhost:8000/cbpi_ui/static/index.html)
- **API Swagger:** [http://localhost:8000/api/doc](http://localhost:8000/api/doc)

### Recursos Externos
- **Documentação Completa:** [GitBook - CraftBeerPi 5 Support](https://openbrewing.gitbook.io/craftbeerpi5_support/)
- **Lista de Plugins:** [Plugin Installation Guide](https://openbrewing.gitbook.io/craftbeerpi5_support/master/plugin-installation#plugin-list)
- **Repositório GitHub:** [craftbeerpi5](https://github.com/ChristopherNicolasSMM/craftbeerpi5)
- **Repositório Original:** [craftbeerpi5](https://github.com/craftbeerpi/craftbeerpi5)

---

## 📝 Notas de Versão

### CraftBeerPi 5.0.0

**Principais Mudanças:**
- ✅ Atualizado de CraftBeerPi 4 para CraftBeerPi 5
- ✅ Compatibilidade com Python 3.11+
- ✅ Bibliotecas atualizadas para versões mais recentes
- ✅ Correções de compatibilidade com Python 3.13
- ✅ Remoção de dependências obsoletas (PyInquirer)
- ✅ Melhorias na estabilidade e performance

**Compatibilidade:**
- Python: 3.11, 3.12, 3.13
- Sistema Operacional: Windows, Linux, macOS
- Raspberry Pi: Suportado (com GPIO)

## 🧑‍🤝‍🧑 Contribute
You want to help develop CraftBeerPi5? To get you quickly stated, this repository comes with a preconfigured
development environment. To be able to use this environment you need 2 things installed on your computer:

- docker
- visual studio code (vscode)

To start developing clone this repository, open the folder in vscode and use the _development container_ feature. The command is called _Reopen in container_. Please note that this quick start setup does not work if you want to develop directly on a 32bit raspberry pi os because docker is only available for 64bit arm plattform. Please use the regular development setup for that.

For a more detailed description of a development setup without the _development container_ feature see the documentation page:
[gitbook.io](https://openbrewing.gitbook.io/craftbeerpi5_support/)

### Contributors
Thanks to all the people who have contributed

[![contributors](https://contributors-img.web.app/image?repo=ChristopherNicolasSMM/craftbeerpi5)](https://github.com/ChristopherNicolasSMM/craftbeerpi5/graphs/contributors)
