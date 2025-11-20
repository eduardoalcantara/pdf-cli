# Implementação: Validação de Entrada/Saída e Confirmação de Fontes Faltantes

**Data**: 19/11/2025
**Status**: ✅ IMPLEMENTADO

---

## 1. FUNCIONALIDADES IMPLEMENTADAS

### 1.1. Validação: Entrada e Saída Não Podem Ser o Mesmo Arquivo ✅

**Problema**: O usuário podia acidentalmente usar o mesmo arquivo como entrada e saída, causando problemas ou perda de dados.

**Solução**: Implementada função `_validate_input_output_paths()` que:
- Resolve caminhos absolutos
- Compara arquivos por caminho normalizado
- Lança exceção clara se forem o mesmo arquivo

**Implementação**:
```python
def _validate_input_output_paths(input_path: str, output_path: str) -> None:
    """
    Valida que os caminhos de entrada e saída não são o mesmo arquivo.

    Raises:
        PDFCliException: Se os caminhos forem iguais (mesmo arquivo)
    """
    from pathlib import Path
    from core.exceptions import PDFCliException

    # Resolver caminhos absolutos e normalizar
    input_abs = Path(input_path).resolve()
    output_abs = Path(output_path).resolve()

    if input_abs == output_abs:
        raise PDFCliException(
            f"Erro: O arquivo de entrada e saída são o mesmo: {input_path}\n"
            f"   Use um nome diferente para o arquivo de saída."
        )
```

**Comandos Protegidos**:
- ✅ `edit-text`
- ✅ `edit-table`
- ✅ `replace-image`
- ✅ `insert-object`
- ✅ `restore-from-json`
- ✅ `edit-metadata`
- ✅ `delete-pages`

**Exemplo de Uso**:
```bash
# ❌ ERRO: Mesmo arquivo
pdf-cli edit-text documento.pdf documento.pdf --content "test" --new-content "TEST"

# ✅ CORRETO: Arquivos diferentes
pdf-cli edit-text documento.pdf documento_editado.pdf --content "test" --new-content "TEST"
```

---

### 1.2. Confirmação: Fontes Faltantes Antes de Gerar PDF ✅

**Problema**: Quando há fontes faltantes, o PDF é gerado sem avisar o usuário, resultando em PDFs com aparência diferente.

**Solução**: Pré-verificação de fontes faltantes ANTES de processar a edição e solicitação de confirmação ao usuário.

**Implementação**:
1. **Pré-verificação** no CLI antes de chamar `_edit_text_all_occurrences`
2. **Exibição** do aviso completo de fontes faltantes
3. **Confirmação** via `typer.confirm()` solicitando ao usuário se deseja continuar
4. **Cancelamento** opcional se usuário não confirmar

**Fluxo**:
```
1. Usuário executa: edit-text com --all-occurrences
2. Sistema pré-verifica fontes que serão usadas
3. Se houver fontes faltantes:
   - Exibe aviso completo (igual ao final)
   - Pergunta: "Deseja continuar assim mesmo e gerar o PDF?"
   - Se NÃO: cancela operação
   - Se SIM: continua processamento
4. Processa edição normalmente
```

**Código Implementado**:
```python
# Pré-verificar fontes faltantes ANTES de processar
preview_font_manager = FontManager()
with PDFRepository(pdf_path) as repo:
    if content:  # Só faz sentido se há busca por conteúdo
        text_objects = repo.extract_text_objects()
        fonts_dict = repo.extract_fonts()
        target_objects = [obj for obj in text_objects if content in obj.content]

        # Verificar fontes que serão usadas
        for obj in target_objects:
            # ... verificação de qualidade de fonte ...
            if match_quality != FontMatchQuality.EXACT:
                preview_font_manager.add_requirement(...)

# Se há fontes faltantes, solicitar confirmação ANTES de processar
if preview_font_manager.has_missing_fonts():
    summary = preview_font_manager.get_missing_fonts_summary()
    print(summary)
    console.print("\n[bold yellow]⚠️ ATENÇÃO:[/bold yellow] O PDF gerado pode ter aparência diferente devido às fontes faltantes.")
    if not typer.confirm("\nDeseja continuar assim mesmo e gerar o PDF?", default=False):
        console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
        raise typer.Abort()
    console.print()
```

**Comportamento**:
- ✅ Aviso aparece ANTES de gerar o PDF
- ✅ Usuário tem chance de cancelar
- ✅ Mensagem clara explica consequências
- ✅ Default é "NÃO" (mais seguro)

**Exemplo de Uso**:
```bash
pdf-cli edit-text documento.pdf saida.pdf --content "test" --new-content "TEST" --all-occurrences

# Sistema detecta fontes faltantes e exibe:
# ================================================================================
# ⚠️  ATENÇÃO: FONTES NÃO ENCONTRADAS NO SISTEMA OPERACIONAL
# ================================================================================
# ...
# ⚠️ ATENÇÃO: O PDF gerado pode ter aparência diferente devido às fontes faltantes.
#
# Deseja continuar assim mesmo e gerar o PDF? [y/N]: _
```

---

## 2. TESTES REALIZADOS

### Teste 1: Validação de Entrada/Saída Igual
```bash
pdf-cli edit-text examples/APIGuide.pdf examples/APIGuide.pdf --content "test" --new-content "TEST"
```
**Resultado**: ✅ Erro exibido corretamente:
```
Erro: O arquivo de entrada e saída são o mesmo: examples/APIGuide.pdf
   Use um nome diferente para o arquivo de saída.
```

### Teste 2: Confirmação de Fontes Faltantes
```bash
pdf-cli edit-text examples/APIGuide.pdf saida.pdf --content "Product Documentation" --new-content "TEST" --all-occurrences
```
**Resultado**: ✅ Aviso exibido antes de processar, confirmação solicitada.

---

## 3. ARQUIVOS MODIFICADOS

1. **`src/pdf_cli.py`**
   - Adicionada função `_validate_input_output_paths()`
   - Adicionada validação em todos comandos que criam PDFs
   - Adicionada pré-verificação e confirmação de fontes faltantes em `edit-text` com `--all-occurrences`

---

## 4. SEGURANÇA E USABILIDADE

### Benefícios da Validação de Entrada/Saída:
- ✅ Previne perda acidental de dados
- ✅ Mensagem clara ao usuário
- ✅ Protege todos comandos que modificam PDFs

### Benefícios da Confirmação de Fontes:
- ✅ Usuário é avisado ANTES de gerar PDF com problemas
- ✅ Chance de cancelar operação
- ✅ Mensagem explicativa sobre consequências
- ✅ Default seguro (NÃO)

---

## 5. PRÓXIMOS PASSOS (OPCIONAL)

1. Adicionar flag `--skip-font-check` para pular verificação de fontes
2. Adicionar flag `--auto-continue` para aceitar automaticamente sem confirmação
3. Estender confirmação para outros comandos que usam fontes (insert-object text, etc.)

---

**Status**: ✅ **IMPLEMENTADO E TESTADO**

Todas as funcionalidades solicitadas foram implementadas e testadas com sucesso.

---

**Elaborado por**: Cursor IDE (AI Assistant)
**Data**: 19/11/2025
