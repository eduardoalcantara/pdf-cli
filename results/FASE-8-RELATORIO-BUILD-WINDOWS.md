# FASE 8 - Relatório de Build para Windows

**PDF-cli - Ferramenta CLI para Edição de PDFs**
**Versão:** 0.7.0 (Fase 7 - HELP Avançado)
**Data:** 20/11/2025
**Sistema:** Windows 10+

---

## 📋 SUMÁRIO

1. [Objetivo](#objetivo)
2. [Processo de Build](#processo-de-build)
3. [Configurações e Parâmetros](#configurações-e-parâmetros)
4. [Problemas Encontrados e Soluções](#problemas-encontrados-e-soluções)
5. [Status do Build](#status-do-build)
6. [Uso do Executável](#uso-do-executável)
7. [Limitações Conhecidas](#limitações-conhecidas)
8. [Próximos Passos](#próximos-passos)

---

## 🎯 OBJETIVO

Criar um executável standalone para Windows (`pdf-cli.exe`) que permita executar o PDF-cli sem necessidade de instalação do Python ou dependências. O executável deve ser portável e funcional em qualquer máquina Windows 10+.

---

## 🔧 PROCESSO DE BUILD

### Script de Build

O processo de build é automatizado pelo script `scripts/build_win.bat`, que executa os seguintes passos:

1. **Verificação do Ambiente**
   - Verifica se o Python 3.8+ está instalado
   - Confirma que o diretório do projeto está correto (`D:\proj\pdf-cli`)

2. **Preparação do Ambiente Virtual**
   - Cria ambiente virtual (`.venv`) se não existir
   - Ativa o ambiente virtual automaticamente

3. **Instalação de Dependências**
   - Atualiza o `pip`
   - Instala dependências de `requirements.txt`:
     - `PyMuPDF>=1.23.0`
     - `PyPDF2>=3.0.0`
     - `Pillow>=10.0.0` (instalado explicitamente se necessário)
   - Instala `PyInstaller` se não estiver presente

4. **Limpeza de Builds Antigos**
   - Remove diretório `build/` se existir
   - Remove `dist/pdf-cli.exe` se existir
   - Remove `pdf-cli.spec` se existir

5. **Compilação com PyInstaller**
   - Usa `--onefile` para gerar um único executável
   - Inclui todos os módulos necessários via `--collect-submodules` e `--hidden-import`
   - Configura caminhos corretos com `--paths src`

6. **Organização do Output**
   - Move o executável gerado para `dist/windows/pdf-cli.exe`
   - Exibe mensagem de sucesso com instruções de teste

---

## ⚙️ CONFIGURAÇÕES E PARÂMETROS

### Comando PyInstaller Utilizado

```batch
pyinstaller --onefile --name pdf-cli --paths src --collect-submodules cli --collect-submodules app --collect-submodules core --hidden-import fitz --hidden-import PyPDF2 --hidden-import PIL --hidden-import cli --hidden-import cli.help --hidden-import cli.parser --hidden-import cli.commands --hidden-import app --hidden-import app.services --hidden-import app.pdf_repo --hidden-import app.logging --hidden-import core --hidden-import core.models --hidden-import core.exceptions --hidden-import core.engine_manager --hidden-import core.font_manager --console --clean src\pdf_cli.py
```

### Parâmetros Explicados

| Parâmetro | Descrição |
|-----------|-----------|
| `--onefile` | Gera um único executável (standalone) |
| `--name pdf-cli` | Nome do executável gerado |
| `--paths src` | Adiciona diretório `src/` ao path do Python |
| `--collect-submodules cli` | Coleta todos os submódulos de `cli` |
| `--collect-submodules app` | Coleta todos os submódulos de `app` |
| `--collect-submodules core` | Coleta todos os submódulos de `core` |
| `--hidden-import fitz` | Força inclusão do módulo `fitz` (PyMuPDF) |
| `--hidden-import PyPDF2` | Força inclusão do PyPDF2 |
| `--hidden-import PIL` | Força inclusão do Pillow (PIL) |
| `--hidden-import cli.*` | Força inclusão de todos os módulos CLI |
| `--hidden-import app.*` | Força inclusão de todos os módulos APP |
| `--hidden-import core.*` | Força inclusão de todos os módulos CORE |
| `--console` | Mantém janela de console (não esconde) |
| `--clean` | Limpa arquivos temporários antes de compilar |
| `src\pdf_cli.py` | Entrypoint da aplicação |

### Modificações no Código Fonte

O arquivo `src/pdf_cli.py` foi modificado para detectar quando está rodando como executável PyInstaller e ajustar o `sys.path` corretamente:

```python
if getattr(sys, 'frozen', False):
    # Rodando como executável compilado (PyInstaller)
    base_path = Path(sys._MEIPASS)
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
else:
    # Rodando como script Python normal
    sys.path.insert(0, str(Path(__file__).parent))
```

Isso garante que os módulos `cli`, `app` e `core` sejam encontrados corretamente tanto no desenvolvimento quanto no executável.

---

## 🐛 PROBLEMAS ENCONTRADOS E SOLUÇÕES

### Problema 1: Erro de Sintaxe no Script Batch

**Sintoma:**
```
else foi inesperado neste momento.
```

**Causa:**
Uso de estruturas `if/else` complexas no script batch que causavam problemas de parsing no CMD.exe.

**Solução:**
Refatoração do script para usar estruturas `if/else` simples e diretas, evitando aninhamentos complexos:

```batch
if errorlevel 1 (
    echo [ERRO] ...
    pause
    exit /b 1
) else (
    echo [INFO] ...
)
```

### Problema 2: Módulos Não Encontrados no Executável

**Sintoma:**
```
ModuleNotFoundError: No module named 'cli'
```

**Causa:**
PyInstaller não estava coletando automaticamente os módulos em subdiretórios (`cli/`, `app/`, `core/`).

**Solução:**
Adição de múltiplas estratégias:
1. **`--paths src`**: Adiciona `src/` ao path do Python durante a análise
2. **`--collect-submodules`**: Coleta automaticamente todos os submódulos de `cli`, `app` e `core`
3. **`--hidden-import`**: Força inclusão explícita de cada módulo necessário
4. **Modificação do código**: Ajuste em `pdf_cli.py` para detectar executável PyInstaller e usar `sys._MEIPASS`

### Problema 3: Caracteres Especiais no Script Batch

**Sintoma:**
Erros de parsing relacionados a caracteres especiais ou acentos.

**Solução:**
Remoção de todos os acentos e caracteres especiais do script batch para garantir compatibilidade com CMD.exe.

### Problema 4: Caminho Absoluto do Projeto

**Sintoma:**
Script não encontrava arquivos quando executado de diferentes diretórios.

**Solução:**
Uso de caminho absoluto fixo no script:

```batch
set PROJECT_ROOT=D:\proj\pdf-cli
cd /d "%PROJECT_ROOT%"
```

Isso garante que o script sempre execute do diretório correto, independente de onde seja chamado.

### Problema 5: PyInstaller Já Instalado

**Sintoma:**
Script não sabia como proceder quando o PyInstaller já estava instalado, causando confusão no fluxo.

**Solução:**
Estrutura condicional clara:

```batch
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller
) else (
    echo [INFO] PyInstaller ja instalado
)
```

---

## ✅ STATUS DO BUILD

### Status Atual

✅ **Build Funcional**

O script `scripts/build_win.bat` está funcionando corretamente e gera o executável `dist/windows/pdf-cli.exe` sem erros.

### Arquivo Gerado

- **Localização:** `dist/windows/pdf-cli.exe`
- **Tamanho:** ~37 MB (aproximadamente, depende das dependências)
- **Tipo:** Executável standalone Windows (x64)
- **Dependências:** Todas incluídas no executável (PyMuPDF, PyPDF2, Pillow)

### Testes Realizados

1. ✅ **Compilação:** Script executa sem erros
2. ✅ **Executável Gerado:** Arquivo criado em `dist/windows/pdf-cli.exe`
3. ⚠️ **Teste de Execução:** Necessário testar o executável em ambiente limpo

### Pendências

- ⚠️ **Teste em Ambiente Limpo:** Validar que o executável funciona em máquina sem Python instalado
- ⚠️ **Teste de Todos os Comandos:** Validar que todos os comandos CLI funcionam no executável
- ⚠️ **Teste de Hash:** Gerar hash SHA256 do executável para verificação de integridade

---

## 📖 USO DO EXECUTÁVEL

### Requisitos

- Windows 10 ou superior
- **Não requer** instalação de Python ou dependências

### Como Executar

1. **Navegue até o diretório:**
   ```cmd
   cd dist\windows
   ```

2. **Execute o comando:**
   ```cmd
   pdf-cli.exe --help
   pdf-cli.exe --version
   ```

### Exemplos de Uso

```cmd
REM Exportar textos de um PDF
pdf-cli.exe export-text documento.pdf textos.json

REM Editar texto em um PDF
pdf-cli.exe edit-text documento.pdf editado.pdf --content "TEXTO" --new-content "NOVO TEXTO" --all-occurrences

REM Listar fontes do PDF
pdf-cli.exe list-fonts documento.pdf

REM Unir múltiplos PDFs
pdf-cli.exe merge arquivo1.pdf arquivo2.pdf resultado.pdf

REM Dividir PDF em múltiplos arquivos
pdf-cli.exe split documento.pdf outputs/ --pages-per-file 10

REM Ajuda detalhada de um comando
pdf-cli.exe --help edit-text
pdf-cli.exe edit-text --help
```

### Comandos Disponíveis

#### Extração
- `export-text` - Extrai apenas textos do PDF para JSON
- `export-objects` - Extrai objetos do PDF para JSON
- `export-images` - Extrai imagens do PDF como arquivos PNG/JPG
- `list-fonts` - Lista todas as fontes e variantes usadas no PDF

#### Edição
- `edit-text` - Edita objeto de texto no PDF
- `edit-table` - Edita tabela (funcionalidade em desenvolvimento)
- `replace-image` - Substitui imagem no PDF
- `insert-object` - Insere novo objeto no PDF

#### Restauração e Metadados
- `restore-from-json` - Restaura PDF via JSON
- `edit-metadata` - Edita metadados do PDF

#### Manipulação Estrutural
- `merge` - Une múltiplos PDFs em um único documento
- `delete-pages` - Exclui páginas específicas do PDF
- `split` - Divide PDF em múltiplos arquivos

---

## ⚠️ LIMITAÇÕES CONHECIDAS

### 1. Tamanho do Executável

- O executável gerado tem aproximadamente **37 MB** devido às dependências incluídas (PyMuPDF, PyPDF2, Pillow).
- Isso é esperado para um executável standalone que inclui todas as dependências.

### 2. Tempo de Inicialização

- O executável pode ter um pequeno atraso na inicialização devido à descompactação dos arquivos temporários (PyInstaller usa `sys._MEIPASS`).

### 3. Funcionalidades em Desenvolvimento

- `edit-table`: Funcionalidade ainda em desenvolvimento, requer algoritmo de detecção de estrutura de tabelas.

### 4. Compatibilidade

- Testado apenas no Windows 10/11. Não testado em versões anteriores (Windows 7/8).

### 5. Antivírus

- Alguns antivírus podem marcar executáveis gerados pelo PyInstaller como suspeitos devido à técnica de empacotamento. Isso é um falso positivo comum.

### 6. Permissões

- O executável pode precisar de permissões de escrita para criar logs e arquivos de saída.

---

## 🔄 PRÓXIMOS PASSOS

### Testes Pendentes

1. **Teste em Ambiente Limpo**
   - Instalar Windows em máquina virtual
   - Copiar apenas o executável `pdf-cli.exe`
   - Testar todos os comandos básicos

2. **Teste de Todos os Comandos**
   - Validar que todos os 13 comandos funcionam corretamente
   - Testar com arquivos PDF reais do repositório (`examples/`)

3. **Teste de Performance**
   - Medir tempo de inicialização
   - Medir tempo de execução de comandos
   - Comparar com execução via Python

4. **Teste de Integridade**
   - Gerar hash SHA256 do executável
   - Documentar hash para verificação futura

### Melhorias Futuras

1. **Assinatura Digital**
   - Assinar o executável com certificado digital para evitar avisos de antivírus

2. **Redução de Tamanho**
   - Investigar opções para reduzir o tamanho do executável (UPX, exclusão de módulos não usados)

3. **Instalador**
   - Criar instalador MSI/NSIS para facilitar instalação

4. **Documentação de Distribuição**
   - Criar guia de distribuição para usuários finais
   - Adicionar informações de versão e build no executável

5. **CI/CD**
   - Automatizar o build em pipeline CI/CD (GitHub Actions, por exemplo)

---

## 📝 OBSERVAÇÕES TÉCNICAS

### Estrutura do Projeto

```
pdf-cli/
├── src/                    # Código fonte
│   ├── pdf_cli.py         # Entrypoint
│   ├── cli/               # Módulos CLI
│   ├── app/               # Módulos de aplicação
│   └── core/              # Módulos de domínio
├── scripts/
│   └── build_win.bat      # Script de build para Windows
├── dist/
│   └── windows/
│       └── pdf-cli.exe    # Executável gerado
└── requirements.txt       # Dependências
```

### Dependências Incluídas

- **PyMuPDF (fitz)**: Biblioteca principal para manipulação de PDFs
- **PyPDF2**: Biblioteca auxiliar para operações complementares
- **Pillow (PIL)**: Manipulação de imagens (filtros)

### Versão do Python

- **Mínima:** Python 3.8
- **Recomendada:** Python 3.10+
- **Testada:** Python 3.14.0

---

## ✅ CONCLUSÃO

O processo de build para Windows foi implementado com sucesso. O script `scripts/build_win.bat` está funcional e gera um executável standalone que pode ser distribuído sem necessidade de instalação de Python ou dependências.

### Status Final

✅ Script de build implementado e funcional
✅ Executável gerado com sucesso
⚠️ Testes em ambiente limpo pendentes
⚠️ Testes de todos os comandos pendentes

### Próximas Ações

1. Testar o executável em ambiente limpo (sem Python)
2. Validar todos os comandos CLI no executável
3. Gerar hash SHA256 para verificação de integridade
4. Documentar processo de distribuição para usuários finais

---

**Relatório gerado em:** 20/11/2025
**Fase:** Fase 8 - Distribuição Portátil e Scripts de Build Cross-platform
**Versão do Projeto:** 0.7.0 (Fase 7 - HELP Avançado)
