# Manual do Usuário - PDF-cli

**Versão:** 0.9.0
**Data:** 20/11/2025
**PDF-cli - Ferramenta CLI para Edição Estrutural de PDFs**

---

## 📋 Índice

1. [Introdução](#introdução)
2. [Instalação](#instalação)
3. [Conceitos Básicos](#conceitos-básicos)
4. [Primeiros Passos](#primeiros-passos)
5. [Comandos de Extração](#comandos-de-extração)
6. [Comandos de Edição](#comandos-de-edição)
7. [Comandos de Manipulação](#comandos-de-manipulação)
8. [Comandos de Conversão](#comandos-de-conversão)
9. [Exemplos Práticos](#exemplos-práticos)
10. [Casos de Uso Comuns](#casos-de-uso-comuns)
11. [Troubleshooting](#troubleshooting)
12. [FAQ - Perguntas Frequentes](#faq---perguntas-frequentes)
13. [Glossário](#glossário)

---

## 🎯 Introdução

### O que é o PDF-cli?

O **PDF-cli** é uma ferramenta de linha de comando (CLI) para edição e manipulação avançada de arquivos PDF. Permite:

- ✅ Extrair textos, imagens e outros objetos de PDFs
- ✅ Editar textos mantendo o layout original
- ✅ Substituir imagens em documentos existentes
- ✅ Unir múltiplos PDFs em um único arquivo
- ✅ Dividir PDFs em múltiplos arquivos
- ✅ Excluir páginas específicas
- ✅ Editar metadados (título, autor, etc.)
- ✅ Listar fontes usadas no documento
- ✅ Converter arquivos Markdown (.md) para PDF

### Para quem é esta ferramenta?

- **Usuários iniciantes** que precisam fazer edições simples em PDFs
- **Desenvolvedores** que precisam automatizar processamento de PDFs
- **Power users** que trabalham com muitos arquivos PDF
- **Administradores** que precisam de ferramentas de linha de comando
- **Pessoas que preferem CLI** ao invés de interfaces gráficas

### Pré-requisitos

- **Windows ou Linux** (executáveis standalone disponíveis)
- **Python 3.8+** (apenas se usar instalação via Python)
- **Conhecimento básico** de linha de comando (CMD, PowerShell, ou Terminal)

---

## 📦 Instalação

### Opção 1: Executável Standalone (Recomendado)

A forma mais fácil de usar o PDF-cli é baixar o executável standalone. Não é necessário instalar Python ou dependências.

#### Windows

1. **Baixe o executável:**
   - Localize o arquivo `pdf-cli.exe` na pasta `dist/windows/`
   - Copie para uma pasta de sua escolha (ex: `C:\Tools\pdf-cli\`)

2. **Adicione ao PATH (opcional):**
   - Para usar `pdf-cli` de qualquer lugar, adicione a pasta ao PATH do Windows
   - Ou crie um alias/shortcut

3. **Teste a instalação:**
   ```cmd
   pdf-cli.exe --version
   pdf-cli.exe --help
   ```

#### Linux

1. **Baixe o executável:**
   ```bash
   # Copie o arquivo pdf-cli de dist/linux/
   cp dist/linux/pdf-cli /usr/local/bin/pdf-cli
   ```

2. **Torne executável:**
   ```bash
   chmod +x /usr/local/bin/pdf-cli
   ```

3. **Teste a instalação:**
   ```bash
   pdf-cli --version
   pdf-cli --help
   ```

### Opção 2: Instalação via Python

Se você já tem Python instalado e prefere usar o código-fonte:

#### Windows

```cmd
# Clone o repositório (ou extraia o código-fonte)
cd pdf-cli

# Instale as dependências
pip install -r requirements.txt

# Execute
python src/pdf_cli.py --help
```

#### Linux

```bash
# Clone o repositório (ou extraia o código-fonte)
cd pdf-cli

# Instale as dependências
pip install -r requirements.txt

# Execute
python3 src/pdf_cli.py --help
```

---

## 📚 Conceitos Básicos

### O que são Objetos em um PDF?

Um arquivo PDF é composto por vários tipos de **objetos**:

- **Texto**: Palavras e frases que você vê no documento
- **Imagens**: Fotos, gráficos, diagramas
- **Links**: Hiperlinks e referências internas
- **Anotações**: Comentários, destaques, notas
- **Tabelas**: Estruturas de dados organizadas
- **Formulários**: Campos preenchíveis

O PDF-cli permite extrair, editar e manipular esses objetos individualmente.

### IDs de Objetos

Cada objeto no PDF tem um **ID único**. Você precisa deste ID para editar um objeto específico.

**Como obter IDs?**
```bash
# Exporte os objetos do PDF
pdf-cli export-objects documento.pdf objetos.json

# Abra o arquivo JSON e encontre o ID do objeto desejado
```

### Caminhos de Arquivos

Sempre use **caminhos completos** ou **caminhos relativos** corretos:

**Windows:**
```
# Caminho absoluto
pdf-cli export-text C:\Documentos\arquivo.pdf saida.json

# Caminho relativo
pdf-cli export-text documentos\arquivo.pdf saida.json
```

**Linux:**
```
# Caminho absoluto
pdf-cli export-text /home/usuario/documentos/arquivo.pdf saida.json

# Caminho relativo
pdf-cli export-text documentos/arquivo.pdf saida.json
```

### Arquivos de Entrada e Saída

- **Entrada**: O arquivo PDF original que você quer modificar
- **Saída**: O novo arquivo PDF que será criado (ou JSON para extrações)

**IMPORTANTE:** O arquivo de entrada e saída devem ser **diferentes**!

---

## 🚀 Primeiros Passos

### Verificar Instalação

Primeiro, vamos verificar se tudo está funcionando:

```bash
# Ver versão
pdf-cli --version

# Ver ajuda geral
pdf-cli --help

# Ver ajuda de um comando específico
pdf-cli export-text --help
```

### Seu Primeiro Comando

Vamos extrair todos os textos de um PDF:

```bash
# 1. Coloque um arquivo PDF na pasta atual
# 2. Execute o comando
pdf-cli export-text documento.pdf textos.json

# 3. Abra o arquivo textos.json para ver os textos extraídos
```

**O que aconteceu?**
- O PDF-cli leu o arquivo `documento.pdf`
- Extraiu todos os textos encontrados
- Salvou os resultados em `textos.json` (formato JSON)

### Estrutura de um Comando

Todos os comandos do PDF-cli seguem este padrão:

```bash
pdf-cli <comando> <arquivo_entrada> [arquivo_saida] [opcoes]
```

**Exemplo:**
```bash
pdf-cli edit-text input.pdf output.pdf --content "Antigo" --new-content "Novo"
```

- `pdf-cli` - Nome da ferramenta
- `edit-text` - Comando a executar
- `input.pdf` - Arquivo de entrada
- `output.pdf` - Arquivo de saída
- `--content "Antigo"` - Opção: texto a buscar
- `--new-content "Novo"` - Opção: texto substituto

---

## 📤 Comandos de Extração

### export-text

Extrai apenas os textos de um PDF para um arquivo JSON.

**Uso Básico:**
```bash
pdf-cli export-text documento.pdf textos.json
```

**Quando Usar:**
- Você quer ver todos os textos do PDF
- Precisa processar os textos em outro programa
- Quer fazer backup do conteúdo textual

**Exemplo Prático:**
```bash
# Extrair textos de um contrato
pdf-cli export-text contrato.pdf contrato_textos.json

# Extrair textos de uma fatura
pdf-cli export-text fatura.pdf fatura_textos.json
```

**Resultado:**
O arquivo JSON contém uma lista de objetos de texto, cada um com:
- ID único
- Conteúdo do texto
- Posição na página (x, y)
- Página onde está
- Fonte e tamanho
- Outros metadados

### export-objects

Extrai objetos de vários tipos (textos, imagens, links, anotações) para JSON.

**Uso Básico:**
```bash
# Extrair todos os tipos de objetos
pdf-cli export-objects documento.pdf objetos.json

# Extrair apenas textos e imagens
pdf-cli export-objects documento.pdf objetos.json --types text,image

# Incluir informações de fontes
pdf-cli export-objects documento.pdf objetos.json --include-fonts
```

**Tipos Disponíveis:**
- `text` - Textos
- `image` - Imagens
- `link` - Links e hiperlinks
- `annotation` - Anotações e comentários

**Quando Usar:**
- Você precisa de informações sobre vários tipos de objetos
- Quer fazer uma análise completa do PDF
- Precisa dos IDs dos objetos para edição posterior

**Exemplo Prático:**
```bash
# Extrair tudo de um relatório
pdf-cli export-objects relatorio.pdf relatorio_completo.json --include-fonts

# Ver apenas imagens e links
pdf-cli export-objects documento.pdf objetos.json --types image,link
```

### export-images

Extrai imagens do PDF como arquivos PNG/JPG separados.

**Uso Básico:**
```bash
# Extrair todas as imagens
pdf-cli export-images documento.pdf --out imagens/

# O comando criará arquivos como:
# imagens/image_1_page_0.png
# imagens/image_2_page_1.jpg
```

**Quando Usar:**
- Você precisa das imagens fora do PDF
- Quer substituir imagens por versões editadas
- Precisa fazer backup das imagens

**Exemplo Prático:**
```bash
# Extrair logotipos de um documento
pdf-cli export-images documento.pdf --out logos/

# Extrair gráficos de um relatório
pdf-cli export-images relatorio.pdf --out graficos/
```

### list-fonts

Lista todas as fontes e variantes usadas no PDF.

**Uso Básico:**
```bash
pdf-cli list-fonts documento.pdf
```

**Quando Usar:**
- Você quer saber quais fontes estão no documento
- Precisa verificar se uma fonte está instalada no sistema
- Está planejando edições e quer garantir compatibilidade de fontes

**Exemplo Prático:**
```bash
# Ver fontes de um documento
pdf-cli list-fonts documento.pdf

# Saída exemplo:
# Fontes encontradas no PDF:
# - ArialMT (usada, embeddada)
# - Helvetica (usada, não embeddada)
# - Times-Roman (usada, embeddada)
```

**Informações Exibidas:**
- Nome da fonte
- Se está embeddada no PDF
- Se está instalada no sistema
- Quantas vezes é usada

---

## ✏️ Comandos de Edição

### edit-text

Edita objetos de texto no PDF, substituindo conteúdo, alterando fonte, cor, tamanho, posição, etc.

#### Edição por ID (Recomendado)

**Passo 1:** Obtenha o ID do objeto
```bash
pdf-cli export-objects documento.pdf objetos.json
```

**Passo 2:** Abra `objetos.json` e encontre o ID do texto que quer editar

**Passo 3:** Edite o texto
```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --id "abc123def456" \
  --new-content "Novo texto"
```

#### Edição por Conteúdo (Busca)

Edita o primeiro texto que contém o termo buscado:

```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --content "Texto Antigo" \
  --new-content "Texto Novo"
```

#### Edição de Todas as Ocorrências

Edita todas as ocorrências de um texto:

```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --content "Antigo" \
  --new-content "Novo" \
  --all-occurrences
```

**⚠️ ATENÇÃO:** Use com cuidado! Isso pode alterar muitas partes do documento.

#### Opções de Formatação

**Alterar Fonte:**
```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --id "abc123" \
  --new-content "Título" \
  --font-name "Arial-Bold" \
  --font-size 18
```

**Alterar Cor:**
```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --id "abc123" \
  --new-content "Destaque" \
  --color "#FF0000"
```

**Centralizar Texto:**
```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --id "abc123" \
  --new-content "Centralizado" \
  --align center \
  --pad
```

**Mover Texto:**
```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --id "abc123" \
  --new-content "Texto" \
  --x 100 \
  --y 200
```

#### Feedback Detalhado (Verbose)

Ver informações detalhadas sobre cada modificação:

```bash
pdf-cli edit-text documento.pdf documento_editado.pdf \
  --content "Antigo" \
  --new-content "Novo" \
  --all-occurrences \
  --verbose
```

**Informações Exibidas:**
- ID do objeto modificado
- Coordenadas (x, y)
- Conteúdo antes e depois
- Fonte original e usada
- Se houve fallback de fonte

#### Quando Usar

- Corrigir erros ortográficos
- Atualizar datas e valores
- Mudar nomes e informações pessoais
- Ajustar formatação de textos
- Personalizar documentos

#### Exemplo Prático Completo

**Cenário:** Atualizar nome em um contrato

```bash
# 1. Extrair objetos para encontrar o texto
pdf-cli export-objects contrato.pdf contrato_objetos.json

# 2. Abrir contrato_objetos.json e encontrar o ID do nome
# (Exemplo: ID encontrado: "bd2e4742-1373-4a74-bf58-67ecbe537d5a")

# 3. Editar o texto
pdf-cli edit-text contrato.pdf contrato_atualizado.pdf \
  --id "bd2e4742-1373-4a74-bf58-67ecbe537d5a" \
  --new-content "João Silva" \
  --verbose

# 4. Verificar o resultado abrindo contrato_atualizado.pdf
```

### replace-image

Substitui uma imagem no PDF mantendo a posição original.

**Uso Básico:**
```bash
# 1. Obtenha o ID da imagem
pdf-cli export-objects documento.pdf objetos.json

# 2. Substitua a imagem
pdf-cli replace-image documento.pdf documento_novo.pdf \
  --id "img123" \
  --src nova_imagem.png
```

#### Aplicar Filtros

**Imagem em Escala de Cinza:**
```bash
pdf-cli replace-image documento.pdf documento_novo.pdf \
  --id "img123" \
  --src imagem.png \
  --filter grayscale
```

**Imagem Invertida:**
```bash
pdf-cli replace-image documento.pdf documento_novo.pdf \
  --id "img123" \
  --src imagem.png \
  --filter invert
```

**Quando Usar:**
- Atualizar logotipos
- Substituir fotos antigas
- Corrigir imagens com problemas
- Aplicar efeitos visuais

#### Exemplo Prático

```bash
# Substituir logo antigo por novo
pdf-cli replace-image apresentacao.pdf apresentacao_nova.pdf \
  --id "logo123" \
  --src novo_logo.png
```

### insert-object

Insere novos objetos (texto ou imagem) no PDF.

**Inserir Texto:**
```bash
pdf-cli insert-object documento.pdf documento_novo.pdf \
  --type text \
  --params '{"page":0,"content":"Novo Texto","x":100,"y":200,"font_size":12}'
```

**Inserir Imagem:**
```bash
pdf-cli insert-object documento.pdf documento_novo.pdf \
  --type image \
  --params '{"page":0,"src":"imagem.png","x":50,"y":50,"width":200,"height":150}'
```

**Parâmetros para Texto:**
- `page`: Número da página (começa em 0)
- `content`: Texto a inserir
- `x`, `y`: Coordenadas (em pontos)
- `font_size`: Tamanho da fonte
- `font_name`: Nome da fonte (opcional)
- `color`: Cor em hexadecimal (opcional)

**Parâmetros para Imagem:**
- `page`: Número da página (começa em 0)
- `src`: Caminho do arquivo de imagem
- `x`, `y`: Coordenadas (em pontos)
- `width`, `height`: Dimensões (em pontos)

**Quando Usar:**
- Adicionar marcas d'água
- Inserir assinaturas digitais
- Adicionar texto adicional
- Incluir novos elementos visuais

### edit-metadata

Edita metadados do PDF (título, autor, assunto, palavras-chave).

**Uso Básico:**
```bash
pdf-cli edit-metadata documento.pdf documento_novo.pdf \
  --title "Novo Título" \
  --author "Nome do Autor" \
  --subject "Assunto" \
  --keywords "palavra1, palavra2, palavra3"
```

**Parâmetros Disponíveis:**
- `--title`: Título do documento
- `--author`: Autor
- `--subject`: Assunto
- `--keywords`: Palavras-chave (separadas por vírgula)
- `--creator`: Aplicativo que criou o documento
- `--producer`: Ferramenta que produziu o PDF

**Quando Usar:**
- Organizar biblioteca de PDFs
- Adicionar informações para busca
- Padronizar metadados
- Corrigir informações incorretas

**Exemplo Prático:**
```bash
# Organizar PDFs de artigos
pdf-cli edit-metadata artigo.pdf artigo_organizado.pdf \
  --title "Título do Artigo" \
  --author "João Silva" \
  --subject "Ciência da Computação" \
  --keywords "IA, Machine Learning, PDF"
```

---

## 📄 Comandos de Conversão

### md-to-pdf

Converte arquivos Markdown (`.md`) para PDF, mantendo formatação visual fiel.
Tambem renderiza blocos Mermaid (`mermaid`) como imagens PNG no PDF.

**Uso Básico:**
```bash
pdf-cli md-to-pdf documento.md documento.pdf
```

**Quando Usar:**
- Converter documentação Markdown para PDF
- Gerar relatórios a partir de templates Markdown
- Criar PDFs a partir de arquivos de texto formatado
- Automatizar geração de documentos

#### Conversão com CSS Customizado

Use um arquivo CSS personalizado para estilizar o PDF:

```bash
pdf-cli md-to-pdf manual.md manual.pdf --css styles/custom.css
```

**Exemplo de CSS customizado:**
```css
@page {
    size: A4;
    margin: 3cm;
}

body {
    font-family: "Times New Roman", serif;
    font-size: 12pt;
}

h1 {
    color: #1a1a1a;
    border-bottom: 3px solid #0066cc;
}
```

#### Informações Detalhadas (Verbose)

Veja informações sobre o processo de conversão:

```bash
pdf-cli md-to-pdf README.md README.pdf --verbose
```

**Informações Exibidas:**
- Arquivo Markdown sendo lido
- Detecção e renderização de diagramas Mermaid (quando houver)
- Conversão Markdown → HTML
- Conversão HTML → PDF
- Biblioteca usada (WeasyPrint ou xhtml2pdf)
- Número de páginas geradas

#### Opções Mermaid

```bash
# Definir tema dos diagramas Mermaid
pdf-cli md-to-pdf arquitetura.md arquitetura.pdf --mermaid-theme dark

# Desabilitar renderização Mermaid
pdf-cli md-to-pdf documento.md documento.pdf --disable-mermaid
```

**Observações:**
- `--mermaid-theme` aceita temas comuns: `default`, `dark`, `forest`, `neutral`
- Se houver bloco Mermaid e nenhum renderer instalado, o comando retorna erro claro
- Renderers detectados automaticamente:
  - `mmdc` no PATH
  - `npx -y @mermaid-js/mermaid-cli`
- Opcional: definir comando customizado pela variável `PDF_CLI_MERMAID_COMMAND`

#### Suporte a Markdown

O comando suporta:
- ✅ **Títulos** (H1-H6)
- ✅ **Texto formatado** (negrito, itálico, código inline)
- ✅ **Listas** (ordenadas e não ordenadas)
- ✅ **Blocos de código** (com syntax highlighting)
- ✅ **Tabelas**
- ✅ **Links** (internos e externos)
- ✅ **Imagens** (locais e remotas, quando disponíveis)
- ✅ **Citações** (blockquote)
- ✅ **Divisores horizontais**
- ✅ **Listas de tarefas** (checkboxes)

#### Imagens

**Imagens Locais:**
- Devem estar no mesmo diretório do arquivo `.md`
- Ou usar caminhos relativos corretos
- Formatos suportados: PNG, JPG, GIF, SVG

**Exemplo:**
```markdown
![Logo](logo.png)
![Gráfico](imagens/grafico.png)
```

**Imagens Remotas:**
- URLs são baixadas automaticamente
- Requer conexão com internet

**Exemplo:**
```markdown
![Logo Online](https://example.com/logo.png)
```

#### CSS Padrão

O PDF gerado usa um CSS padrão profissional que inclui:
- Página A4 com margens de 2cm
- Tipografia clara (DejaVu Sans, Arial fallback)
- Cabeçalhos estilizados com bordas
- Blocos de código com fundo destacado
- Tabelas com bordas e cabeçalhos destacados
- Links clicáveis (quando possível)
- Cores e espaçamentos profissionais

#### Bibliotecas de Conversão

O comando detecta automaticamente a melhor biblioteca disponível:

**WeasyPrint (Preferido):**
- Melhor qualidade de renderização
- Funciona bem no Linux com dependências do sistema
- No Linux: `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0`
- No Windows: Requer GTK instalado (não recomendado)

**xhtml2pdf (Fallback):**
- Portável, funciona em Windows e Linux
- Não requer dependências externas do sistema
- Instalação: `pip install xhtml2pdf`

O comando faz fallback automático se WeasyPrint não estiver disponível.

#### Exemplo Prático Completo

**Cenário:** Converter documentação Markdown para PDF

```bash
# 1. Converter README para PDF
pdf-cli md-to-pdf README.md README.pdf

# 2. Converter com CSS customizado
pdf-cli md-to-pdf manual.md manual.pdf --css styles/manual.css

# 3. Converter com informações detalhadas
pdf-cli md-to-pdf documento.md documento.pdf --verbose
```

#### Limitações

- Markdown avançado (tabelas complexas, notas de rodapé) pode ter suporte limitado
- Imagens muito grandes podem afetar o tamanho do PDF
- Links para seções do documento podem não funcionar
- Algumas extensões Markdown podem não ser suportadas
- Imagens não encontradas geram aviso mas não impedem a conversão

#### Logs

A operação é registrada em `logs/` com:
- Arquivos de entrada e saída
- Número de páginas geradas
- CSS usado (padrão ou customizado)
- Biblioteca de conversão utilizada
- Erros (se houver)

---

## 🔧 Comandos de Manipulação

### merge

Une múltiplos PDFs em um único arquivo.

**Uso Básico:**
```bash
pdf-cli merge arquivo1.pdf arquivo2.pdf arquivo3.pdf -o combinado.pdf
```

**Quando Usar:**
- Juntar capítulos de um livro
- Combinar relatórios
- Unir documentos relacionados
- Consolidar múltiplas páginas

**Exemplo Prático:**
```bash
# Juntar capítulos de um livro
pdf-cli merge cap01.pdf cap02.pdf cap03.pdf -o livro_completo.pdf

# Combinar relatórios mensais
pdf-cli merge janeiro.pdf fevereiro.pdf marco.pdf -o trimestre1.pdf
```

**Ordem:** Os PDFs são unidos na ordem em que aparecem no comando.

### split

Divide um PDF em múltiplos arquivos menores.

**Uso Básico:**
```bash
# Dividir em faixas de páginas
pdf-cli split documento.pdf --ranges "1-3,4-6,7-10" --out parte_

# Resultado:
# parte_1.pdf (páginas 1-3)
# parte_2.pdf (páginas 4-6)
# parte_3.pdf (páginas 7-10)
```

**Sintaxe de Ranges:**
- `1-3`: Páginas 1, 2 e 3
- `4,6,8`: Páginas 4, 6 e 8
- `10-`: Do início até a página 10
- `-10`: Da página 10 até o fim

**Quando Usar:**
- Dividir documentos grandes
- Extrair capítulos específicos
- Separar seções de um relatório
- Criar versões resumidas

**Exemplo Prático:**
```bash
# Dividir livro em capítulos (3 páginas cada)
pdf-cli split livro.pdf --ranges "1-3,4-6,7-9,10-12" --out cap_

# Dividir relatório em seções
pdf-cli split relatorio.pdf --ranges "1-5,6-10,11-15" --out secao_
```

### delete-pages

Exclui páginas específicas de um PDF.

**Uso Básico:**
```bash
# Excluir páginas específicas (com confirmação)
pdf-cli delete-pages documento.pdf documento_novo.pdf --pages "1,3,5"

# Excluir faixa de páginas
pdf-cli delete-pages documento.pdf documento_novo.pdf --pages "5-10"

# Sem confirmação (--force)
pdf-cli delete-pages documento.pdf documento_novo.pdf --pages "1-5" --force
```

**⚠️ ATENÇÃO:** Por padrão, o comando pede confirmação antes de excluir. Use `--force` para pular a confirmação (cuidado!).

**Quando Usar:**
- Remover páginas desnecessárias
- Eliminar páginas em branco
- Remover seções obsoletas
- Criar versões resumidas

**Exemplo Prático:**
```bash
# Remover página de capa antiga
pdf-cli delete-pages documento.pdf documento_novo.pdf --pages "1"

# Remover páginas intermediárias
pdf-cli delete-pages documento.pdf documento_novo.pdf --pages "5-7"
```

### restore-from-json

Restaura/edita um PDF a partir de um arquivo JSON com alterações.

**Uso Básico:**
```bash
# 1. Exporte os objetos para JSON
pdf-cli export-objects documento.pdf objetos.json

# 2. Edite o arquivo JSON manualmente (altere textos, posições, etc.)

# 3. Restaure o PDF com as alterações
pdf-cli restore-from-json documento.pdf objetos.json documento_novo.pdf
```

**Quando Usar:**
- Fazer edições em lote via script
- Automatizar modificações complexas
- Processar múltiplos documentos
- Integrar com outros sistemas

**⚠️ AVANÇADO:** Requer conhecimento de estrutura JSON dos objetos.

---

## 💡 Exemplos Práticos

### Exemplo 1: Corrigir Nome em um Contrato

**Cenário:** Você precisa atualizar o nome "João" para "José" em um contrato.

**Solução:**
```bash
# 1. Extrair objetos
pdf-cli export-objects contrato.pdf contrato_objetos.json

# 2. Abrir contrato_objetos.json e encontrar o ID do nome
# (Procure por "João" no arquivo JSON)

# 3. Editar o texto
pdf-cli edit-text contrato.pdf contrato_atualizado.pdf \
  --id "ID_ENCONTRADO" \
  --new-content "José" \
  --verbose

# 4. Verificar o resultado
```

### Exemplo 2: Substituir Todas as Ocorrências de um Texto

**Cenário:** Atualizar o nome da empresa em todo o documento.

**Solução:**
```bash
# Substituir todas as ocorrências
pdf-cli edit-text documento.pdf documento_novo.pdf \
  --content "Empresa Antiga LTDA" \
  --new-content "Empresa Nova LTDA" \
  --all-occurrences \
  --verbose
```

**⚠️ CUIDADO:** Use `--verbose` para ver todas as alterações antes de confirmar.

### Exemplo 3: Juntar Relatórios Mensais

**Cenário:** Você tem relatórios mensais e quer juntá-los em um trimestral.

**Solução:**
```bash
# Juntar 3 relatórios
pdf-cli merge janeiro.pdf fevereiro.pdf marco.pdf -o trimestre1.pdf
```

### Exemplo 4: Dividir Livro em Capítulos

**Cenário:** Você tem um livro de 100 páginas e quer dividir em capítulos de 10 páginas.

**Solução:**
```bash
# Dividir em capítulos
pdf-cli split livro.pdf \
  --ranges "1-10,11-20,21-30,31-40,41-50,51-60,61-70,71-80,81-90,91-100" \
  --out cap_
```

### Exemplo 5: Remover Página de Capa Antiga

**Cenário:** Você quer remover a primeira página (capa antiga) de um documento.

**Solução:**
```bash
# Remover primeira página
pdf-cli delete-pages documento.pdf documento_novo.pdf --pages "1"
```

### Exemplo 6: Extrair Todas as Imagens

**Cenário:** Você precisa extrair todas as imagens de um PDF para editá-las.

**Solução:**
```bash
# Extrair imagens
pdf-cli export-images documento.pdf --out imagens/

# Editar as imagens manualmente (ex: no Photoshop, GIMP, etc.)

# Depois, substituir no PDF usando replace-image
```

### Exemplo 7: Converter Documentação Markdown para PDF

**Cenário:** Você tem documentação em Markdown e precisa gerar PDFs para distribuição.

**Solução:**
```bash
# Converter README para PDF
pdf-cli md-to-pdf README.md README.pdf

# Converter manual com CSS customizado
pdf-cli md-to-pdf MANUAL.md MANUAL.pdf --css styles/manual.css

# Converter com informações detalhadas
pdf-cli md-to-pdf documento.md documento.pdf --verbose
```

### Exemplo 8: Atualizar Metadados para Organização

**Cenário:** Você tem vários PDFs de artigos e quer organizá-los com metadados corretos.

**Solução:**
```bash
# Atualizar metadados de cada artigo
pdf-cli edit-metadata artigo1.pdf artigo1_org.pdf \
  --title "Título do Artigo 1" \
  --author "Autor" \
  --subject "Ciência" \
  --keywords "pesquisa, estudo, ciência"

pdf-cli edit-metadata artigo2.pdf artigo2_org.pdf \
  --title "Título do Artigo 2" \
  --author "Autor" \
  --subject "Ciência" \
  --keywords "pesquisa, estudo, ciência"

# Agora os PDFs estão organizados e podem ser encontrados por busca
```

---

## 🎯 Casos de Uso Comuns

### Caso 1: Processamento em Lote

**Cenário:** Você tem 100 PDFs e precisa substituir o mesmo texto em todos.

**Solução com Script (Windows - batch):**
```batch
@echo off
for %%f in (*.pdf) do (
    pdf-cli.exe edit-text "%%f" "editados\%%f" --content "Antigo" --new-content "Novo" --force
)
```

**Solução com Script (Linux - bash):**
```bash
#!/bin/bash
for file in *.pdf; do
    pdf-cli edit-text "$file" "editados/$file" \
      --content "Antigo" \
      --new-content "Novo" \
      --force
done
```

### Caso 2: Backup de Conteúdo

**Cenário:** Você quer fazer backup do conteúdo textual de vários PDFs.

**Solução:**
```bash
# Criar script para exportar textos de todos os PDFs
for file in *.pdf; do
    pdf-cli export-text "$file" "backup/${file%.pdf}.json"
done
```

### Caso 3: Validação de Fontes

**Cenário:** Antes de editar um PDF, você quer verificar se as fontes necessárias estão disponíveis.

**Solução:**
```bash
# Listar fontes
pdf-cli list-fonts documento.pdf

# Se aparecer aviso sobre fontes faltantes, instale-as antes de editar
```

### Caso 4: Extração de Dados

**Cenário:** Você precisa extrair informações de faturas/boletos em formato estruturado.

**Solução:**
```bash
# 1. Extrair objetos
pdf-cli export-objects fatura.pdf fatura.json

# 2. Processar o JSON com um script Python/Node.js/etc.
# para extrair valores, datas, etc.
```

---

## 🔧 Troubleshooting

### Problema: "Arquivo não encontrado"

**Causa:** Caminho do arquivo incorreto ou arquivo não existe.

**Solução:**
- Verifique se o caminho está correto
- Use caminho absoluto se necessário
- Verifique se o arquivo realmente existe

```bash
# Windows
pdf-cli export-text "C:\Documentos\arquivo.pdf" saida.json

# Linux
pdf-cli export-text "/home/usuario/documentos/arquivo.pdf" saida.json
```

### Problema: "Permission denied" (Linux)

**Causa:** Sem permissão de leitura/escrita.

**Solução:**
```bash
# Dar permissão de execução ao pdf-cli
chmod +x pdf-cli

# Dar permissão de leitura ao PDF
chmod +r documento.pdf

# Dar permissão de escrita na pasta de saída
chmod +w pasta_saida/
```

### Problema: "Fontes faltantes detectadas"

**Causa:** Uma ou mais fontes usadas no PDF não estão instaladas no sistema.

**Solução:**
1. Execute `pdf-cli list-fonts documento.pdf` para ver quais fontes faltam
2. Instale as fontes necessárias no sistema operacional
3. Tente editar novamente

**Windows:** Copie os arquivos de fonte (.ttf) para `C:\Windows\Fonts\`
**Linux:** Copie para `~/.fonts/` ou `/usr/share/fonts/`

### Problema: Fonte alterada após edição

**Causa:** A fonte original não está disponível, então o sistema usou uma similar.

**Solução:**
- Instale a fonte original no sistema
- Ou aceite a fonte similar (layout pode mudar ligeiramente)

### Problema: "Arquivo de entrada e saída são iguais"

**Causa:** Você especificou o mesmo arquivo para entrada e saída.

**Solução:**
Use nomes diferentes:
```bash
# ERRADO
pdf-cli edit-text documento.pdf documento.pdf --content "A" --new-content "B"

# CORRETO
pdf-cli edit-text documento.pdf documento_editado.pdf --content "A" --new-content "B"
```

### Problema: Texto não foi encontrado

**Causa:** O texto buscado não existe ou está escrito diferente (maiúsculas/minúsculas, espaços, etc.).

**Solução:**
- Verifique o texto exato usando `export-text`
- Busque por parte do texto
- Verifique espaços e caracteres especiais

### Problema: PDF corrompido

**Causa:** O arquivo PDF está danificado ou corrompido.

**Solução:**
- Tente abrir o PDF em outro visualizador para confirmar
- Use ferramentas de reparo de PDF
- Solicite uma nova cópia do arquivo

### Problema: Erro ao converter Markdown para PDF

**Causa:** Biblioteca de conversão não disponível ou dependências faltando.

**Solução:**

**Windows:**
- O comando usa `xhtml2pdf` automaticamente (portável)
- Se falhar, instale: `pip install xhtml2pdf`

**Linux:**
- Tenta usar `weasyprint` primeiro (melhor qualidade)
- Se falhar, instale dependências: `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0`
- Ou use `xhtml2pdf` como alternativa: `pip install xhtml2pdf`

### Problema: Imagens não aparecem no PDF

**Causa:** Imagens não encontradas ou caminhos incorretos.

**Solução:**
- Verifique se as imagens estão no mesmo diretório do arquivo `.md`
- Use caminhos relativos corretos
- Verifique se os arquivos de imagem existem
- O comando mostra avisos sobre imagens não encontradas

### Problema: CSS customizado não aplicado

**Causa:** Arquivo CSS não encontrado ou caminho incorreto.

**Solução:**
- Verifique se o caminho do CSS está correto
- Use caminho absoluto se necessário
- Verifique se o arquivo CSS existe e está acessível

### Problema: Comando muito lento

**Causa:** PDF muito grande ou muitos objetos para processar.

**Solução:**
- Aguarde (processamento de PDFs grandes pode demorar)
- Considere dividir o PDF em partes menores
- Use `--force` para pular confirmações e acelerar

---

## ❓ FAQ - Perguntas Frequentes

### Como encontro o ID de um objeto?

1. Execute `pdf-cli export-objects documento.pdf objetos.json`
2. Abra o arquivo `objetos.json` em um editor de texto
3. Procure pelo texto/conteúdo que você quer editar
4. Copie o valor do campo `id`

### Posso editar múltiplos textos de uma vez?

Sim, use `--all-occurrences` para editar todas as ocorrências do mesmo texto. Para textos diferentes, execute o comando múltiplas vezes ou use `restore-from-json`.

### O PDF-cli pode criar PDFs do zero?

Não, o PDF-cli é focado em edição e manipulação de PDFs existentes. Para criar PDFs do zero, use outras ferramentas.

### Posso editar tabelas?

Atualmente não. A edição de tabelas requer detecção complexa da estrutura, que ainda não foi implementada. Esta funcionalidade está planejada para uma fase futura.

### Como converter Markdown para PDF?

Use o comando `md-to-pdf`:

```bash
pdf-cli md-to-pdf documento.md documento.pdf
```

O comando suporta CSS customizado e funciona em Windows e Linux. Veja a seção [Comandos de Conversão](#comandos-de-conversão) para mais detalhes.

### Qual biblioteca é usada para converter Markdown?

O comando detecta automaticamente:
- **WeasyPrint** (preferido, melhor qualidade) - funciona no Linux
- **xhtml2pdf** (fallback, portável) - funciona em Windows e Linux

O fallback é automático se WeasyPrint não estiver disponível.

### O que fazer se a fonte mudar após edição?

Instale a fonte original no sistema operacional. Se não for possível, a ferramenta usará uma fonte similar, mas o layout pode mudar ligeiramente.

### Posso usar o PDF-cli em scripts automatizados?

Sim! O PDF-cli é perfeito para automação. Use `--force` para evitar confirmações interativas.

### Os arquivos originais são modificados?

Não. O PDF-cli sempre cria um novo arquivo. O arquivo original permanece inalterado (a menos que você o substitua manualmente).

### Como faço backup antes de editar?

O PDF-cli não cria backup automático dos arquivos originais. Sempre mantenha uma cópia do arquivo original:

```bash
# Fazer backup manual
cp documento.pdf documento_backup.pdf

# Depois editar
pdf-cli edit-text documento.pdf documento_novo.pdf ...
```

### Posso usar caminhos relativos?

Sim, mas certifique-se de estar no diretório correto ou use caminhos relativos corretos.

```bash
# Estar na pasta correta
cd C:\Documentos
pdf-cli export-text arquivo.pdf saida.json

# Ou usar caminho relativo
pdf-cli export-text Documentos\arquivo.pdf saida.json
```

### O PDF-cli funciona com PDFs protegidos por senha?

Atualmente não. PDFs protegidos por senha precisam ser desbloqueados antes de usar o PDF-cli.

### Posso editar PDFs escaneados (imagem)?

PDFs escaneados são imagens, não textos editáveis. Você precisa usar OCR (Optical Character Recognition) primeiro para converter em texto editável.

---

## 📖 Glossário

- **CLI**: Command Line Interface - Interface de Linha de Comando
- **ID**: Identificador único de um objeto no PDF
- **Embedded Font**: Fonte que está incluída dentro do PDF
- **Fallback**: Quando uma fonte não está disponível, usar uma similar
- **Metadata**: Informações sobre o documento (título, autor, etc.)
- **Object**: Elemento do PDF (texto, imagem, link, etc.)
- **Page**: Página do documento PDF
- **Point**: Unidade de medida usada em PDFs (72 points = 1 polegada)
- **JSON**: JavaScript Object Notation - Formato de dados estruturado
- **OCR**: Optical Character Recognition - Reconhecimento óptico de caracteres

---

## 📞 Suporte

### Obtendo Ajuda

**Ajuda Geral:**
```bash
pdf-cli --help
```

**Ajuda de Comando Específico:**
```bash
pdf-cli <comando> --help
```

**Exemplos:**
```bash
pdf-cli edit-text --help
pdf-cli export-objects --help
```

### Recursos Adicionais

- **README.md**: Documentação técnica completa
- **CHANGELOG.md**: Histórico de mudanças e versões
- **Relatórios de Fases**: Documentação detalhada de cada fase de desenvolvimento
- **Especificações**: Documentação técnica avançada

### Reportando Problemas

Se encontrar um problema:

1. Verifique esta seção de Troubleshooting
2. Verifique a FAQ
3. Consulte a documentação técnica (README.md)
4. Abra uma issue no repositório (se for open source)
5. Inclua informações sobre:
   - Versão do PDF-cli (`pdf-cli --version`)
   - Sistema operacional
   - Comando que causou o erro
   - Mensagem de erro completa

---

## ✅ Conclusão

Este manual cobre todas as funcionalidades principais do PDF-cli. Para informações mais avançadas, consulte a documentação técnica (README.md) e os relatórios de desenvolvimento.

**Lembre-se:**
- ✅ Sempre faça backup dos arquivos originais
- ✅ Use `--verbose` para entender o que está acontecendo
- ✅ Teste em arquivos de teste antes de processar documentos importantes
- ✅ Leia as mensagens de aviso e confirmação

**Boa sorte e bom uso!** 🚀

---

**Última Atualização:** 20/11/2025
**Versão do Manual:** 1.1
**Versão do PDF-cli:** 0.9.0
