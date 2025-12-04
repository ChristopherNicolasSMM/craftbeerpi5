from abc import abstractmethod, ABCMeta
import asyncio
from cbpi.api.config import ConfigType
import time

import logging

"""
================================================================================
CLASSE BASE: CBPiBase
================================================================================
Classe base abstrata para todos os componentes do CraftBeerPi.

Esta classe fornece métodos utilitários comuns para:
- Acesso a configurações (estáticas e dinâmicas)
- Interação com outros componentes (kettle, fermenter, sensor, actor)
- Controle de atuadores e leitura de sensores

Todas as classes de componentes (Actor, Sensor, Step, Logic, etc.)
herdam desta classe base para ter acesso a esses métodos utilitários.
"""
class CBPiBase(metaclass=ABCMeta):

    def get_static_config_value(self,name,default):
        """
        Obtém um valor de configuração estática (do config.yaml).
        
        Args:
            name: Nome da configuração
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou default
        """
        return self.cbpi.static_config.get(name, default)

    def get_config_value(self,name,default):
        """
        Obtém um valor de configuração dinâmica (do banco de dados).
        
        Args:
            name: Nome da configuração
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou default
        """
        return self.cbpi.config.get(name, default=default)

    async def set_config_value(self,name,value):
        """
        Define um valor de configuração dinâmica.
        
        Args:
            name: Nome da configuração
            value: Valor a ser definido
        """
        return await self.cbpi.config.set(name,value)

    async def add_config_value(self, name, value, type: ConfigType, description, options=None):
        """
        Adiciona uma nova configuração dinâmica ao sistema.
        
        Args:
            name: Nome da configuração
            value: Valor inicial
            type: Tipo da configuração (STRING, NUMBER, SELECT, etc.)
            description: Descrição da configuração
            options: Opções disponíveis (para SELECT)
        """
        await self.cbpi.config.add(name, value, type, description, options=None)

    # ============================================================================
    # MÉTODOS PARA INTERAÇÃO COM PANELAS (KETTLE)
    # ============================================================================
    
    def get_kettle(self,id):
        """Obtém uma panela pelo ID"""
        return self.cbpi.kettle.find_by_id(id)

    def get_kettle_target_temp(self,id):
        """Obtém a temperatura alvo de uma panela"""
        return self.cbpi.kettle.find_by_id(id).target_temp

    async def set_target_temp(self,id, temp):
        """Define a temperatura alvo de uma panela"""
        await self.cbpi.kettle.set_target_temp(id, temp)

    # ============================================================================
    # MÉTODOS PARA INTERAÇÃO COM FERMENTADORES
    # ============================================================================
    
    def get_fermenter(self,id):
        """Obtém um fermentador pelo ID"""
        return self.cbpi.fermenter._find_by_id(id)

    def get_fermenter_target_temp(self,id):
        """Obtém a temperatura alvo de um fermentador"""
        return self.cbpi.fermenter._find_by_id(id).target_temp

    async def set_fermenter_target_temp(self,id, temp):
        """Define a temperatura alvo de um fermentador"""
        await self.cbpi.fermenter.set_target_temp(id, temp)

    def get_fermenter_target_pressure(self,id):
        """Obtém a pressão alvo de um fermentador"""
        return self.cbpi.fermenter._find_by_id(id).target_pressure

    async def set_fermenter_target_pressure(self,id, temp):
        """Define a pressão alvo de um fermentador"""
        await self.cbpi.fermenter.set_target_pressure(id, temp)

    # ============================================================================
    # MÉTODOS PARA INTERAÇÃO COM SENSORES
    # ============================================================================
    
    def get_sensor(self,id):
        """Obtém um sensor pelo ID"""
        return self.cbpi.sensor.find_by_id(id)
    
    def get_sensor_value(self,id):
        """Obtém o valor atual de um sensor"""
        return self.cbpi.sensor.get_sensor_value(id)

    # ============================================================================
    # MÉTODOS PARA INTERAÇÃO COM ATUADORES
    # ============================================================================
    
    def get_actor(self,id):
        """Obtém um atuador pelo ID"""
        return self.cbpi.actor.find_by_id(id)

    def get_actor_state(self,id):
        """
        Obtém o estado atual de um atuador (ligado/desligado).
        
        Returns:
            bool: True se ligado, False se desligado
        """
        try:
            actor = self.cbpi.actor.find_by_id(id)
            return actor.instance.state
        except:
            logging.error("Failed to read actor state in step - actor {}".format(id))
            return False 

    async def actor_on(self,id,power=100):
        """
        Liga um atuador com potência especificada.
        
        Args:
            id: ID do atuador
            power: Potência (0-100), padrão 100
        """
        try:
            await self.cbpi.actor.on(id,power)
        except Exception as e:
            pass

    async def actor_off(self,id):
        """
        Desliga um atuador.
        
        Args:
            id: ID do atuador
        """
        try:
            await self.cbpi.actor.off(id)
        except Exception as e:
            pass

    async def actor_set_power(self,id,power):
        """
        Define a potência de um atuador (se já estiver ligado).
        
        Args:
            id: ID do atuador
            power: Potência (0-100)
        """
        try:
            await self.cbpi.actor.set_power(id,power)
        except Exception as e:
            pass
