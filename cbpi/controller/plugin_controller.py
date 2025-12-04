
import importlib
import logging
import os
import pkgutil

from importlib import import_module

from cbpi.api import *
from cbpi.utils.utils import load_config
from importlib_metadata import metadata, version

logger = logging.getLogger(__name__)

"""
================================================================================
CONTROLLER: PluginController
================================================================================
Gerencia plugins e extensões do sistema.

Plugins podem:
- Adicionar novos tipos de atuadores, sensores, etapas, etc.
- Estender funcionalidades do sistema
- Adicionar endpoints HTTP customizados
- Registrar handlers de eventos

Tipos de plugins:
1. Plugins internos: em cbpi/extension/ (incluídos no código)
2. Plugins externos: instalados via pip (nome começa com 'cbpi')

Processo de carregamento:
1. Carrega plugins internos de cbpi/extension/
2. Descobre plugins externos instalados
3. Chama setup() de cada plugin para registro
"""
class PluginController():
    modules = {}  # Módulos de plugins carregados
    types = {}  # Tipos registrados pelos plugins

    def __init__(self, cbpi):
        """
        Inicializa o controller de plugins.
        
        Args:
            cbpi: Instância principal do CraftBeerPi
        """
        self.cbpi = cbpi

    def load_plugins(self):
        """
        Carrega plugins internos da pasta cbpi/extension/.
        
        Processo:
        1. Lista diretórios em cbpi/extension/
        2. Para cada diretório, verifica config.yaml
        3. Se active=True e version=4, carrega o plugin
        4. Chama setup() do plugin para registro
        
        Nota: Versão 4 é para compatibilidade com CraftBeerPi 4.
              Para CraftBeerPi 5, deveria ser version=5, mas mantido
              como 4 para compatibilidade com plugins existentes.
        """
        this_directory = os.sep.join(
            os.path.abspath(__file__).split(os.sep)[:-1])
        # Itera sobre diretórios em cbpi/extension/
        for filename in os.listdir(os.path.join(this_directory, "../extension")):
            # Ignora se não for diretório ou for __pycache__
            if os.path.isdir(
                    os.path.join(this_directory, "../extension/") + filename) is False or filename == "__pycache__":
                continue
            try:
                logger.info("Trying to load plugin %s" % filename)
                # Carrega config.yaml do plugin
                data = load_config(os.path.join(
                    this_directory, "../extension/%s/config.yaml" % filename))
                # Verifica se plugin está ativo e compatível
                if (data.get("active") is True and data.get("version") == 4):
                    # Importa e carrega o plugin
                    self.modules[filename] = import_module(
                        "cbpi.extension.%s" % (filename))
                    # Chama setup() do plugin para registro
                    self.modules[filename].setup(self.cbpi)
                else:
                    logger.warning(
                        "Plugin %s is not supporting version 4" % filename)

            except Exception as e:
                logger.error(e)

    def load_plugins_from_evn(self):
        """
        Carrega plugins externos instalados no ambiente Python.
        
        Descobre módulos Python que:
        - Começam com 'cbpi' (ex: cbpi5_meuplugin)
        - Têm mais de 4 caracteres (exclui 'cbpi' base)
        
        Processo:
        1. Itera sobre todos os módulos Python instalados
        2. Filtra módulos que começam com 'cbpi'
        3. Tenta importar e chamar setup() de cada um
        """
        # Descobre plugins instalados
        discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in pkgutil.iter_modules()
            if name.startswith('cbpi') and len(name) > 4
        }

        # Carrega cada plugin descoberto
        for key, value in discovered_plugins.items():
            from importlib.metadata import version
            try:
                logger.info("Try to load plugin:  {} == {} ".format(
                    key, version(key)))
                # Chama setup() do plugin para registro
                value.setup(self.cbpi)
                logger.info("Plugin {} loaded successfully".format(key))
            except Exception as e:
                logger.error("FAILED to load plugin {} ".format(key))
                logger.error(e)

    def register(self, name, clazz) -> None:
        """
        Registra um novo tipo de componente (ator, sensor, etapa, etc.).
        
        Este método é chamado pelos plugins durante setup() para registrar
        novos tipos de componentes que podem ser usados no sistema.
        
        Args:
            name: Nome do tipo (ex: "GPIOActor", "DS18B20Sensor")
            clazz: Classe do componente
        
        O tipo é registrado no controller apropriado baseado na classe base:
        - CBPiActor -> ActorController
        - CBPiSensor -> SensorController
        - CBPiStep -> StepController
        - CBPiKettleLogic -> KettleController
        - etc.
        """
        logger.debug("Register %s Class %s" % (name, clazz.__name__))

        # Registra no controller apropriado baseado na classe base
        if issubclass(clazz, CBPiActor):
            self.cbpi.actor.types[name] = self._parse_step_props(clazz, name)

        if issubclass(clazz, CBPiKettleLogic):
            self.cbpi.kettle.types[name] = self._parse_step_props(clazz, name)

        if issubclass(clazz, CBPiFermenterLogic):
            self.cbpi.fermenter.types[name] = self._parse_step_props(
                clazz, name)

        if issubclass(clazz, CBPiSensor):
            self.cbpi.sensor.types[name] = self._parse_step_props(clazz, name)

        if issubclass(clazz, CBPiStep):
            self.cbpi.step.types[name] = self._parse_step_props(clazz, name)

        if issubclass(clazz, CBPiFermentationStep):
            self.cbpi.fermenter.steptypes[name] = self._parse_step_props(
                clazz, name)

        if issubclass(clazz, CBPiExtension):
            self.c = clazz(self.cbpi)

    def _parse_property_object(self, p):
        if isinstance(p, Property.Number):
            return {"label": p.label, "type": "number", "configurable": p.configurable, "description": p.description,
                    "default_value": p.default_value}
        elif isinstance(p, Property.Text):
            return {"label": p.label, "type": "text", "configurable": p.configurable, "default_value": p.default_value,
                    "description": p.description}
        elif isinstance(p, Property.Select):
            return {"label": p.label, "type": "select", "configurable": True, "options": p.options,
                    "description": p.description}
        elif isinstance(p, Property.Actor):
            return {"label": p.label, "type": "actor", "configurable": p.configurable, "description": p.description}
        elif isinstance(p, Property.Sensor):
            return {"label": p.label, "type": "sensor", "configurable": p.configurable, "description": p.description}
        elif isinstance(p, Property.Kettle):
            return {"label": p.label, "type": "kettle", "configurable": p.configurable, "description": p.description}
        elif isinstance(p, Property.Fermenter):
            return {"label": p.label, "type": "fermenter", "configurable": p.configurable, "description": p.description}

    def _parse_step_props(self, cls, name):

        result = {"name": name, "class": cls, "properties": [], "actions": []}

        if hasattr(cls, "cbpi_parameters"):
            parameters = []
            for p in cls.cbpi_parameters:
                parameters.append(self._parse_property_object(p))
            result["properties"] = parameters
        for method_name, method in cls.__dict__.items():
            if hasattr(method, "action"):
                key = method.__getattribute__("key")
                parameters = []
                for p in method.__getattribute__("parameters"):
                    parameters.append(self._parse_property_object(p))
                result["actions"].append(
                    {"method": method_name, "label": key, "parameters": parameters})

        return result

    def _parse_props(self, cls):

        name = cls.__name__

        result = {"name": name, "class": cls, "properties": [], "actions": []}

        tmpObj = cls(cbpi=None, managed_fields=None)
        members = [attr for attr in dir(tmpObj) if not callable(
            getattr(tmpObj, attr)) and not attr.startswith("__")]
        for m in members:
            if isinstance(tmpObj.__getattribute__(m), Property.Number):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "number", "configurable": t.configurable,
                     "description": t.description, "default_value": t.default_value})
            elif isinstance(tmpObj.__getattribute__(m), Property.Text):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "text", "configurable": t.configurable,
                     "default_value": t.default_value, "description": t.description})
            elif isinstance(tmpObj.__getattribute__(m), Property.Select):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "select", "configurable": True, "options": t.options,
                     "description": t.description})
            elif isinstance(tmpObj.__getattribute__(m), Property.Actor):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "actor", "configurable": t.configurable,
                     "description": t.description})
            elif isinstance(tmpObj.__getattribute__(m), Property.Sensor):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "sensor", "configurable": t.configurable,
                     "description": t.description})
            elif isinstance(tmpObj.__getattribute__(m), Property.Kettle):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "kettle", "configurable": t.configurable,
                     "description": t.description})
            elif isinstance(tmpObj.__getattribute__(m), Property.Fermenter):
                t = tmpObj.__getattribute__(m)
                result["properties"].append(
                    {"name": m, "label": t.label, "type": "fermenter", "configurable": t.configurable,
                     "description": t.description})

        for method_name, method in cls.__dict__.items():
            if hasattr(method, "action"):
                key = method.__getattribute__("key")
                parameters = method.__getattribute__("parameters")
                result["actions"].append(
                    {"method": method_name, "label": key, "parameters": parameters})

        return result

    async def load_plugin_list(self):
        result = []
        try:
            discovered_plugins = {
                name: importlib.import_module(name)
                for finder, name, ispkg
                in pkgutil.iter_modules()
                if name.startswith('cbpi') and len(name) > 4
            }
            for key, module in discovered_plugins.items():
                from importlib.metadata import version
                try:
                    from importlib.metadata import (distribution, metadata,
                                                    version)
                    meta = metadata(key)
                    result.append({row: meta[row]
                                  for row in list(metadata(key))})
                except Exception as e:
                    logger.error("FAILED to load plugin {} ".format(key))
                    logger.error(e)

        except Exception as e:
            logger.error(e)
            return []
        return result
