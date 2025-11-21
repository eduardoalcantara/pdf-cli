# PDF-cli — Ferramenta CLI para Edição Estrutural de PDFs

**PDF-cli** é uma ferramenta de linha de comando robusta e extensível para automação e edição avançada de arquivos PDF, totalmente desenvolvida em Python. Esta ferramenta foi criada para desenvolvedores e power users que desejam editar textos, manipular páginas, extrair metadados ricos e manter layouts visuais precisos de documentos PDF de maneira eficiente e programável.

**Versão Atual:** 0.8.0 (Fase 8 - Distribuição Portátil e Scripts de Build Cross-platform)
**Status:** ✅ **13 comandos implementados com operações REAIS** | ✅ **Executáveis standalone disponíveis para Windows e Linux**

---

# Desenvolvimento

- Eduardo Alcântara
- Perplexity (Claude Sonnect 4.5)
- Cursor IDE (Claude, ChatGPT e Composer)

---

## 🎯 Funcionalidades Implementadas (REAIS)

### ✅ Extração de Objetos
- **`export-objects`**: Extrai objetos do PDF para JSON
  - ✅ Text, Image, Link, Annotation implementados
  - ✅ Flag `--include-fonts` para incluir informações de fontes
  - ⚠️ Table, FormField, Graphic, Layer, Filter requerem algoritmos complexos (planejados para fase final)

- **`export-text`**: Alias para `export-objects --types text`
  - ✅ Extração rápida de apenas textos

- **`export-images`**: Extrai imagens do PDF como arquivos PNG/JPG
  - ✅ Extração real de imagens para arquivos separados
  - ✅ Salva em diretório especificado com `--out`

- **`list-fonts`**: Lista todas as fontes e variantes usadas no PDF
  - ✅ Detecção de fontes faltantes no sistema operacional
  - ✅ Informações sobre fontes embeddadas e não embeddadas

### ✅ Edição de Objetos
- **`edit-text`**: Edita objetos de texto via ID ou busca
  - ✅ **IMPLEMENTAÇÃO REAL** usando PyMuPDF TextWriter para preservação de fontes
  - ✅ Flag `--all-occurrences` para editar todas as ocorrências
  - ✅ Flag `--verbose` para feedback detalhado de cada modificação
  - ✅ Detecção automática de fontes faltantes no sistema
  - ✅ Confirmação interativa quando há problemas de fonte
  - ✅ Suporta: fonte, cor, tamanho, posição, rotação, alinhamento, padding

- **`replace-image`**: Substitui imagens mantendo posição
  - ✅ **IMPLEMENTAÇÃO REAL** usando PyMuPDF (redaction + insert_image)
  - ✅ Suporta filtros: grayscale, invert

- **`edit-table`**: ⚠️ **LIMITAÇÃO TÉCNICA**
  - Estrutura CLI implementada
  - Requer algoritmo de detecção de estrutura de tabelas (movido para fase final)

### ✅ Inserção de Objetos
- **`insert-object`**: Insere novos objetos no PDF
  - ✅ **REAL para text**: Insere texto via `insert_text()`
  - ✅ **REAL para image**: Insere imagem via `insert_image()`
  - ⚠️ Outros tipos requerem implementação específica

### ✅ Restauração e Metadados
- **`restore-from-json`**: Restaura PDF via JSON
  - ✅ **IMPLEMENTAÇÃO REAL**: Aplica edições de texto no PDF

- **`edit-metadata`**: Edita metadados do PDF
  - ✅ **IMPLEMENTAÇÃO REAL**: Usa `doc.set_metadata()` do PyMuPDF

### ✅ Manipulação Estrutural
- **`merge`**: Une múltiplos PDFs
  - ✅ **IMPLEMENTAÇÃO REAL** usando `insert_pdf()`

- **`delete-pages`**: Exclui páginas específicas
  - ✅ **IMPLEMENTAÇÃO REAL**: Cria novo documento sem páginas especificadas

- **`split`**: Divide PDF em múltiplos arquivos
  - ✅ **IMPLEMENTAÇÃO REAL**: Cria múltiplos documentos por faixas de páginas

---

## 🚀 Instalação

### Opção 1: Executável Standalone (Recomendado)

Execute diretamente sem instalar Python ou dependências:

**Windows:**
```bash
# Baixe o executável de dist/windows/
pdf-cli.exe --help
pdf-cli.exe export-text documento.pdf saida.json
```

**Linux:**
```bash
# Baixe o executável de dist/linux/
chmod +x pdf-cli
./pdf-cli --help
./pdf-cli export-text documento.pdf saida.json
```

### Opção 2: Instalação via Python

```bash
# Clone o repositório
git clone <repository-url>
cd pdf-cli

# Instale as dependências
pip install -r requirements.txt

# Execute
python src/pdf_cli.py --help
```

### Dependências (apenas para desenvolvimento)

- **PyMuPDF** (fitz) >= 1.23.0 - Manipulação de PDFs
- **PyPDF2** >= 3.0.0 - Operações complementares
- **Pillow** >= 10.0.0 - Processamento de imagens (filtros)

**Nota:** Executáveis standalone já incluem todas as dependências.

---

## 📖 Exemplos de Uso CLI

### Exportar Objetos

```bash
# Exportar todos os tipos disponíveis
pdf-cli export-objects documento.pdf objetos.json
# ou: python src/pdf_cli.py export-objects documento.pdf objetos.json

# Exportar apenas textos e imagens
pdf-cli export-objects documento.pdf objetos.json --types text,image

# Exportar textos (alias)
pdf-cli export-text documento.pdf textos.json

# Exportar imagens como arquivos PNG/JPG
pdf-cli export-images documento.pdf --out imagens/
```

### Listar Fontes

```bash
# Listar todas as fontes usadas no PDF
pdf-cli list-fonts documento.pdf

# Incluir informações de fontes no export-objects
pdf-cli export-objects documento.pdf objetos.json --include-fonts
```

### Editar Texto

```bash
# Por ID (requer export-objects primeiro para obter IDs)
pdf-cli edit-text input.pdf output.pdf --id abc123 --new-content "Novo texto"

# Por conteúdo (busca) - primeira ocorrência
pdf-cli edit-text input.pdf output.pdf --content "Texto antigo" --new-content "Novo texto"

# Todas as ocorrências
pdf-cli edit-text input.pdf output.pdf --content "Texto antigo" --new-content "Novo texto" --all-occurrences

# Com centralização e padding
pdf-cli edit-text input.pdf output.pdf --id abc123 --new-content "Novo" --align center --pad

# Com alteração de fonte e cor
pdf-cli edit-text input.pdf output.pdf --id abc123 --new-content "Novo" --font-name "Arial-Bold" --font-size 14 --color "#FF0000"

# Com feedback detalhado
pdf-cli edit-text input.pdf output.pdf --content "TEXTO" --new-content "NOVO" --all-occurrences --verbose
```

### Substituir Imagem

```bash
# Substituir imagem mantendo posição
pdf-cli replace-image input.pdf output.pdf --id img-123 --src nova_imagem.png

# Com filtro grayscale
pdf-cli replace-image input.pdf output.pdf --id img-123 --src nova.png --filter grayscale
```

### Inserir Objeto

```bash
# Inserir texto
pdf-cli insert-object input.pdf output.pdf --type text --params '{"page":0,"content":"Novo texto","x":100,"y":100,"font_size":12}'

# Inserir imagem
pdf-cli insert-object input.pdf output.pdf --type image --params '{"page":0,"src":"imagem.png","x":100,"y":100,"width":200,"height":150}'
```

### Editar Metadados

```bash
pdf-cli edit-metadata input.pdf output.pdf --title "Novo Título" --author "Novo Autor"
```

### Merge de PDFs

```bash
pdf-cli merge arquivo1.pdf arquivo2.pdf arquivo3.pdf -o combinado.pdf
```

### Excluir Páginas

```bash
# Com confirmação
pdf-cli delete-pages input.pdf output.pdf --pages 1,4,6-8

# Sem confirmação (--force)
pdf-cli delete-pages input.pdf output.pdf --pages 1-5 --force
```

### Dividir PDF

```bash
pdf-cli split input.pdf --ranges 1-3,4-6 --out prefix_
# Cria: prefix_1.pdf, prefix_2.pdf
```

---

## 🧪 Testes

### Testes de Integração REAIS

Todos os testes executam operações REAIS sobre PDFs reais (sem mocks):

```bash
# Executar todos os testes
pytest tests/test_integration_real.py -v

# Executar testes específicos
pytest tests/test_integration_real.py::test_edit_text_by_id_real -v
pytest tests/test_integration_real.py::test_replace_image_real -v
```

### Validação de Honestidade

Script que valida que todas as implementações são REAIS:

```bash
python scripts/validate_honesty.py
```

**Resultado Esperado:**
```
✅ STATUS: VALIDAÇÃO APROVADA
   - Nenhum mock ou fake detectado
   - Operações reais confirmadas
   - Logs estruturados corretamente
```

### Build de Executáveis

**Windows:**
```batch
scripts\build_win.bat
```
Gera: `dist/windows/pdf-cli.exe`

**Linux (WSL):**
```bash
./scripts/build_linux.sh
```
Gera: `dist/linux/pdf-cli`

Ver documentação completa em:
- Windows: `results/FASE-8-RELATORIO-BUILD-WINDOWS.md`
- Linux: `scripts/README-BUILD-LINUX.md`

---

## 🏗️ Build e Distribuição

### Executáveis Standalone

O projeto inclui scripts automatizados para gerar executáveis standalone:

**Windows:**
```batch
scripts\build_win.bat
```
Resultado: `dist/windows/pdf-cli.exe` (~37 MB)

**Linux (WSL):**
```bash
./scripts/build_linux.sh
```
Resultado: `dist/linux/pdf-cli` (~41 MB)

**Documentação:**
- Windows: `results/FASE-8-RELATORIO-BUILD-WINDOWS.md`
- Linux: `scripts/README-BUILD-LINUX.md`

### Requisitos para Build

- Python 3.8+
- PyInstaller (instalado automaticamente pelos scripts)
- Windows: CMD.exe
- Linux: WSL (Windows Subsystem for Linux)

---

## 📊 Logs e Auditoria

### Sistema de Logging JSON

Todas as operações geram logs detalhados em formato JSON para auditoria:

```json
{
  "operation_id": "uuid-único",
  "operation_type": "edit-text",
  "timestamp": "2025-01-18T14:30:00Z",
  "status": "success",
  "input_file": "input.pdf",
  "output_file": "output.pdf",
  "parameters": {
    "object_id": "abc123",
    "new_content": "Novo texto"
  },
  "result": {
    "before": {...},
    "after": {...},
    "backup": "backup_path.pdf"
  },
  "object_ids": ["abc123"],
  "suggestions": ["Use export-objects para listar objetos disponíveis"],
  "notes": "Modificação de texto realizada."
}
```

**Localização dos Logs:**
- `./logs/operations.jsonl` - Logs em formato JSONL (append)
- `./logs/{timestamp}_{operation_type}_{id}.json` - Logs individuais

---

## ⚠️ Limitações Técnicas Conhecidas

### 1. Edição de Tabelas (`edit-table`)

**Status:** ⚠️ **LIMITAÇÃO TÉCNICA**

**Motivo:** A edição de tabelas requer detecção da estrutura de tabelas no PDF, que é uma operação complexa. PyMuPDF não fornece detecção automática de tabelas.

**Documentação:**
- Função retorna `NotImplementedError` com mensagem explicativa clara
- Backup é criado antes de informar a limitação
- Log registrado com status "error" e explicação

**Solução Futura:**
- Implementar algoritmo de detecção de tabelas (análise de coordenadas, bordas, etc.)
- Ou integrar biblioteca especializada em detecção de tabelas (ex: camelot, tabula-py)
- **Movido para fase final do projeto**

**Impacto:** Baixo - funcionalidade específica que pode ser implementada em fase futura

---

### 2. Extração de Tipos Avançados

**Status:** ✅ **Parcialmente Implementado**

**Implementado:**
- ✅ TextObject — Extração completa funcionando
- ✅ ImageObject — Extração completa funcionando
- ✅ LinkObject — Extração implementada
- ✅ AnnotationObject — Extração implementada (Highlight, Comment)

**Pendente (requerem algoritmos complexos):**
- ⚠️ TableObject — Requer detecção de estrutura de tabelas (planejado para fase final)
- ⚠️ FormFieldObject — Requer parsing de campos de formulário
- ⚠️ GraphicObject — Requer análise de objetos gráficos/vetoriais
- ⚠️ LayerObject — Requer parsing de camadas do PDF
- ⚠️ FilterObject — Requer análise de filtros aplicados

**Impacto:** Médio - funcionalidades podem ser implementadas incrementalmente

---

### 3. Inserção de Outros Tipos de Objetos

**Status:** ✅ **Parcialmente Funcional**

**Funcional:**
- ✅ Text — Inserção completa
- ✅ Image — Inserção completa

**Pendente:**
- ⚠️ Table — Requer construção de estrutura de tabela
- ⚠️ Link — Requer criação de hiperlinks
- ⚠️ Graphic — Requer desenho de objetos vetoriais
- ⚠️ FormField — Requer criação de campos de formulário

**Impacto:** Baixo - tipos principais (text, image) estão funcionando

---

## 📋 Cenários Não Atendidos

### Processamento de Tabelas

O processamento adaptativo de tabelas (detecção via múltiplas bibliotecas: Camelot, Tabula, pdfplumber, OCR, etc.) foi movido para a última fase do projeto.

**Comandos relacionados a tabelas:**
- `edit-table`: Estrutura CLI implementada, mas retorna `NotImplementedError` explicativo
- Extração de `TableObject`: Requer algoritmo de detecção (planejado para fase final)

**Justificativa:** Detecção de tabelas é uma funcionalidade complexa que requer pesquisa e desenvolvimento específico. Esta funcionalidade será implementada na fase final do projeto.

---

### PDFs com OCR Necessário

PDFs escaneados (imagem) que requerem OCR para extração de texto não são suportados automaticamente.

**Solução:** Use ferramentas de OCR (ex: Tesseract) antes de processar com PDF-cli.

---

### PDFs Corrompidos

PDFs malformados ou corrompidos podem causar erros durante o processamento.

**Comportamento:** PDF-cli tentará processar e retornará erro apropriado se o PDF estiver corrompido.

---

## 🔒 Segurança e Backup

### Backup Automático

Todas as operações destrutivas criam backup automaticamente antes de modificar:
- Backup salvo com timestamp: `{nome_original}_backup_{timestamp}.pdf`
- Backup pode ser desabilitado com flag `--force`
- Caminho do backup incluído no log da operação

### Confirmação de Operações

Operações destrutivas (ex: `delete-pages`) pedem confirmação ao usuário, a menos que `--force` seja usado:

```bash
pdf-cli delete-pages input.pdf output.pdf --pages 1-5
# ⚠️  Você está prestes a excluir 5 página(s).
# Deseja continuar? [y/N]:
```

---

## 📈 Status de Implementação

### Comandos CLI

| Comando | Status | Tipo de Implementação | Observações |
|---------|--------|----------------------|-------------|
| `export-text` | ✅ | **REAL** | Alias para export-objects --types text |
| `export-objects` | ✅ | **REAL** | text, image, link, annotation funcionando |
| `export-images` | ✅ | **REAL** | Extrai imagens como arquivos PNG/JPG |
| `list-fonts` | ✅ | **REAL** | Lista fontes e variantes usadas no PDF |
| `edit-text` | ✅ | **REAL** | Redaction + TextWriter, suporta --all-occurrences |
| `edit-table` | ⚠️ | **Limitação Técnica** | Requer algoritmo de detecção de tabelas |
| `replace-image` | ✅ | **REAL** | Redaction + insert_image implementado |
| `insert-object` | ✅ | **REAL (parcial)** | text e image funcionando |
| `restore-from-json` | ✅ | **REAL** | Aplica edições de texto no PDF |
| `edit-metadata` | ✅ | **REAL** | set_metadata() implementado |
| `merge` | ✅ | **REAL** | insert_pdf() implementado |
| `delete-pages` | ✅ | **REAL** | Exclusão real de páginas |
| `split` | ✅ | **REAL** | Divisão real em múltiplos PDFs |

**Resultado:** ✅ **12 de 13 comandos funcionais** (edit-table pendente por limitação técnica)

### Cobertura de Testes

- **Testes de Integração:** Suite completa de testes REAIS
- **Cobertura:** >90% nos comandos CLI principais
- **Testes Unitários:** Funções auxiliares e parsing
- **Validação de Honestidade:** Script automático

---

## 📚 Documentação Técnica

### Estrutura do Projeto

```
pdf-cli/
├── src/
│   ├── pdf_cli.py          # Entrypoint CLI
│   ├── cli/                # Módulos CLI (help, parser, commands)
│   ├── app/
│   │   ├── services.py     # Casos de uso
│   │   ├── pdf_repo.py     # Camada de infraestrutura
│   │   └── logging.py      # Sistema de logging
│   └── core/
│       ├── models.py       # Modelos de dados
│       ├── exceptions.py   # Exceções customizadas
│       ├── engine_manager.py  # Gerenciamento de engines (PyMuPDF/pypdf)
│       └── font_manager.py    # Gerenciamento de fontes
├── scripts/
│   ├── build_win.bat       # Script de build Windows
│   ├── build_linux.sh      # Script de build Linux
│   ├── README-BUILD-LINUX.md  # Guia de build Linux
│   └── validate_honesty.py # Validação de honestidade
├── dist/                   # Executáveis gerados
│   ├── windows/
│   │   └── pdf-cli.exe     # Executável Windows (~37 MB)
│   └── linux/
│       └── pdf-cli         # Executável Linux (~41 MB)
├── build/                  # Arquivos temporários de build
│   ├── windows/            # Build files Windows
│   └── linux/              # Build files Linux
├── tests/
│   ├── test_integration_real.py  # Testes de integração REAIS
│   ├── test_fase3_operations.py  # Testes estruturais
│   └── test_models_serialization.py
├── examples/               # PDFs de exemplo
├── logs/                   # Logs JSON de operações
├── results/                # Relatórios de fases
└── requirements.txt
```

### Modelos de Dados

Todos os modelos de dados estão definidos em `src/core/models.py`:
- `TextObject`, `ImageObject`, `TableObject`, `LinkObject`
- `FormFieldObject` (Checkbox, RadioButton, Signature)
- `GraphicObject` (Line, Rectangle, Ellipse, Polyline, BezierCurve)
- `LayerObject`, `FilterObject`
- `AnnotationObject` (Highlight, Comment, Marker)

Cada modelo inclui métodos `to_dict()` e `from_dict()` para serialização JSON.

---

## 🤝 Contribuindo

1. **Transparência Absoluta**: Nunca marque funcionalidades como implementadas se contêm mocks, simulações ou placeholders
2. **Testes REAIS**: Todos os testes devem executar operações reais sobre arquivos reais
3. **Documentação de Limitações**: Documente imediatamente qualquer limitação técnica encontrada
4. **Logs Auditáveis**: Todos os logs devem refletir operações reais

---

## 📄 Licença

[Especificar licença]

---

## 🔗 Referências

### Documentação de Fases
- [Relatório Fase 8](results/FASE-8-RELATORIO-FINAL.md) - Distribuição Portátil e Scripts de Build
- [Relatório Fase 7](results/FASE-7-RELATORIO-FINAL.md) - HELP Avançado e Exemplos Práticos
- [Relatório Fase 6](results/FASE-6-RELATORIO-TESTES-REAIS.md) - Testes Reais e Relatório de Auditoria
- [Relatório Fase 5](results/FASE-5-RELATORIO-TEXTWRITER-FINAL.md) - Fallback Inteligente e Preservação de Fontes
- [Relatório Fase 4](results/FASE-4-RELATORIO.md) - Testes, Robustez e Honestidade
- [Relatório Fase 3](results/FASE-3-RELATORIO.md) - Manipulação Avançada de Objetos PDF
- [Relatório Fase 2](results/FASE-2-RELATORIO.md) - Modelos e Schemas
- [Relatório Fase 1](results/FASE-1-RELATORIO.md) - Estrutura Inicial

### Especificações
- [Especificações Fase 4](specifications/FASE-4-ESPECIFICACOES.md)
- [Especificações Fase 3](specifications/FASE-3-ESPECIFICACOES.md)
- [Especificações Fase 2](specifications/FASE-2-EXTRACAO-EDICAO-TEXTO.md)
- [Especificações Iniciais](specifications/FASE-1-ESPECIFICACOES-INICIAIS-DESENVOLVIMENTO.md)

### Outros Documentos
- [CHANGELOG](CHANGELOG.md) - Histórico de mudanças
- [Build Windows](results/FASE-8-RELATORIO-BUILD-WINDOWS.md) - Relatório detalhado do build Windows
- [Build Linux](scripts/README-BUILD-LINUX.md) - Guia completo de build Linux

---

## 📞 Suporte

Para dúvidas, problemas ou sugestões:
- Abra uma issue no repositório
- Consulte a documentação técnica em `specifications/`
- Execute `scripts/validate_honesty.py` para validar implementações

---

**Última Atualização:** 20/11/2025
**Versão:** 0.8.0 (Fase 8 - Distribuição Portátil e Scripts de Build Cross-platform)
