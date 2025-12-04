import logging
import requests
from cbpi.configFolder import ConfigFolder
from cbpi.utils.utils import load_config
from zipfile import ZipFile
from cbpi.craftbeerpi import CraftBeerPi
import os
import pkgutil
import shutil
import click
from subprocess import call
from colorama import Fore, Back, Style
import importlib
from importlib_metadata import metadata
from tabulate import tabulate
# PyInquirer removed - using standard input() instead for Python 3.13 compatibility
import platform

"""
================================================================================
CLASSE: CraftBeerPiCli
================================================================================
Interface de linha de comando (CLI) para o CraftBeerPi 5.

Esta classe fornece comandos para:
- Setup inicial do sistema
- Iniciar o servidor
- Gerenciar plugins
- Configurar 1-Wire (Raspberry Pi)
- Gerenciar autostart e modo Kiosk
"""
class CraftBeerPiCli():
    def __init__(self, config) -> None:
        """
        Inicializa a CLI do CraftBeerPi.
        
        Args:
            config: Objeto ConfigFolder para gerenciar configurações
        """
        self.config = config
        pass

    def setup(self):
        """
        Executa o setup inicial do CraftBeerPi.
        
        Cria a estrutura de pastas necessária e o arquivo de configuração
        padrão (config.yaml) se não existirem.
        """
        print("Setting up CraftBeerPi")
        self.config.create_home_folder_structure()  # Cria estrutura de pastas
        self.config.create_config_file()  # Cria config.yaml padrão

    def start(self):
        """
        Inicia o servidor CraftBeerPi.
        
        Verifica se o setup foi executado e, se sim, cria uma instância
        do CraftBeerPi e inicia o servidor web.
        """
        if self.config.check_for_setup() is False:
            return
        print("START")
        cbpi = CraftBeerPi(self.config)  # Cria instância principal
        cbpi.start()  # Inicia servidor web

    def setup_one_wire(self):
        """
        Configura o protocolo 1-Wire no Raspberry Pi.
        
        Adiciona a configuração necessária ao arquivo /boot/config.txt
        para habilitar o suporte a sensores 1-Wire (ex: DS18B20).
        Esta função só funciona no Raspberry Pi.
        """
        print("Setting up 1Wire")
        with open('/boot/config.txt', 'w') as f:
            f.write("dtoverlay=w1-gpio,gpiopin=4,pullup=on")
        print("/boot/config.txt created")

    def list_one_wire(self):
        """
        Lista dispositivos 1-Wire conectados.
        
        Carrega os módulos do kernel necessários e lista todos os
        dispositivos 1-Wire encontrados no sistema (sensores de temperatura).
        """
        print("List 1Wire")
        call(["modprobe", "w1-gpio"])  # Carrega módulo GPIO para 1-Wire
        call(["modprobe", "w1-therm"])  # Carrega módulo para sensores de temperatura
        try:
            # Lista dispositivos 1-Wire (IDs começam com 28 ou 10)
            for dirname in os.listdir('/sys/bus/w1/devices'):
                if (dirname.startswith("28") or dirname.startswith("10")):
                    print(dirname)
        except Exception as e:
            print(e)

    def plugins_list(self):
        """
        Lista todos os plugins ativos instalados no sistema.
        
        Procura por módulos Python que começam com 'cbpi' e têm mais de 4 caracteres,
        extrai seus metadados (nome, versão, autor, etc.) e exibe em formato de tabela.
        """
        result = []
        print("")
        print(Fore.LIGHTYELLOW_EX,"List of active plugins", Style.RESET_ALL)
        print("")
        # Descobre plugins instalados (módulos que começam com 'cbpi')
        discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules()
            if name.startswith('cbpi') and len(name) > 4
        }
        # Extrai metadados de cada plugin
        for key, module in discovered_plugins.items():
            try:
                meta = metadata(key)
                result.append(dict(Name=meta["Name"], Version=meta["Version"], Author=meta["Author"], Homepage=meta["Home-page"], Summary=meta["Summary"]))
                            
            except Exception as e:
                print(e)
        # Exibe em formato de tabela
        print(Fore.LIGHTGREEN_EX, tabulate(result, headers="keys"), Style.RESET_ALL)


    def plugin_create(self):
        """
        Cria um novo plugin a partir de um template.
        
        Este método:
        1. Solicita o nome do plugin
        2. Baixa o template oficial do GitHub
        3. Extrai e renomeia os arquivos
        4. Usa Jinja2 para processar templates (setup.py, MANIFEST.in, config.yaml)
        5. Personaliza os arquivos com o nome do plugin
        
        O plugin criado seguirá o padrão: cbpi5_nomedoplugin
        """
        print("Plugin Creation")
        print("")

        # Solicita nome do plugin
        plugin_name = input("Plugin Name: ").strip()
        if not plugin_name:
            print("Plugin name cannot be empty")
            return

        name = "cbpi5_" + plugin_name
        if os.path.exists(os.path.join(".", name)) is True:
            print("Cant create Plugin. Folder {} already exists ".format(name))
            return

        # Baixa template do GitHub
        url = 'https://github.com/Manuel83/craftbeerpi5-plugin-template/archive/main.zip'
        r = requests.get(url)
        with open('temp.zip', 'wb') as f:
            f.write(r.content)

        # Extrai template
        with ZipFile('temp.zip', 'r') as repo_zip:
            repo_zip.extractall()

        # Renomeia pastas
        os.rename("./craftbeerpi5-plugin-template-main", os.path.join(".", name))
        os.rename(os.path.join(".", name, "src"), os.path.join(".", name, name))

        # Processa templates com Jinja2
        import jinja2

        templateLoader = jinja2.FileSystemLoader(searchpath=os.path.join(".", name))
        templateEnv = jinja2.Environment(loader=templateLoader)
        
        # Processa setup.py
        TEMPLATE_FILE = "setup.py"
        template = templateEnv.get_template(TEMPLATE_FILE)
        outputText = template.render(name=name)
        with open(os.path.join(".", name, "setup.py"), "w") as fh:
            fh.write(outputText)

        # Processa MANIFEST.in
        TEMPLATE_FILE = "MANIFEST.in"
        template = templateEnv.get_template(TEMPLATE_FILE)
        outputText = template.render(name=name)
        with open(os.path.join(".", name, "MANIFEST.in"), "w") as fh:
            fh.write(outputText)

        # Processa config.yaml
        TEMPLATE_FILE = os.path.join("/", name, "config.yaml")
        operatingsystem = str(platform.system()).lower()
        if operatingsystem.startswith("win"):
            TEMPLATE_FILE=str(TEMPLATE_FILE).replace('\\','/')

        template = templateEnv.get_template(TEMPLATE_FILE)
        outputText = template.render(name=name)
        with open(os.path.join(".", name, name, "config.yaml"), "w") as fh:
            fh.write(outputText)

        print("")
        print("")
        print("Plugin {}{}{} created! ".format(Fore.LIGHTGREEN_EX, name, Style.RESET_ALL) )
        print("")
        print("Developer Documentation: https://openbrewing.gitbook.io/craftbeerpi5_support/readme/development")
        print("")
        print("Happy developing! Cheers")
        print("")
        print("")

    def autostart(self, name):
        """
        Gerencia o autostart do CraftBeerPi no sistema (systemd).
        
        Args:
            name: 'on' para habilitar, 'off' para desabilitar, 'status' para verificar status
        """
        if(name == "status"):
            if os.path.exists(os.path.join("/etc/systemd/system","craftbeerpi.service")) is True:
                print("CraftBeerPi Autostart is {}ON{}".format(Fore.LIGHTGREEN_EX,Style.RESET_ALL))
            else:
                print("CraftBeerPi Autostart is {}OFF{}".format(Fore.RED,Style.RESET_ALL))
        elif(name == "on"):
            print("Add craftbeerpi.service to systemd")
            try:
                if os.path.exists(os.path.join("/etc/systemd/system","craftbeerpi.service")) is False:
                    srcfile = self.config.get_file_path("craftbeerpi.service")
                    destfile = os.path.join("/etc/systemd/system")
                    shutil.copy(srcfile, destfile)
                    print("Copied craftbeerpi.service to /etc/systemd/system")
                    os.system('systemctl enable craftbeerpi.service')
                    print('Enabled craftbeerpi service')
                    os.system('systemctl start craftbeerpi.service')
                    print('Started craftbeerpi.service')
                else:
                    print("craftbeerpi.service is already located in /etc/systemd/system")
            except Exception as e:
                print(e)
                return
            return
        elif(name == "off"): 
            print("Remove craftbeerpi.service from systemd")
            try:
                status = os.popen('systemctl list-units --type=service --state=running | grep craftbeerpi.service').read()
                if status.find("craftbeerpi.service") != -1:
                    os.system('systemctl stop craftbeerpi.service')
                    print('Stopped craftbeerpi service')
                    os.system('systemctl disable craftbeerpi.service')
                    print('Removed craftbeerpi.service as service')
                else:
                    print('craftbeerpi.service service is not running')

                if os.path.exists(os.path.join("/etc/systemd/system","craftbeerpi.service")) is True:
                    os.remove(os.path.join("/etc/systemd/system","craftbeerpi.service")) 
                    print("Deleted craftbeerpi.service from /etc/systemd/system")
                else:
                    print("craftbeerpi.service is not located in /etc/systemd/system")
            except Exception as e:
                print(e)
                return
            return


    def chromium(self, name):
        """
        Gerencia o modo Kiosk do Chromium (inicia automaticamente a interface web).
        
        Args:
            name: 'on' para habilitar, 'off' para desabilitar, 'status' para verificar status
        """
        if(name == "status"):
            if os.path.exists(os.path.join("/etc/xdg/autostart/","chromium.desktop")) is True:
                print("CraftBeerPi Chromium Desktop is {}ON{}".format(Fore.LIGHTGREEN_EX,Style.RESET_ALL))
            else:
                print("CraftBeerPi Chromium Desktop is {}OFF{}".format(Fore.RED,Style.RESET_ALL))
        elif(name == "on"):
            print("Add chromium.desktop to /etc/xdg/autostart/")
            try:
                if os.path.exists(os.path.join("/etc/xdg/autostart/","chromium.desktop")) is False:
                    srcfile = self.config.get_file_path("chromium.desktop")
                    destfile = os.path.join("/etc/xdg/autostart/")
                    shutil.copy(srcfile, destfile)
                    print("Copied chromium.desktop to /etc/xdg/autostart/")
                else:
                    print("chromium.desktop is already located in /etc/xdg/autostart/")
            except Exception as e:
                print(e)
                return
            return
        elif(name == "off"): 
            print("Remove chromium.desktop from /etc/xdg/autostart/")
            try:
                if os.path.exists(os.path.join("/etc/xdg/autostart/","chromium.desktop")) is True:
                    os.remove(os.path.join("/etc/xdg/autostart/","chromium.desktop"))
                    print("Deleted chromium.desktop from /etc/xdg/autostart/")
                else:
                    print("chromium.desktop is not located in /etc/xdg/autostart/")
            except Exception as e:
                print(e)
                return
            return


@click.group()
@click.pass_context
@click.option('--config-folder-path', '-c', default="./config", type=click.Path(), 
              help="Specify where the config folder is located. Defaults to './config'.")
def main(context, config_folder_path):
    """
    Interface de linha de comando principal do CraftBeerPi 5.
    Gerencia todos os comandos disponíveis para setup, inicialização e configuração.
    """
    print("---------------------")
    print("Welcome to CBPi")
    print("---------------------")
    # Configura logging
    level = logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    # Cria instância do CLI com a pasta de configuração
    cbpi_cli = CraftBeerPiCli(ConfigFolder(config_folder_path))
    context.obj = cbpi_cli

@main.command()
@click.pass_context
def setup(context):
    """Cria a estrutura de pastas e arquivos de configuração padrão."""
    context.obj.setup()

@main.command()
@click.pass_context
@click.option('--list', is_flag=True, help="List all 1Wire Devices")
@click.option('--setup', is_flag=True, help="Setup 1Wire on Raspberry Pi")
def onewire(context, list, setup):
    """Configura ou lista dispositivos 1-Wire no Raspberry Pi."""
    if setup is True:
        context.obj.setup_one_wire()
    if list is True:
        context.obj.list_one_wire()

@main.command()
@click.pass_context
def start(context):
    """Inicia o servidor CraftBeerPi."""
    context.obj.start()

@main.command()
@click.pass_context
def plugins(context):
    """Lista todos os plugins ativos instalados no sistema."""
    context.obj.plugins_list()

@main.command()
@click.pass_context
def create(context):
    """Cria um novo plugin a partir do template oficial."""
    context.obj.plugin_create()

@main.command()
@click.pass_context
@click.argument('name')
def autostart(context, name):
    """Gerencia o autostart do CraftBeerPi (on|off|status)."""
    context.obj.autostart(name)

@main.command()
@click.pass_context
@click.argument('name')
def chromium(context, name):
    """Gerencia o modo Kiosk do Chromium (on|off|status)."""
    context.obj.chromium(name)
