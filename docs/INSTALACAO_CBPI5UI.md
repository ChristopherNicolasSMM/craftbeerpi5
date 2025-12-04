# Guia de Instalação do cbpi5ui

Este guia explica como instalar o `cbpi5ui` (Interface de Usuário do CraftBeerPi 5) diretamente do repositório GitHub.

---

## 📋 Índice

1. [Instalação Direta via pip](#instalação-direta-via-pip)
2. [Instalação via requirements.txt](#instalação-via-requirementstxt)
3. [Instalação via setup.py](#instalação-via-setuppy)
4. [Opções de Instalação](#opções-de-instalação)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Instalação Direta via pip

### Instalar de um Commit Específico

```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@860c88b24053f67eca5d96020fdcc2b30580b283
```

### Instalar da Branch Main

```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@main
```

### Instalar de uma Branch Específica

```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@nome-da-branch
```

### Instalar de uma Tag

```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@v1.0.0
```

---

## 📦 Instalação via requirements.txt

O arquivo `requirements.txt` já está configurado para instalar de um commit específico:

```txt
cbpi5ui @ git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@860c88b24053f67eca5d96020fdcc2b30580b283
```

### Instalar todas as dependências:

```bash
# Certifique-se de estar no diretório craftbeerpi5
cd craftbeerpi5

# Ative o ambiente virtual (se estiver usando)
# Windows:
.\venvCraftbeerPi\Scripts\Activate.ps1
# Linux/Mac:
source venvCraftbeerPi/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### Atualizar apenas o cbpi5ui:

```bash
pip install --upgrade --force-reinstall git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@860c88b24053f67eca5d96020fdcc2b30580b283
```

---

## 🔧 Instalação via setup.py

O arquivo `setup.py` também está configurado para instalar do GitHub. Ao instalar o pacote `craftbeerpi5`, o `cbpi5ui` será instalado automaticamente:

```bash
# No diretório craftbeerpi5
pip install -e .
```

Ou para instalação em modo de desenvolvimento:

```bash
pip install -e . --no-deps
pip install -r requirements.txt
```

---

## 🎯 Opções de Instalação

### 1. Commit Específico (Recomendado para Produção)

**Vantagens:**
- ✅ Versão fixa e estável
- ✅ Reproduzível
- ✅ Não muda sem atualização explícita

**Sintaxe:**
```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@<hash-do-commit>
```

**Exemplo:**
```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@860c88b24053f67eca5d96020fdcc2b30580b283
```

### 2. Branch Main (Desenvolvimento)

**Vantagens:**
- ✅ Sempre a versão mais recente
- ✅ Útil para desenvolvimento

**Desvantagens:**
- ⚠️ Pode quebrar com atualizações
- ⚠️ Não é reproduzível

**Sintaxe:**
```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@main
```

### 3. Branch Específica

**Sintaxe:**
```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@nome-da-branch
```

### 4. Tag de Versão

**Sintaxe:**
```bash
pip install git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@v1.0.0
```

---

## 📝 Atualizando o Commit no requirements.txt

Para atualizar para um novo commit:

1. **Edite o arquivo `requirements.txt`:**
   ```txt
   cbpi5ui @ git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@<novo-hash-commit>
   ```

2. **Reinstale:**
   ```bash
   pip install --upgrade --force-reinstall -r requirements.txt
   ```

---

## 📝 Atualizando o Commit no setup.py

Para atualizar o `setup.py`:

1. **Edite o arquivo `setup.py` (linha ~53):**
   ```python
   'cbpi5ui @ git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@<novo-hash-commit>',
   ```

2. **Reinstale:**
   ```bash
   pip install -e . --force-reinstall
   ```

---

## 🔍 Verificar Instalação

### Verificar se está instalado:

```bash
pip show cbpi5ui
```

### Verificar a versão instalada:

```bash
pip list | grep cbpi5ui
```

### Verificar o local de instalação:

```bash
python -c "import cbpi5ui; print(cbpi5ui.__file__)"
```

---

## 🛠️ Troubleshooting

### Problema: "Command 'git' not found"

**Solução:**
Instale o Git no seu sistema:
- **Windows:** Baixe de [git-scm.com](https://git-scm.com/)
- **Linux:** `sudo apt-get install git` (Ubuntu/Debian) ou `sudo yum install git` (CentOS/RHEL)
- **Mac:** `brew install git` ou baixe de [git-scm.com](https://git-scm.com/)

### Problema: "Permission denied" ou "Access denied"

**Solução:**
- Use um ambiente virtual (recomendado)
- Ou use `pip install --user` para instalar apenas para o usuário atual

### Problema: "Could not find a version that satisfies the requirement"

**Solução:**
- Verifique se o commit/branch/tag existe no repositório
- Verifique se a URL está correta
- Certifique-se de que o Git está instalado e acessível

### Problema: "ModuleNotFoundError: No module named 'cbpi5ui'"

**Solução:**
1. Verifique se está no ambiente virtual correto:
   ```bash
   which python  # Linux/Mac
   where python  # Windows
   ```

2. Reinstale o pacote:
   ```bash
   pip install --upgrade --force-reinstall git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@860c88b24053f67eca5d96020fdcc2b30580b283
   ```

### Problema: Mudanças não aparecem após reinstalação

**Solução:**
1. Limpe o cache do pip:
   ```bash
   pip cache purge
   ```

2. Desinstale completamente:
   ```bash
   pip uninstall cbpi5ui -y
   ```

3. Reinstale:
   ```bash
   pip install --no-cache-dir git+https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui.git@860c88b24053f67eca5d96020fdcc2b30580b283
   ```

---

## 📚 Referências

- [pip install from git](https://pip.pypa.io/en/stable/topics/vcs-support/)
- [GitHub - CraftBeerPi 5 UI](https://github.com/ChristopherNicolasSMM/craftbeerpi5-ui)
- [Documentação do CraftBeerPi 5](../README.md)

---

**Última atualização:** 2024  
**Versão do Documento:** 1.0

