from cbpi.utils.encoder import ComplexEncoder

__all__ = ['load_config',"json_dumps"]

import json
import yaml

"""
================================================================================
UTILITÁRIOS: Funções Auxiliares
================================================================================
Funções utilitárias usadas em todo o sistema.
"""

def load_config(fname):
    """
    Carrega um arquivo de configuração YAML.
    
    Args:
        fname: Caminho do arquivo YAML
    
    Returns:
        Dicionário com dados do arquivo ou None se houver erro
    
    Usado para carregar:
    - config.yaml (configuração principal)
    - config.yaml de plugins
    - Receitas (YAML)
    """
    try:
        with open(fname, 'rt') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        return data
    except Exception as e:
        # Retorna None silenciosamente se houver erro
        pass

def json_dumps(obj):
    """
    Serializa um objeto Python para JSON usando encoder customizado.
    
    O ComplexEncoder permite serializar objetos complexos como:
    - Dataclasses
    - Objetos com método to_dict()
    - Enums
    
    Args:
        obj: Objeto a ser serializado
    
    Returns:
        String JSON
    """
    return json.dumps(obj, cls=ComplexEncoder)
