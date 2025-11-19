# RELATÓRIO DE CORREÇÕES REALIZADAS - PDF-cli

**Data:** 2025-11-19
**Última Atualização:** 2025-11-19
**Versão:** 0.4.0 (Fase 4)
**Responsável:** Equipe de Desenvolvimento

---

## SUMÁRIO EXECUTIVO

Este relatório documenta todas as correções realizadas no projeto PDF-cli após a identificação de problemas críticos durante testes manuais. As correções incluem:

1. ✅ **Correção de substituição parcial de texto** - Texto completo preservado ao substituir substring
2. ✅ **Implementação do parâmetro `--all-occurrences`** - Substituição de todas as ocorrências em uma única execução
3. ✅ **Correção de lock de arquivo no Windows** - Refatoração seguindo princípio DRY
4. ✅ **Melhoria de feedback detalhado do CLI** - Informações completas sobre cada ocorrência processada
5. ⚠️ **Melhoria na preservação de fontes** - Mapeamento de fontes com fallback inteligente
6. 📋 **Documentação e testes** - Validação completa das correções

---

## 1. PROBLEMAS IDENTIFICADOS

### 1.1. Problema: Texto Incompleto Após Substituição

**Descrição:**
Ao substituir a substring "ALCANTARA" dentro do texto completo "LUIZ EDUARDO ALVES DE ALCANTARA", o sistema estava substituindo o texto inteiro por apenas "ALCÂNTARA", perdendo o resto do conteúdo.

**Causa Raiz:**
A lógica de substituição não distinguia entre substituição parcial (quando `search_term` é uma substring) e substituição completa. O código sempre substituía o conteúdo completo do objeto por `new_content`.

**Impacto:**
- ❌ Perda de dados importantes no PDF
- ❌ Resultados incorretos e não reversíveis sem backup
- ❌ Experiência do usuário prejudicada

**Arquivo Afetado:**
- `src/app/services.py` (função `edit_text`, linhas 220-243)

---

### 1.2. Problema: Necessidade de Múltiplas Execuções

**Descrição:**
Para substituir todas as ocorrências de um texto no PDF, era necessário executar o comando múltiplas vezes, uma para cada ocorrência.

**Causa Raiz:**
O comando `edit-text` processava apenas a primeira ocorrência encontrada do texto.

**Impacto:**
- ❌ Processo manual e tedioso
- ❌ Alto risco de erro humano
- ❌ Ineficiente para documentos grandes

---

### 1.3. Problema: Fonte Alterada Após Edição

**Descrição:**
Após editar texto, fontes originais (ex: ArialMT, ArialNarrow-Bold) eram substituídas por Helvetica.

**Causa Raiz:**
PyMuPDF não tem acesso a todas as fontes instaladas no sistema. Quando uma fonte não é encontrada, faz fallback para fontes padrão (helv = Helvetica).

**Impacto:**
- ⚠️ Alteração visual do documento
- ⚠️ Inconsistência de formatação
- ⚠️ Dificuldade em manter identidade visual

**Limitação Técnica:**
PyMuPDF não pode acessar fontes TrueType/OpenType do sistema diretamente. A única solução é usar fontes embutidas no PDF ou fontes padrão do PyMuPDF.

---

### 1.4. Problema: Lock de Arquivo no Windows (Permission Denied)

**Descrição:**
Ao usar `--all-occurrences`, o sistema apresentava erro "Permission denied: cannot remove file" ao tentar salvar o PDF modificado.

**Causa Raiz:**
A implementação inicial abria e fechava o documento em cada iteração do loop, causando problemas de lock no Windows. Além disso, o PyMuPDF não permite salvar com `incremental=False` no mesmo arquivo que foi aberto (erro: "save to original must be incremental").

**Impacto:**
- ❌ Falha completa da operação `--all-occurrences`
- ❌ Arquivos temporários não removidos
- ❌ Experiência do usuário comprometida
- ❌ Violação do princípio DRY (reabertura desnecessária do documento)

**Arquivo Afetado:**
- `src/app/services.py` (função `_edit_text_all_occurrences`, linhas 171-286)

---

### 1.5. Problema: Feedback Insuficiente do CLI

**Descrição:**
Ao processar múltiplas ocorrências com `--all-occurrences`, o CLI exibia apenas uma mensagem genérica "✓ Todas as ocorrências foram editadas com sucesso!", sem informações detalhadas sobre o que foi modificado.

**Causa Raiz:**
A função `_edit_text_all_occurrences` coletava informações sobre cada ocorrência processada, mas essas informações não eram expostas ao usuário no CLI.

**Impacto:**
- ❌ Usuário não sabia quais objetos foram modificados
- ❌ Impossível verificar coordenadas ou detecção de fallback de fonte
- ❌ Falta de transparência sobre o que foi alterado
- ❌ Dificuldade para debug e auditoria

**Arquivo Afetado:**
- `src/pdf_cli.py` (comando `edit-text`, linhas 194-198)

---

## 2. CORREÇÕES IMPLEMENTADAS

### 2.1. Correção: Substituição Parcial de Texto ✅

**Arquivo:** `src/app/services.py`
**Linhas:** 220-243

**Implementação:**
```python
# Lógica de substituição de conteúdo
if new_content:
    # IMPORTANTE: Se o search_term é uma substring do texto original,
    # substituir APENAS a parte correspondente, preservando o resto do texto
    if search_term and search_term.strip() and search_term in original_content and search_term != original_content:
        # Substituição parcial: preservar o texto original, substituindo apenas a substring encontrada
        target_obj.content = original_content.replace(search_term, new_content, 1)
        final_content = target_obj.content
    else:
        # Substituição completa: substituir todo o conteúdo
        # (quando search_term == original_content ou busca por ID)
        if pad:
            target_obj.content = center_and_pad_text(target_obj, new_content)
        else:
            target_obj.content = new_content
        final_content = target_obj.content
```

**Resultado:**
- ✅ Texto completo preservado: "LUIZ EDUARDO ALVES DE ALCANTARA" → "LUIZ EDUARDO ALVES DE ALCÂNTARA"
- ✅ Substituição apenas da parte correspondente
- ✅ Comportamento correto para substituição completa (quando necessário)

**Teste:**
```bash
.\pdf.bat edit-text examples/boleto.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --force
```

**Resultado do Teste:**
- ✅ Texto original: "LUIZ EDUARDO ALVES DE ALCANTARA"
- ✅ Texto resultante: "LUIZ EDUARDO ALVES DE ALCÂNTARA"
- ✅ Texto completo preservado

---

### 2.2. Implementação: Parâmetro `--all-occurrences` ✅

**Arquivos Modificados:**
- `src/app/services.py` (nova função `_edit_text_all_occurrences`, linhas 136-280)
- `src/pdf_cli.py` (adicionado parâmetro `--all-occurrences`, linha 162)

**Implementação:**

1. **Nova função `_edit_text_all_occurrences`:**
   - Processa todas as ocorrências do texto em loop
   - Rastreia objetos já processados por ID único
   - Aplica substituição parcial preservando texto completo
   - Mantém formatação original (fonte, tamanho, cor, etc.)

2. **Parâmetro CLI:**
   ```python
   all_occurrences: bool = typer.Option(
       False,
       "--all-occurrences",
       help="Substitui todas as ocorrências do texto (apenas com --content)"
   )
   ```

**Uso:**
```bash
.\pdf.bat edit-text input.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences --force
```

**Resultado:**
- ✅ Substitui todas as ocorrências em uma única execução
- ✅ Processa todas as páginas automaticamente
- ✅ Mantém logs detalhados de quantas ocorrências foram processadas
- ✅ Preserva formatação original de cada ocorrência

**Log de Operação:**
```json
{
  "operation_type": "edit-text",
  "parameters": {
    "search_term": "ALCANTARA",
    "new_content": "ALCÂNTARA",
    "all_occurrences": true
  },
  "result": {
    "status": "success",
    "occurrences_processed": 3
  },
  "notes": "Processadas 3 ocorrências do texto 'ALCANTARA'"
}
```

---

### 2.3. Correção: Lock de Arquivo no Windows (DRY) ✅

**Arquivo:** `src/app/services.py`
**Linhas:** 163-315 (função `_edit_text_all_occurrences`)

**Problema Identificado:**
- Loop reabria o documento em cada iteração
- PyMuPDF não permite salvar `incremental=False` no mesmo arquivo aberto
- Locks de arquivo no Windows causavam "Permission denied"

**Implementação (Princípio DRY):**

1. **Uso de Arquivos Temporários:**
   ```python
   # Criar dois arquivos temporários: um para trabalhar e outro para salvar
   working_temp_path  # Arquivo aberto e editado (fechado após uso)
   save_temp_path     # Arquivo onde salva o resultado (incremental=False permitido)
   final_output_path  # Destino final após mover
   ```

2. **Abrir Documento UMA VEZ:**
   ```python
   # Abrir documento UMA VEZ e processar todas as ocorrências
   # Isso evita problemas de lock de arquivo no Windows e é mais eficiente (DRY)
   with PDFRepository(working_temp_path) as repo:
       doc = repo.open()

       # Processar ocorrências em loop até não encontrar mais
       while True:
           # ... processar cada ocorrência sem fechar o documento ...

       # Salvar PDF APENAS UMA VEZ após todas as edições
       doc.save(save_temp_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
       # O context manager fechará o documento automaticamente
   ```

3. **Mover para Destino Final:**
   ```python
   # Mover arquivo temporário para o nome final após fechar o documento
   shutil.move(save_temp_path, final_output_path)
   ```

**Resultado:**
- ✅ Documento aberto apenas uma vez (DRY)
- ✅ Todas as ocorrências processadas em loop sem reabrir
- ✅ Salvamento único no final (mais eficiente)
- ✅ Problema de lock no Windows resolvido
- ✅ Compatível com limitação do PyMuPDF (`incremental=False`)

**Benefícios:**
- Melhor performance (menos I/O)
- Menos risco de locks de arquivo
- Código mais limpo e manutenível (DRY)
- Compatibilidade garantida com Windows

---

### 2.4. Melhoria: Feedback Detalhado do CLI ✅

**Arquivos Modificados:**
- `src/app/services.py` (função `_edit_text_all_occurrences`, linhas 136-315)
- `src/pdf_cli.py` (comando `edit-text`, linhas 176-225)

**Problema Identificado:**
- Feedback genérico não informava detalhes das modificações
- Usuário não sabia quais objetos, coordenadas ou fontes foram alteradas
- Impossível identificar fallbacks de fonte durante o processamento

**Implementação:**

1. **Coleta de Detalhes por Ocorrência:**
   ```python
   occurrence_details = {
       "id": target_obj.id,
       "page": target_obj.page,
       "coordinates": {
           "x": round(target_obj.x, 2),
           "y": round(target_obj.y, 2),
           "width": round(target_obj.width, 2),
           "height": round(target_obj.height, 2)
       },
       "original_content": original_content,
       "new_content": final_content,
       "font_original": final_font,
       "font_used": fontname_to_use,
       "font_fallback": font_fallback_occurred,
       "font_source": font_used_source,
       "font_size": final_font_size,
       "substitution_type": "parcial" ou "completa",
       "changes": [lista de mudanças]
   }
   ```

2. **Retorno de Detalhes:**
   ```python
   # Função retorna tupla: (caminho_arquivo, lista_de_detalhes)
   return output_path, occurrences_details
   ```

3. **Exibição Formatada no CLI:**
   ```python
   # Para cada ocorrência, exibe:
   ┌─ Ocorrência 1/3
   │ ID: 0ff545bf-88f3-4197-b961-17fe22f88f94
   │ Página: 0  |  Posição: (96.0, 95.2)  |  Tamanho: 131.9×7.8
   │ Modificado: 'LUIZ EDUARDO ALVES DE ALCANTARA' → 'LUIZ EDUARDO ALVES DE ALCÂNTARA'
   │ Fonte original: ArialMT (6pt)
   │ ⚠ Fonte usada: Helvetica (mapeada (ArialMT → helv))
   └─
   ```

**Resultado:**
- ✅ ID completo de cada objeto modificado
- ✅ Página e coordenadas (X, Y) exibidas
- ✅ Tamanho do objeto (largura × altura)
- ✅ Conteúdo antes e depois da modificação
- ✅ Fonte original e fonte usada
- ✅ Indicação visual de fallback de fonte (⚠️ quando ocorre)
- ✅ Lista de todas as mudanças aplicadas
- ✅ Contador de progresso (ex: Ocorrência 1/3)

**Exemplo de Saída:**
```
Processando 3 ocorrência(s)...

┌─ Ocorrência 1/3
│ ID: 0ff545bf-88f3-4197-b961-17fe22f88f94
│ Página: 0  |  Posição: (96.0, 95.2)  |  Tamanho: 131.9×7.8
│ Modificado: 'LUIZ EDUARDO ALVES DE ALCANTARA' → 'LUIZ EDUARDO ALVES DE ALCÂNTARA'
│ Fonte original: ArialMT (6pt)
│ ⚠ Fonte usada: Helvetica (mapeada (ArialMT → helv))
└─

┌─ Ocorrência 2/3
│ ID: 61810f46-286c-472d-ab3d-b27791918294
│ Página: 0  |  Posição: (82.8, 698.0)  |  Tamanho: 142.9×10.3
│ Modificado: 'LUIZ EDUARDO ALVES DE ALCANTARA' → 'LUIZ EDUARDO ALVES DE ALCÂNTARA'
│ Fonte original: ArialNarrow-Bold (9pt)
│ ⚠ Fonte usada: Helvetica-Bold (mapeada (ArialNarrow-Bold → hebo))
└─

✓ Total: 3 ocorrência(s) editada(s) com sucesso!
   Arquivo: examples\boleto_editado.pdf
```

**Benefícios:**
- Transparência total sobre o que foi modificado
- Facilita debug e auditoria
- Usuário pode verificar se modificações estão corretas
- Indicação clara de quando há fallback de fonte
- Melhor experiência do usuário

---

### 2.5. Melhoria: Preservação de Fontes ⚠️

**Arquivo:** `src/app/services.py`
**Linhas:** 307-366 (função `edit_text`) e 233-280 (função `_edit_text_all_occurrences`)

**Implementação:**

1. **Mapeamento de Fontes:**
   ```python
   font_mapping = {
       "ArialMT": "helv",           # Helvetica (padrão sans-serif)
       "Arial": "helv",
       "ArialNarrow": "helv",
       "ArialNarrow-Bold": "hebo",  # Helvetica-Bold
       "Times": "tiro",             # Times-Roman (serif)
       "Times-Roman": "tiro",
       "Courier": "cour",           # Courier (monospace)
   }
   ```

2. **Lógica de Fallback:**
   - Primeiro: Tenta usar fonte mapeada
   - Segundo: Tenta usar fonte original (se PyMuPDF suportar)
   - Terceiro: Fallback para Helvetica (helv)
   - Especial: Detecta fontes "bold" e usa Helvetica-Bold (hebo) quando apropriado

**Resultado:**
- ⚠️ Tamanho da fonte preservado (ex: 6pt, 9pt)
- ⚠️ Estilo bold detectado e aplicado quando possível
- ⚠️ Fonte muda para similar padrão (ex: ArialMT → Helvetica)
- ⚠️ **Limitação:** PyMuPDF não pode acessar fontes do sistema diretamente

**Pesquisa Realizada:**
Após pesquisa na documentação oficial e fóruns do PyMuPDF, foi confirmado que:
- PyMuPDF não tem acesso a fontes TrueType/OpenType do sistema
- Única alternativa: fontes embutidas no PDF ou fontes padrão (helv, tiro, cour, etc.)
- Para preservar 100% a fonte original, seria necessário usar outra biblioteca (ex: ReportLab, Aspose.PDF) ou embutir as fontes no PDF antes da edição

**Recomendação Técnica:**
- ✅ Mapeamento implementado preserva estilo visual similar
- ⚠️ Para preservação 100% da fonte original, considerar migração para biblioteca que suporte acesso a fontes do sistema (avaliação de trade-offs necessária)

---

## 3. TESTES REALIZADOS

### 3.1. Teste de Substituição Parcial

**Comando:**
```bash
.\pdf.bat edit-text examples/boleto.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --force
```

**Resultado Esperado:**
- Texto original: "LUIZ EDUARDO ALVES DE ALCANTARA"
- Texto resultante: "LUIZ EDUARDO ALVES DE ALCÂNTARA"

**Resultado Obtido:**
- ✅ Texto completo preservado
- ✅ Apenas substring "ALCANTARA" substituída por "ALCÂNTARA"

### 3.2. Teste de `--all-occurrences`

**Comando:**
```bash
.\pdf.bat edit-text examples/boleto.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences --force
```

**Resultado Esperado:**
- Todas as 3 ocorrências substituídas em uma única execução

**Resultado Obtido:**
- ✅ Log indica "occurrences_processed: 3"
- ✅ Todas as ocorrências processadas corretamente
- ✅ Sem erros de lock de arquivo

### 3.3. Teste de Correção de Lock de Arquivo

**Comando:**
```bash
.\pdf.bat edit-text examples/boleto.pdf examples/boleto_editado_final.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences
```

**Resultado Esperado:**
- Sem erros de "Permission denied"
- Arquivo criado com sucesso
- Todas as ocorrências substituídas

**Resultado Obtido:**
- ✅ Comando executado com sucesso
- ✅ Arquivo criado sem erros de lock
- ✅ Todas as 3 ocorrências processadas
- ✅ Mensagem: "✓ Todas as ocorrências foram editadas com sucesso!"

### 3.4. Teste de Preservação de Fonte

**Resultado:**
- ⚠️ Tamanho preservado (6pt, 9pt)
- ⚠️ Estilo bold preservado quando possível
- ⚠️ Fonte muda para similar (ArialMT → Helvetica)

### 3.5. Teste de Feedback Detalhado do CLI

**Comando:**
```bash
.\pdf.bat edit-text examples/boleto.pdf examples/boleto_editado.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences
```

**Resultado Esperado:**
- Feedback detalhado para cada ocorrência processada
- Informações sobre ID, coordenadas, conteúdo e fonte

**Resultado Obtido:**
- ✅ Exibição formatada de cada ocorrência (1/3, 2/3, 3/3)
- ✅ ID completo de cada objeto modificado
- ✅ Página e coordenadas (X, Y, W, H) exibidas
- ✅ Conteúdo antes e depois mostrado claramente
- ✅ Fonte original e fonte usada exibidas
- ✅ Indicação visual de fallback (⚠️) quando ocorre
- ✅ Formatação visual com caixas (┌─ └─) para melhor legibilidade

---

## 4. LIMITAÇÕES CONHECIDAS

### 4.1. Preservação de Fontes

**Limitação:**
PyMuPDF não pode acessar fontes TrueType/OpenType do sistema.

**Impacto:**
Fontes originais (ex: ArialMT) são substituídas por fontes padrão similares (ex: Helvetica).

**Mitigação Implementada:**
- Mapeamento inteligente de fontes
- Preservação de tamanho e estilo (bold)

**Solução Futura (Recomendação):**
- Avaliar migração para biblioteca que suporte acesso a fontes do sistema
- Considerar uso de Aspose.PDF (comercial) ou ReportLab (open-source)
- Alternativa: Implementar sistema de embutimento de fontes no PDF antes da edição

---

## 5. ARQUIVOS MODIFICADOS

### 5.1. `src/app/services.py`

**Mudanças:**
1. Nova função `_edit_text_all_occurrences` (linhas 136-315)
   - Refatoração completa seguindo princípio DRY
   - Uso de arquivos temporários para evitar locks no Windows
   - Processamento em loop sem reabrir documento
   - Salvamento único após todas as edições
2. Modificação da função `edit_text`:
   - Adicionado parâmetro `all_occurrences` (linha 322)
   - Correção da lógica de substituição parcial (linhas 220-243)
   - Melhoria no mapeamento de fontes (linhas 307-366)

### 5.2. `src/pdf_cli.py`

**Mudanças:**
1. Adicionado parâmetro `--all-occurrences` ao comando `edit-text` (linha 162)
2. Atualizada documentação do comando com exemplo de uso (linhas 170-172)
3. Implementado feedback detalhado para `--all-occurrences` (linhas 194-225)
   - Exibição formatada de cada ocorrência processada
   - Informações sobre ID, coordenadas, conteúdo modificado
   - Indicação visual de fallback de fonte
   - Formatação visual com caixas (┌─ └─) para melhor legibilidade

---

## 6. DOCUMENTAÇÃO ATUALIZADA

### 6.1. Help do CLI

O comando `edit-text` agora exibe:
```
--all-occurrences    Substitui todas as ocorrências do texto (apenas com --content)

Exemplo:
    pdf-cli edit-text input.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences
```

### 6.2. Logs de Operação

Os logs agora incluem:
- Campo `all_occurrences: true` quando aplicável
- Campo `occurrences_processed` com contagem de ocorrências
- Campo `occurrences_details` com lista completa de detalhes de cada ocorrência
- Campo `notes` com resumo da operação

### 6.3. Feedback Detalhado no CLI

Quando `--all-occurrences` é usado, o CLI agora exibe:

**Para cada ocorrência:**
- Número da ocorrência (ex: 1/3, 2/3)
- ID completo do objeto modificado
- Página onde está localizado
- Coordenadas (posição X, Y e tamanho W × H)
- Conteúdo original e novo conteúdo
- Fonte original (nome e tamanho)
- Fonte usada e indicação se houve fallback
- Mudanças adicionais (fonte, tamanho, cor, alinhamento)

**Indicadores visuais:**
- ✅ (verde) quando fonte original foi preservada
- ⚠️ (amarelo) quando houve fallback de fonte
- Formatação com caixas (┌─ └─) para melhor organização visual

---

## 7. CONCLUSÃO

### 7.1. Correções Completas ✅

1. ✅ **Substituição parcial de texto** - Implementada e testada
2. ✅ **Parâmetro `--all-occurrences`** - Implementado e funcional
3. ✅ **Correção de lock de arquivo no Windows** - Refatoração DRY implementada e testada
4. ✅ **Feedback detalhado do CLI** - Implementado e testado

### 7.2. Melhorias Parciais ⚠️

1. ⚠️ **Preservação de fontes** - Melhorada com mapeamento, mas limitada pela biblioteca PyMuPDF

### 7.3. Próximos Passos Recomendados

1. **Avaliar bibliotecas alternativas** para preservação 100% de fontes:
   - Aspose.PDF (comercial, suporte completo)
   - ReportLab (open-source, suporte parcial)
   - pdfplumber + reportlab (híbrido)

2. **Expandir mapeamento de fontes** com base em uso real:
   - Adicionar mais fontes comuns conforme demanda
   - Permitir configuração customizada de mapeamento

3. **Implementar testes automatizados** para substituição parcial e `--all-occurrences`

4. **Expandir feedback detalhado** para outros comandos:
   - Adicionar feedback similar para `replace-image`
   - Adicionar feedback para `insert-object`
   - Considerar modo verbose global para feedback detalhado

---

## 8. ANEXOS

### 8.1. Comandos de Teste

```bash
# Teste básico de substituição parcial
.\pdf.bat edit-text examples/boleto.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --force

# Teste com --all-occurrences (corrigido - sem lock de arquivo)
.\pdf.bat edit-text examples/boleto.pdf examples/boleto_editado_final.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences

# Teste com preservação de formatação
.\pdf.bat edit-text examples/boleto.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences --font-size 9 --force
```

**Nota:** O comando com `--all-occurrences` agora funciona corretamente no Windows, sem erros de "Permission denied", graças à refatoração DRY que usa arquivos temporários.

### 8.2. Exemplo de Log JSON

```json
{
  "operation_id": "abc123",
  "operation_type": "edit-text",
  "timestamp": "2024-01-15T10:30:00",
  "input_file": "examples/boleto.pdf",
  "output_file": "output.pdf",
  "parameters": {
    "search_term": "ALCANTARA",
    "new_content": "ALCÂNTARA",
    "all_occurrences": true
  },
  "result": {
    "status": "success",
    "occurrences_processed": 3,
    "occurrences_details": [
      {
        "id": "0ff545bf-88f3-4197-b961-17fe22f88f94",
        "page": 0,
        "coordinates": {
          "x": 96.0,
          "y": 95.2,
          "width": 131.9,
          "height": 7.8
        },
        "original_content": "LUIZ EDUARDO ALVES DE ALCANTARA",
        "new_content": "LUIZ EDUARDO ALVES DE ALCÂNTARA",
        "font_original": "ArialMT",
        "font_used": "Helvetica",
        "font_fallback": true,
        "font_source": "mapeada (ArialMT → helv)",
        "font_size": 6,
        "substitution_type": "parcial"
      }
    ]
  },
  "notes": "Processadas 3 ocorrências do texto 'ALCANTARA'"
}
```

### 8.3. Exemplo de Feedback do CLI

**Saída ao executar `--all-occurrences`:**

```
Processando 3 ocorrência(s)...

┌─ Ocorrência 1/3
│ ID: 0ff545bf-88f3-4197-b961-17fe22f88f94
│ Página: 0  |  Posição: (96.0, 95.2)  |  Tamanho: 131.9×7.8
│ Modificado: 'LUIZ EDUARDO ALVES DE ALCANTARA' → 'LUIZ EDUARDO ALVES DE ALCÂNTARA'
│ Fonte original: ArialMT (6pt)
│ ⚠ Fonte usada: Helvetica (mapeada (ArialMT → helv))
└─

┌─ Ocorrência 2/3
│ ID: 61810f46-286c-472d-ab3d-b27791918294
│ Página: 0  |  Posição: (82.8, 698.0)  |  Tamanho: 142.9×10.3
│ Modificado: 'LUIZ EDUARDO ALVES DE ALCANTARA' → 'LUIZ EDUARDO ALVES DE ALCÂNTARA'
│ Fonte original: ArialNarrow-Bold (9pt)
│ ⚠ Fonte usada: Helvetica-Bold (mapeada (ArialNarrow-Bold → hebo))
└─

┌─ Ocorrência 3/3
│ ID: 40259a56-c5f0-405c-ba39-b7c0d1b09feb
│ Página: 1  |  Posição: (56.4, 68.8)  |  Tamanho: 108.1×8.0
│ Modificado: 'LUIZ EDUARDO ALVES DE ALCANTARA' → 'LUIZ EDUARDO ALVES DE ALCÂNTARA'
│ Fonte original: ArialNarrow (6pt)
│ ⚠ Fonte usada: Helvetica (mapeada (ArialNarrow → helv))
└─

✓ Total: 3 ocorrência(s) editada(s) com sucesso!
   Arquivo: examples\boleto_editado.pdf
```

---

**Fim do Relatório**
