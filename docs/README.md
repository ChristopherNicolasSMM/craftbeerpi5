# Documentação do Desenvolvedor - CraftBeerPi 5

Bem-vindo à documentação completa para desenvolvedores do CraftBeerPi 5. Esta documentação fornece guias detalhados para criar plugins, atores, sensores e outros recursos do sistema.

## 📚 Índice

### 1. [Guia de Início Rápido](01-inicio-rapido.md)
- Introdução ao desenvolvimento de plugins
- Estrutura básica de um plugin
- Primeiro plugin passo a passo

### 2. [Criando Plugins](02-criando-plugins.md)
- Estrutura de um plugin
- Arquivo config.yaml
- Função setup()
- Tipos de plugins (internos e externos)
- Distribuição de plugins

### 3. [Criando Atores (Actors)](03-criando-atores.md)
- Classe base CBPiActor
- Implementando métodos obrigatórios
- Propriedades configuráveis
- Ações customizadas
- Exemplos práticos

### 4. [Criando Sensores](04-criando-sensores.md)
- Classe base CBPiSensor
- Leitura de dados
- Atualização de valores
- Logging de dados
- Exemplos práticos

### 5. [Criando Etapas (Steps)](05-criando-etapas.md)
- Classe base CBPiStep
- Etapas de brassagem
- Etapas de fermentação
- Estados e resultados
- Exemplos práticos

### 6. [Criando Lógicas de Controle](06-criando-logicas.md)
- Lógicas de panela (CBPiKettleLogic)
- Lógicas de fermentador (CBPiFermenterLogic)
- Controle de temperatura
- Controle de pressão
- Exemplos práticos

### 7. [Criando Endpoints HTTP](07-criando-endpoints.md)
- Decorador @request_mapping
- Rotas REST
- Autenticação
- Validação de dados
- Exemplos práticos

### 8. [Propriedades e Configuração](08-propriedades-configuracao.md)
- Tipos de propriedades
- Property.Number
- Property.Text
- Property.Select
- Property.Actor, Sensor, Kettle, Fermenter
- Decorador @parameters

### 9. [Event Bus e Comunicação](09-event-bus.md)
- Sistema de eventos
- Decorador @on_event
- Publicando eventos
- Escutando eventos
- Wildcards e padrões

### 10. [Tarefas em Background](10-tarefas-background.md)
- Decorador @background_task
- Execução periódica
- Inicializadores (@on_startup)
- Exemplos práticos

### 11. [Extensões e Funcionalidades Avançadas](11-extensoes-avancadas.md)
- Classe CBPiExtension
- Adicionando páginas customizadas
- Integração com frontend
- Widgets customizados

### 12. [Boas Práticas e Dicas](12-boas-praticas.md)
- Convenções de código
- Tratamento de erros
- Logging
- Performance
- Testes

### 13. [API Reference](13-api-reference.md)
- Referência completa da API
- Classes principais
- Métodos e propriedades
- Exemplos de uso

## 🚀 Começando

Se você é novo no desenvolvimento de plugins para CraftBeerPi 5, comece pelo [Guia de Início Rápido](01-inicio-rapido.md).

## 📖 Estrutura de Documentação

Cada manual contém:
- **Introdução**: Explicação do conceito
- **Requisitos**: O que você precisa saber
- **Passo a Passo**: Tutorial detalhado
- **Exemplos**: Código completo funcionando
- **Referência**: Detalhes técnicos

## 🔗 Links Úteis

- [Repositório GitHub](https://github.com/ChristopherNicolasSMM/craftbeerpi5)
- [Documentação da API](13-api-reference.md)
- [Exemplos de Plugins](../cbpi/extension/)

## 💡 Contribuindo

Se você encontrar erros ou tiver sugestões para melhorar esta documentação, por favor abra uma issue ou pull request no repositório.

---

**Última atualização**: 2024
**Versão do CraftBeerPi**: 5.0.0

