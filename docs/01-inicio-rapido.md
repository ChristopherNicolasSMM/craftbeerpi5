# Guia de Início Rápido

Este guia irá ajudá-lo a criar seu primeiro plugin para o CraftBeerPi 5 em poucos minutos.

## Pré-requisitos

- Python 3.11 ou superior
- Conhecimento básico de Python
- CraftBeerPi 5 instalado e funcionando

## O que é um Plugin?

Um plugin é uma extensão do CraftBeerPi que adiciona novas funcionalidades ao sistema, como:
- Novos tipos de atuadores (ex: GPIO, MQTT)
- Novos tipos de sensores (ex: DS18B20, HTTP)
- Novas etapas de processo (ex: Mash, Boil)
- Novas lógicas de controle (ex: Hysteresis, PID)
- Endpoints HTTP customizados
- Funcionalidades avançadas

## Estrutura Básica de um Plugin

Um plugin mínimo consiste em:

```
meu_plugin/
├── __init__.py          # Código do plugin
└── config.yaml          # Configuração do plugin
```

## Criando seu Primeiro Plugin

Vamos criar um plugin simples que adiciona um atuador "dummy" (simulado).

### Passo 1: Criar a Estrutura

Crie uma pasta para seu plugin dentro de `cbpi/extension/`:

```bash
mkdir cbpi/extension/meu_primeiro_plugin
cd cbpi/extension/meu_primeiro_plugin
```

### Passo 2: Criar config.yaml

Crie o arquivo `config.yaml`:

```yaml
name: Meu Primeiro Plugin
version: 4
active: true
```

**Nota**: A versão 4 é mantida para compatibilidade. Para CraftBeerPi 5, você pode usar version: 5.

### Passo 3: Criar __init__.py

Crie o arquivo `__init__.py` com o código do plugin:

```python
# -*- coding: utf-8 -*-
from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([])
class MeuPrimeiroAtor(CBPiActor):
    """
    Um atuador simples de exemplo.
    """
    
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        logger.info("MeuPrimeiroAtor inicializado: %s" % id)
    
    async def on(self, power=100):
        """
        Liga o atuador.
        
        Args:
            power: Potência (0-100)
        """
        logger.info("Atuador %s LIGADO com potência %s" % (self.id, power))
        self.state = True
    
    async def off(self):
        """
        Desliga o atuador.
        """
        logger.info("Atuador %s DESLIGADO" % self.id)
        self.state = False
    
    def get_state(self):
        """
        Retorna o estado atual do atuador.
        """
        return dict(state=self.state)

def setup(cbpi):
    """
    Função obrigatória chamada durante a inicialização do sistema.
    
    Aqui você registra todos os componentes do seu plugin.
    
    Args:
        cbpi: Instância principal do CraftBeerPi
    """
    cbpi.plugin.register("Meu Primeiro Ator", MeuPrimeiroAtor)
    logger.info("Plugin 'Meu Primeiro Plugin' carregado com sucesso!")
```

### Passo 4: Testar o Plugin

1. Reinicie o CraftBeerPi 5
2. Acesse a interface web
3. Vá em Hardware > Atores
4. Clique em "Adicionar Ator"
5. Você deve ver "Meu Primeiro Ator" na lista de tipos disponíveis

## Explicação do Código

### Importações

```python
from cbpi.api import *
```

Importa todas as classes e decoradores necessários do CraftBeerPi.

### Decorador @parameters

```python
@parameters([])
```

Define as propriedades configuráveis do componente. Neste exemplo, não há propriedades (lista vazia).

### Classe do Atuador

```python
class MeuPrimeiroAtor(CBPiActor):
```

Herda de `CBPiActor`, a classe base para todos os atuadores.

### Métodos Obrigatórios

- `on(power)`: Liga o atuador com potência especificada
- `off()`: Desliga o atuador
- `get_state()`: Retorna estado atual

### Função setup()

```python
def setup(cbpi):
    cbpi.plugin.register("Meu Primeiro Ator", MeuPrimeiroAtor)
```

Esta função é chamada automaticamente durante a inicialização. Use-a para registrar seus componentes.

## Próximos Passos

Agora que você criou seu primeiro plugin, você pode:

1. **Adicionar Propriedades**: Veja [Propriedades e Configuração](08-propriedades-configuracao.md)
2. **Criar um Sensor**: Veja [Criando Sensores](04-criando-sensores.md)
3. **Adicionar Ações**: Veja [Criando Atores](03-criando-atores.md)
4. **Criar Endpoints HTTP**: Veja [Criando Endpoints HTTP](07-criando-endpoints.md)

## Exemplo Completo

Você pode encontrar exemplos completos de plugins na pasta `cbpi/extension/`:

- `dummyactor/` - Atuador simples de exemplo
- `dummysensor/` - Sensor simples de exemplo
- `gpioactor/` - Atuador GPIO real
- `onewire/` - Sensor DS18B20

## Dicas

- Sempre use `logger` para mensagens de log
- Trate exceções adequadamente
- Use type hints quando possível
- Documente seu código com docstrings
- Teste seu plugin antes de distribuir

## Problemas Comuns

### Plugin não aparece na lista

- Verifique se `active: true` no `config.yaml`
- Verifique se a versão está correta (4 ou 5)
- Verifique os logs para erros

### Erro ao carregar plugin

- Verifique a sintaxe do Python
- Verifique se todos os imports estão corretos
- Verifique se a função `setup()` está definida

### Atuador não funciona

- Verifique se os métodos `on()` e `off()` estão implementados
- Verifique os logs para mensagens de erro
- Verifique se o plugin foi registrado corretamente

## Recursos Adicionais

- [Documentação Completa de Plugins](02-criando-plugins.md)
- [Referência da API](13-api-reference.md)
- [Boas Práticas](12-boas-praticas.md)

