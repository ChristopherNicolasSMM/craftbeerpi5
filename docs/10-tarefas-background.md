# Tarefas em Background

Este guia detalha como criar tarefas que executam em background no CraftBeerPi 5.

## Visão Geral

Tarefas em background são executadas periodicamente, mesmo quando não há requisições HTTP. Úteis para:
- Limpeza de dados
- Sincronização
- Monitoramento
- Manutenção

## Decorador @background_task

Use o decorador `@background_task` para criar tarefas periódicas:

```python
from cbpi.api import *

@background_task(name="Limpeza de Logs", interval=3600)
async def limpar_logs(self):
    """
    Tarefa que executa a cada hora (3600 segundos).
    """
    logger.info("Limpando logs antigos...")
    # Lógica de limpeza
```

## Parâmetros

### name

Nome da tarefa (para logs e identificação).

```python
@background_task(name="Minha Tarefa", interval=60)
```

### interval

Intervalo entre execuções em segundos.

```python
@background_task(name="Tarefa", interval=60)      # A cada minuto
@background_task(name="Tarefa", interval=3600)     # A cada hora
@background_task(name="Tarefa", interval=86400)    # A cada dia
```

## Exemplo: Limpeza de Logs

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LogCleaner:
    """
    Limpa logs antigos automaticamente.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        # Registrar tarefas
        self.cbpi.bus.register_object(self)
    
    @background_task(name="Limpeza de Logs", interval=3600)
    async def limpar_logs(self):
        """
        Remove logs mais antigos que 7 dias.
        """
        try:
            log_dir = os.path.join(".", "logs")
            if not os.path.exists(log_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=7)
            deleted_count = 0
            
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    # Verificar data de modificação
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff_date:
                        os.remove(filepath)
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info("Limpeza de logs: %s arquivos removidos" % deleted_count)
        except Exception as e:
            logger.error("Erro ao limpar logs: %s" % e)

def setup(cbpi):
    LogCleaner(cbpi)
```

## Exemplo: Sincronização

```python
class DataSync:
    """
    Sincroniza dados com servidor externo.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.bus.register_object(self)
    
    @background_task(name="Sincronização de Dados", interval=300)
    async def sincronizar(self):
        """
        Sincroniza dados a cada 5 minutos.
        """
        try:
            # Obter dados
            atores = self.cbpi.actor.data
            sensores = self.cbpi.sensor.data
            
            # Enviar para servidor externo
            # (implementar lógica de sincronização)
            
            logger.info("Dados sincronizados")
        except Exception as e:
            logger.error("Erro na sincronização: %s" % e)

def setup(cbpi):
    DataSync(cbpi)
```

## Exemplo: Monitoramento

```python
class SystemMonitor:
    """
    Monitora saúde do sistema.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.bus.register_object(self)
    
    @background_task(name="Monitoramento do Sistema", interval=60)
    async def monitorar(self):
        """
        Monitora sistema a cada minuto.
        """
        try:
            import psutil
            
            # Verificar uso de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Verificar uso de memória
            memory = psutil.virtual_memory()
            
            # Verificar espaço em disco
            disk = psutil.disk_usage('/')
            
            # Logar se acima de limites
            if cpu_percent > 80:
                logger.warning("CPU acima de 80%%: %s%%" % cpu_percent)
            
            if memory.percent > 80:
                logger.warning("Memória acima de 80%%: %s%%" % memory.percent)
            
            if disk.percent > 90:
                logger.warning("Disco acima de 90%%: %s%%" % disk.percent)
        
        except Exception as e:
            logger.error("Erro no monitoramento: %s" % e)

def setup(cbpi):
    SystemMonitor(cbpi)
```

## Inicializadores (@on_startup)

Use `@on_startup` para executar código durante a inicialização:

```python
@on_startup(name="Inicialização", order=0)
async def inicializar(self):
    """
    Executado durante inicialização do sistema.
    """
    logger.info("Inicializando plugin...")
    # Código de inicialização
```

### Parâmetros

- `name`: Nome do inicializador
- `order`: Ordem de execução (menor = primeiro)

```python
@on_startup(name="Inicialização 1", order=0)  # Executa primeiro
@on_startup(name="Inicialização 2", order=1)  # Executa depois
```

## Exemplo: Inicialização

```python
class MeuPlugin:
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.bus.register_object(self)
    
    @on_startup(name="Configuração Inicial", order=0)
    async def configurar(self):
        """
        Configura plugin durante inicialização.
        """
        logger.info("Configurando plugin...")
        
        # Criar diretórios necessários
        os.makedirs("meu_plugin/data", exist_ok=True)
        
        # Carregar configuração
        config = self.cbpi.config.get("meu_plugin", {})
        logger.info("Configuração carregada: %s" % config)
    
    @background_task(name="Tarefa Periódica", interval=300)
    async def tarefa_periodica(self):
        """
        Tarefa executada a cada 5 minutos.
        """
        logger.info("Executando tarefa periódica...")

def setup(cbpi):
    MeuPlugin(cbpi)
```

## Exemplo Completo

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class MeuPluginCompleto:
    """
    Plugin com tarefas em background e inicialização.
    """
    
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self.cbpi.bus.register_object(self)
        self.last_backup = None
    
    @on_startup(name="Inicialização do Plugin", order=0)
    async def inicializar(self):
        """
        Inicializa plugin durante startup.
        """
        logger.info("Inicializando MeuPluginCompleto...")
        
        # Verificar se diretório existe
        import os
        backup_dir = os.path.join(".", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        logger.info("Plugin inicializado")
    
    @background_task(name="Backup Automático", interval=3600)
    async def backup_automatico(self):
        """
        Faz backup a cada hora.
        """
        try:
            logger.info("Iniciando backup automático...")
            
            # Lógica de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = "backups/backup_%s.zip" % timestamp
            
            # (implementar lógica de backup)
            
            self.last_backup = backup_file
            logger.info("Backup concluído: %s" % backup_file)
        
        except Exception as e:
            logger.error("Erro no backup: %s" % e)
    
    @background_task(name="Verificação de Saúde", interval=300)
    async def verificar_saude(self):
        """
        Verifica saúde do sistema a cada 5 minutos.
        """
        try:
            # Verificar componentes
            atores_ativos = sum(1 for a in self.cbpi.actor.data if a.instance and a.instance.state)
            sensores_ativos = sum(1 for s in self.cbpi.sensor.data if s.instance and s.instance.running)
            
            logger.info("Sistema: %s atores ativos, %s sensores ativos" % (atores_ativos, sensores_ativos))
        
        except Exception as e:
            logger.error("Erro na verificação: %s" % e)

def setup(cbpi):
    MeuPluginCompleto(cbpi)
    logger.info("MeuPluginCompleto carregado")
```

## Boas Práticas

1. **Use intervalos apropriados** (não muito frequentes)
2. **Trate exceções** adequadamente
3. **Use logging** para rastreamento
4. **Evite operações bloqueantes** (use async/await)
5. **Documente** o que cada tarefa faz
6. **Considere ordem de inicialização** com `order`

## Recursos Adicionais

- [Criando Plugins](02-criando-plugins.md)
- [Event Bus](09-event-bus.md)
- [Boas Práticas](12-boas-praticas.md)
- [API Reference](13-api-reference.md)

