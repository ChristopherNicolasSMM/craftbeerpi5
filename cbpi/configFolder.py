import os
from os import listdir
from os.path import isfile, join
import pathlib
import platform
import shutil
import zipfile
import glob

"""
================================================================================
CLASSE: ConfigFolder
================================================================================
Gerencia a pasta de configuração do CraftBeerPi.

Esta classe fornece métodos para:
- Verificar existência de arquivos de configuração
- Criar estrutura de pastas necessária
- Copiar arquivos padrão se não existirem
- Restaurar configurações de backup
- Obter caminhos de arquivos de receitas e uploads

Estrutura de pastas criada:
- config/
  - dashboard/widgets/
  - recipes/
  - upload/
  - fermenterrecipes/
  - logs/sensors/
"""
class ConfigFolder:
    def __init__(self, configFolderPath):
        """
        Inicializa o gerenciador de pasta de configuração.
        
        Args:
            configFolderPath: Caminho da pasta de configuração (geralmente './config')
        """
        self._rawPath = configFolderPath

    def config_file_exists(self, path):
        """
        Verifica se um arquivo de configuração existe.
        
        Args:
            path: Caminho relativo do arquivo
        
        Returns:
            True se arquivo existe, False caso contrário
        """
        return os.path.exists(self.get_file_path(path))
    
    def get_file_path(self, file):
        """
        Obtém caminho completo de um arquivo na pasta de configuração.
        
        Args:
            file: Nome do arquivo ou caminho relativo
        
        Returns:
            Caminho completo do arquivo
        """
        return os.path.join(self._rawPath, file)

    def get_upload_file(self, file):
        """
        Obtém caminho de um arquivo na pasta de upload.
        
        Args:
            file: Nome do arquivo
        
        Returns:
            Caminho completo do arquivo de upload
        """
        return os.path.join(self._rawPath, 'upload', file)

    def get_recipe_file_by_id(self, recipe_id):
        """
        Obtém caminho do arquivo de uma receita de brassagem.
        
        Args:
            recipe_id: ID da receita
        
        Returns:
            Caminho completo do arquivo YAML da receita
        """
        return os.path.join(self._rawPath, 'recipes', "{}.yaml".format(recipe_id))

    def get_fermenter_recipe_by_id(self, recipe_id):
        """
        Obtém caminho do arquivo de uma receita de fermentação.
        
        Args:
            recipe_id: ID da receita de fermentação
        
        Returns:
            Caminho completo do arquivo YAML da receita
        """
        return os.path.join(self._rawPath, 'fermenterrecipes', "{}.yaml".format(recipe_id))

    def get_all_fermenter_recipes(self):
        """
        Lista todos os IDs de receitas de fermentação disponíveis.
        
        Returns:
            Lista de IDs (nomes dos arquivos sem extensão .yaml)
        """
        fermenter_recipes_folder = os.path.join(self._rawPath, 'fermenterrecipes')
        fermenter_recipe_ids = [os.path.splitext(f)[0] for f in listdir(fermenter_recipes_folder) 
                                if isfile(join(fermenter_recipes_folder, f)) and f.endswith(".yaml")]
        return fermenter_recipe_ids

    def check_for_setup(self):
        """
        Verifica se o setup foi executado (arquivos e pastas necessários existem).
        
        Também verifica se há backup para restaurar (restored_config.zip).
        
        Returns:
            True se setup está completo, False caso contrário
        """
        # Verifica arquivo de configuração principal
        if self.config_file_exists("config.yaml") is False:
            print("***************************************************")
            print("CraftBeerPi Config File not found: %s" % self.get_file_path("config.yaml"))
            print("Please run 'cbpi setup' before starting the server ")
            print("***************************************************")
            return False
        # Verifica pasta de upload
        if self.config_file_exists("upload") is False:
            print("***************************************************")
            print("CraftBeerPi upload folder not found: %s" % self.get_file_path("upload"))
            print("Please run 'cbpi setup' before starting the server ")
            print("***************************************************")
            return False
    #    if os.path.exists(os.path.join(".", "config", "fermenterrecipes")) is False:
    #        print("***************************************************")
    #        print("CraftBeerPi fermenterrecipes folder not found: %s" % os.path.join(".", "config/fermenterrecipes"))
    #        print("Please run 'cbpi setup' before starting the server ")
    #        print("***************************************************")
    #        return False
        backupfile = os.path.join(".", "restored_config.zip")
        if os.path.exists(os.path.join(backupfile)) is True:
            print("***************************************************")
            print("Found backup of config. Starting restore")
            required_content=['dashboard/', 'recipes/', 'upload/', 'config.json', 'config.yaml']
            zip=zipfile.ZipFile(backupfile)
            zip_content_list = zip.namelist()
            zip_content = True
            print("Checking content of zip file")
            for content in required_content:
                try:
                    check = zip_content_list.index(content)
                except:
                    zip_content = False

            if zip_content == True:
                print("Found correct content. Starting Restore process")
                output_path = pathlib.Path(self._rawPath)
                system = platform.system()
                print(system)
                if system != "Windows":
                    owner = output_path.owner()
                    group = output_path.group()
                print("Removing old config folder")
                shutil.rmtree(output_path, ignore_errors=True) 
                print("Extracting zip file to config folder")
                zip.extractall(output_path)
                zip.close()
                if system != "Windows":
                    print(f"Changing owner and group of config folder recursively to {owner}:{group}")
                    self.recursive_chown(output_path, owner, group)
                print("Removing backup file")
                os.remove(backupfile)
            else:
                print("Wrong Content in zip file. No restore possible")
                print("Removing zip file")
                os.remove(backupfile)
            print("***************************************************")

    def copyDefaultFileIfNotExists(self, file):
        """
        Copia arquivo padrão se não existir na pasta de configuração.
        
        Args:
            file: Nome do arquivo a ser copiado
        """
        if self.config_file_exists(file) is False:
            srcfile = os.path.join(os.path.dirname(__file__), "config", file)  # Arquivo padrão
            destfile = os.path.join(self._rawPath, file)  # Destino na pasta de config
            shutil.copy(srcfile, destfile)

    def create_config_file(self):
        """
        Cria todos os arquivos de configuração padrão se não existirem.
        
        Copia arquivos padrão de cbpi/config/ para a pasta de configuração.
        """
        # Arquivos de configuração principais
        self.copyDefaultFileIfNotExists("config.yaml")  # Configuração principal
        self.copyDefaultFileIfNotExists("actor.json")  # Lista de atuadores
        self.copyDefaultFileIfNotExists("sensor.json")  # Lista de sensores
        self.copyDefaultFileIfNotExists("kettle.json")  # Lista de panelas
        self.copyDefaultFileIfNotExists("fermenter_data.json")  # Dados de fermentadores
        self.copyDefaultFileIfNotExists("step_data.json")  # Dados de etapas
        self.copyDefaultFileIfNotExists("config.json")  # Configurações dinâmicas
        self.copyDefaultFileIfNotExists("craftbeerpi.service")  # Arquivo systemd (Linux)
        self.copyDefaultFileIfNotExists("chromium.desktop")  # Arquivo autostart (Kiosk mode)

        # Dashboard padrão
        if os.path.exists(os.path.join(self._rawPath, "dashboard", "cbpi_dashboard_1.json")) is False:
            srcfile = os.path.join(os.path.dirname(__file__), "config", "dashboard", "cbpi_dashboard_1.json")
            destfile = os.path.join(self._rawPath, "dashboard")
            shutil.copy(srcfile, destfile)

        print("Config Folder created")

    def create_home_folder_structure(configFolder):
        """
        Cria estrutura de pastas necessária (método estático).
        
        Args:
            configFolder: Instância de ConfigFolder
        """
        # Cria pasta de logs de sensores
        pathlib.Path(os.path.join(".", 'logs/sensors')).mkdir(parents=True, exist_ok=True)
        
        # Cria pastas de configuração
        configFolder.create_folders()
        print("Folder created")

    def create_folders(self):
        """
        Cria todas as pastas necessárias na estrutura de configuração.
        
        Pastas criadas:
        - config/ (raiz)
        - config/dashboard/widgets/ (widgets customizados)
        - config/recipes/ (receitas de brassagem)
        - config/upload/ (arquivos enviados)
        """
        pathlib.Path(self._rawPath).mkdir(parents=True, exist_ok=True)  # Pasta raiz
        pathlib.Path(os.path.join(self._rawPath, 'dashboard', 'widgets')).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(self._rawPath, 'recipes')).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(self._rawPath, 'upload')).mkdir(parents=True, exist_ok=True)

    def recursive_chown(path, owner, group):
        """
        Altera proprietário e grupo de arquivos recursivamente (Linux/Unix).
        
        Args:
            path: Caminho do diretório
            owner: Proprietário
            group: Grupo
        """
        for dirpath, dirnames, filenames in os.walk(path):
            shutil.chown(dirpath, owner, group)
            for filename in filenames:
                shutil.chown(os.path.join(dirpath, filename), owner, group)