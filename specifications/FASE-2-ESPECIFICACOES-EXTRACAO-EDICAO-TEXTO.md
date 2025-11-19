# ESPECIFICACOES-FASE-2-EXTRACAO-EDICAO-TEXTO.md

## Projeto: PDF-cli
**Fase 2 — Extração e Edição Detalhada de Texto**

---

## Objetivo Geral

Desenvolver operações de extração, busca e substituição avançada de textos nos arquivos PDF, com documentação rigorosa e garantia de rastreabilidade das alterações. Os resultados devem ser reprodutíveis, auditáveis e reversíveis.

---

## Banner do CLI

Ao executar o programa sem parâmetros, exibir obrigatoriamente o banner artístico abaixo seguido do usage/help automático:

```
┏━┓╺┳┓┏━╸  ┏━╸╻  ╻
┣━┛ ┃┃┣╸╺━╸┃  ┃  ┃
╹  ╺┻┛╹    ┗━╸┗━╸╹
2025 ⓒ Eduardo Alcantara
Made With Perplexity & Cursor

Usage:
    pdf.exe [COMMAND] [OPTIONS]
    For help on individual commands: pdf.exe <command> --help
```

Estruture o handler do entrypoint para garantir que o banner seja exibido antes do usage/help em todos cenários previstos (ex: erro, help global).

---

## Funcionalidades Detalhadas

### 1. EXTRAÇÃO DE OBJETOS DE TEXTO PARA JSON

#### Exemplo de uso:
```
pdf.exe export-text input.pdf output.json
```

#### Exemplo de JSON gerado:
```
[
  {
    "id": "bd2e4742-1373-4a74-bf58-67ecbe537d5a",
    "page": 3,
    "content": "Relação de Inscritos",
    "x": 120,
    "y": 80,
    "width": 180,
    "height": 22,
    "font_name": "Times-New-Roman-Bold",
    "font_size": 18,
    "color": "#222222",
    "align": "center"
  },
  {
    "id": "c1640e8c-4ea8-4bc2-87ca-9f33be5ad1e4",
    "page": 3,
    "content": "Inscrito",
    "x": 124,
    "y": 140,
    "width": 60,
    "height": 16,
    "font_name": "Arial",
    "font_size": 14,
    "color": "#444444",
    "align": "left"
  }
]
```

#### Exemplo de teste unitário:
```
def test_extract_text_objects():
    result = extract_text_objects("input.pdf")
    assert result.page == 3
    assert result.content == "Relação de Inscritos"
    assert result.font_name == "Arial"[1]
```

---

### 2. SUBSTITUIÇÃO DE TEXTO, CENTRALIZAÇÃO E PADDING

#### Exemplo CLI:

```
pdf.exe edit-text input.pdf output.pdf "Relação de Inscritos" "Lista Final" --center --pad
```

#### Exemplo de lógica:
- Bloco original: "Relação de Inscritos" (18 chars, largura 180px, centralizado em 120px)
- Substituição: "Lista Final" (11 chars, target centralização: calcula 3 espaços antes e 4 após, mantendo largura original)
- Padding ajusta para bloquear deslocamentos visuais.

#### Exemplo de log editável:
```
{
  "edit_id": "bd2e4742-1373-4a74-bf58-67ecbe537d5a",
  "page": 3,
  "original": "Relação de Inscritos",
  "edited": "   Lista Final    ",
  "options": ["center", "pad"],
  "timestamp": "2025-11-18T13:53:10Z"
}
```

#### Teste unitário:
```
def test_replace_text_center_pad():
    output_pdf = "test-edit.pdf"
    replace_text("input.pdf", output_pdf, "Relação de Inscritos", "Lista Final", options={"center": True, "pad": True})
    objs = extract_text_objects(output_pdf)
    assert "Lista Final" in [obj.content.strip() for obj in objs]
    # valida quantidade de espaços antes/depois, posição, fonte e cor preservadas
```

---

### 3. RECONSTRUÇÃO E LOGGING

#### Exemplo:
```
def test_edit_log_output():
    log_path = "edit-log.json"
    export_edit_log(log_path)
    with open(log_path) as f:
        log = json.load(f)
        assert all(k in log for k in ["edit_id", "original", "edited"])
```

---

### 4. ERROS E EXCEÇÕES

#### Exemplos de erro:
- Texto “Relação de Inscritos” não encontrado → retorna TextNotFoundError, explica como extrair lista de textos via export.
- Padding impossível (texto editado maior que bloco) → retorna PaddingError, recomenda encurtar texto ou alterar fonte.

---

### 5. REGRAS DE IMPLEMENTAÇÃO (Refinadas)

- Use UUID para id de cada objeto de texto.
- Funções subsequentes devem aceitar busca por `"id"` ou `"content"`.
- Caso texto a ser substituído esteja fragmentado, retorne erro claro e oriente solução (ex: export JSON, modifique, reimporte).
- Preserve ao máximo as propriedades visuais do texto original.
- Registrar toda alteração em arquivo de log editável.

---

### 6. CHECKLIST DE ENTREGA

- src/app/services.py: funções completas, exemplos no docstring.
- src/app/pdf_repo.py: infra implementada conforme testes.
- src/core/models.py: modelos validados com exemplo de instância.
- CLI com banner e help.
- Testes em `tests/` com coverage >80%.
- README ampliado com todos exemplos acima.
- Edit-log gerado em cada execução de substituição.

---

**Observação:**
Deve seguir estritamente o planejamento, sem improvisos que desviem de escopo/função.
Todo código deve obedecer ao padrão de qualidade e arquitetura definido nos docs da Fase 1 e `.cursorrules`.

**Dúvidas pontuais devem ser registradas via issue documentada, nunca resolvidas por atalhos temporários.**

[1](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/11382368/3e37b6f9-2a51-4876-ac94-c9b9b306ca58/image.jpg)

Aqui vão exemplos **mais técnicos** para templates de funções, schemas de JSON para diferentes objetos do PDF, exemplos de erros reais, logs detalhados e como devem ser tratados/documentados:

***

---

## 1. Template de Função Python — Extração genérica

```python
from typing import List
from core.models import TextObject, ImageObject

def extract_pdf_objects(pdf_path: str) -> dict:
    """
    Extrai e retorna objetos do PDF: textos e imagens por página.

    Args:
        pdf_path (str): caminho para o PDF de entrada.
    Returns:
        dict: {
            "pages": [
                {
                    "number": 1,
                    "texts": [TextObject, ...],
                    "images": [ImageObject, ...],
                },
                ...
            ]
        }
    Raises:
        PDFMalformedError: se não puder abrir/parsing do PDF.
    Exemplos:
        >>> ret = extract_pdf_objects("input.pdf")
        >>> print(ret['pages'][0]['texts'][0].content)
    """
    pass # Implementação
```

***

## 2. Template de JSON — TextObject e ImageObject

### TextObject (padrão):
```json
{
  "id": "b1a233de-eef2-477c-85de-c234bdc6ab06",
  "page": 2,
  "content": "Prazo final",
  "x": 90.5,
  "y": 110.0,
  "width": 140.2,
  "height": 18.3,
  "font_name": "Arial-Bold",
  "font_size": 14,
  "color": "#0A0A0A",
  "align": "center",
  "rotation": 0
}
```

### ImageObject:
```json
{
  "id": "img-18271c0e-9d04-4edd-abc1-022411da6e16",
  "page": 2,
  "mime_type": "image/png",
  "x": 135.0,
  "y": 220.0,
  "width": 120,
  "height": 64,
  "data_base64": "iVBORw0KGgoAAAANSU...AgAA",
  "caption": "Logo da empresa"
}
```

***

## 3. Template de Log — Edit Operation Log

```json
[
  {
    "edit_id": "b1a233de-eef2-477c-85de-c234bdc6ab06",
    "timestamp": "2025-11-18T14:00:31Z",
    "user": "Cursor",
    "page": 2,
    "object_type": "text",
    "original_content": "Prazo final",
    "new_content": "Entrega encerrada",
    "options": {
      "center": true,
      "pad": false,
      "case_sensitive": true
    },
    "status": "success",
    "notes": "Centralizado, conteúdo menor, padding não necessário"
  },
  {
    "edit_id": "img-18271c0e-9d04-4edd-abc1-022411da6e16",
    "timestamp": "2025-11-18T14:01:15Z",
    "object_type": "image",
    "operation": "deleted",
    "status": "success",
    "notes": "Imagem removida da página 2"
  }
]
```

***

## 4. Exemplos de Erros Reais

### Exemplo: Texto não encontrado
```json
{
    "error": "TextNotFoundError",
    "timestamp": "2025-11-18T14:05:03Z",
    "search": "Documento válido",
    "page": "all",
    "message": "Texto 'Documento válido' não encontrado em nenhuma página.",
    "suggestion": "Use o comando 'export-text' para obter todos os textos presentes."
}
```

### Exemplo: Padding impossível
```json
{
    "error": "PaddingError",
    "timestamp": "2025-11-18T14:07:27Z",
    "edit_id": "b1a233de-eef2-477c-85de-c234bdc6ab06",
    "original_content": "Prazo final",
    "new_content": "Este texto novo ficou maior que o bloco original.",
    "width_original": 140.2,
    "width_new": 178.0,
    "message": "Texto novo ultrapassa largura máxima do bloco.",
    "suggestion": "Reduza o texto ou aumente tamanho do bloco/font."
}
```

***

## 5. Template — Teste unitário para erro

```python
def test_replace_text_not_found():
    with pytest.raises(TextNotFoundError):
        replace_text("input.pdf", "output.pdf", "Termo inexistente", "Qualquer coisa")

def test_replace_text_padding_error():
    with pytest.raises(PaddingError):
        replace_text(
            "input.pdf", "output.pdf",
            "Prazo final",
            "Texto novo que é muito maior que o permitido",
            options={"pad": True}
        )
```

***

## 6. Template — Função para reconstrução de JSON

```python
def from_json_restore_text(pdf_path: str, json_path: str, output_path: str) -> None:
    """
    Reconstrói o texto dos blocos do PDF de acordo com um arquivo JSON de objetos.
    Aplica edição reversível de layout, fontes, cores e posições.
    Exemplo:
        >>> from_json_restore_text("input.pdf", "texto_editado.json", "final.pdf")
    """
    pass # Implementação
```

***

**Esses exemplos servem como padrão mínimo para o programador implementar, testar e entregar com detalhes em logs e documentação. Qualquer ajuste na estrutura dos objetos, mensagens de erro ou testes só deve ser feito por solicitação direta do engenheiro/gestor do projeto.**

---

Segue exemplos **adicionais** para outros tipos de objetos do PDF, como tabelas, hyperlinks, campos de formulário e templates de teste:

***

## 1. JSON — TableObject (Tabela)

```json
{
  "id": "tbl-7cbbdf10-f645-4a6b-89ef-cfdaad4b30c8",
  "page": 5,
  "type": "table",
  "x": 60.0,
  "y": 340.0,
  "width": 400.0,
  "height": 260.0,
  "headers": ["Nome", "Cargo", "Data"],
  "rows": [
    ["Paulo", "Analista", "2025-11-11"],
    ["Ana", "Gerente", "2025-11-12"]
  ],
  "cell_fonts": [
    {"row": 0, "col": 0, "font": "Arial", "size": 12, "color": "#333333"}
  ]
}
```

***

## 2. JSON — LinkObject (Hiperlink)

```json
{
  "id": "lnk-cfee1327-57cd-41cf-b286-621677293219",
  "page": 1,
  "type": "hyperlink",
  "content": "Clique aqui para acessar",
  "x": 490.5,
  "y": 98.0,
  "width": 180,
  "height": 22,
  "font_name": "Arial-Bold",
  "font_size": 12,
  "color": "#0055FF",
  "url": "https://meusite.com/docs"
}
```

***

## 3. JSON — FormFieldObject (Campo de formulário)

```json
{
  "id": "fld-747a0f71-c6af-4db2-8111-e3c0bd126d9a",
  "page": 8,
  "type": "formfield",
  "field_type": "text",
  "label": "Nome do usuário",
  "x": 82.0,
  "y": 410.0,
  "width": 200.0,
  "height": 20.0,
  "required": true,
  "value": "",
  "font_name": "Verdana",
  "font_size": 11,
  "border_color": "#333333"
}
```

***

## 4. Teste — FormField, Link, Table

```python
def test_extract_table_objects():
    objs = extract_pdf_objects("input_tables.pdf")
    tables = [obj for page in objs['pages'] for obj in page['tables']]
    assert len(tables) > 0
    assert tables[0]['headers'] == ["Nome", "Cargo", "Data"]

def test_extract_link_objects():
    objs = extract_pdf_objects("input_links.pdf")
    links = [obj for page in objs['pages'] for obj in page.get('links',[])]
    assert links[0]['url'].startswith('https://')

def test_extract_formfields_objects():
    objs = extract_pdf_objects("input_formfields.pdf")
    fields = [obj for page in objs['pages'] for obj in page.get('formfields',[])]
    assert fields[0]['label'] == "Nome do usuário"
    assert fields[0]['required'] is True
```

***

## 5. Erro Real — Campo obrigatório sem valor

```json
{
  "error": "FormFieldRequiredError",
  "timestamp": "2025-11-18T14:10:23Z",
  "field_id": "fld-747a0f71-c6af-4db2-8111-e3c0bd126d9a",
  "page": 8,
  "field_type": "text",
  "label": "Nome do usuário",
  "message": "Campo obrigatório 'Nome do usuário' sem valor preenchido.",
  "suggestion": "Preencha o campo antes de salvar/editar o PDF."
}
```

***

## 6. Log Detalhado de Operações em Tabelas e Links

```json
[
  {
    "operation": "table_edit",
    "edit_id": "tbl-7cbbdf10-f645-4a6b-89ef-cfdaad4b30c8",
    "page": 5,
    "row": 1,
    "col": 2,
    "original_value": "2025-11-12",
    "new_value": "2025-12-01",
    "timestamp": "2025-11-18T14:17:12Z",
    "status": "success"
  },
  {
    "operation": "hyperlink_edit",
    "edit_id": "lnk-cfee1327-57cd-41cf-b286-621677293219",
    "page": 1,
    "original_url": "https://meusite.com/docs",
    "new_url": "https://meusite.com/atualizado",
    "timestamp": "2025-11-18T14:18:22Z",
    "status": "success"
  }
]
```

***

Esses exemplos devem ser seguidos literalmente pelo programador, sem improvisos ou mudanças na estrutura/schemas sem autorização do engenheiro responsável.

---

Aqui estão mais exemplos técnicos para campos de assinatura, checkbox, radio button e templates de testes avançados:

***

## 1. JSON — SignatureFieldObject (Campo de Assinatura)

```json
{
  "id": "sig-6fbe425c-c875-4dc6-9fe3-9957ae73d1e2",
  "page": 9,
  "type": "signature",
  "label": "Assinatura do responsável",
  "x": 130.0,
  "y": 540.0,
  "width": 200.0,
  "height": 28.0,
  "signed": false,
  "signer_name": "",
  "sign_time": null,
  "border_color": "#333333"
}
```

***

## 2. JSON — CheckboxFieldObject (Caixa de Seleção)

```json
{
  "id": "chk-4fbef488-92e2-4a70-bdee-252a34e46641",
  "page": 7,
  "type": "checkbox",
  "label": "Aceito os termos",
  "x": 68.0,
  "y": 307.0,
  "width": 14.0,
  "height": 14.0,
  "checked": true,
  "required": true
}
```

***

## 3. JSON — RadioButtonFieldObject (Botão de Rádio)

```json
{
  "id": "rbn-0d12cafe-7183-4ca4-8636-1be0f5b4c318",
  "page": 7,
  "type": "radiobutton",
  "group": "tipousuario",
  "label": "Administrador",
  "x": 95.0,
  "y": 350.0,
  "width": 14.0,
  "height": 14.0,
  "selected": false,
  "options": ["Administrador", "Usuário geral", "Visitante"]
}
```

***

## 4. Teste — Signature, Checkbox, Radio Button

```python
def test_extract_signature_fields():
    objs = extract_pdf_objects("input_signature.pdf")
    signatures = [obj for page in objs['pages'] for obj in page.get('signatures',[])]
    assert signatures[0]['signed'] is False
    assert signatures[0]['label'].startswith("Assinatura")

def test_extract_checkbox_fields():
    objs = extract_pdf_objects("input_checkboxes.pdf")
    checks = [obj for page in objs['pages'] for obj in page.get('checkboxes',[])]
    assert all(isinstance(check['checked'], bool) for check in checks)

def test_extract_radiobutton_fields():
    objs = extract_pdf_objects("input_radios.pdf")
    radios = [obj for page in objs['pages'] for obj in page.get('radiobuttons',[])]
    assert radios[0]['group'] == "tipousuario"
    assert "Administrador" in radios[0]['options']
```

***

## 5. Erros Reais — Signature Not Signed / Invalid Option

### Campo de assinatura não preenchido
```json
{
  "error": "SignatureNotFilledError",
  "timestamp": "2025-11-18T14:22:41Z",
  "field_id": "sig-6fbe425c-c875-4dc6-9fe3-9957ae73d1e2",
  "label": "Assinatura do responsável",
  "message": "Campo de assinatura obrigatório não está preenchido.",
  "suggestion": "Preencha, digitalize ou assine antes de salvar o PDF."
}
```

### Opção inválida para botão de rádio
```json
{
  "error": "RadioButtonInvalidOptionError",
  "timestamp": "2025-11-18T14:24:03Z",
  "field_id": "rbn-0d12cafe-7183-4ca4-8636-1be0f5b4c318",
  "selected": "Gestor",
  "valid_options": ["Administrador", "Usuário geral", "Visitante"],
  "message": "Opção de radio button 'Gestor' não pertence ao grupo permitido.",
  "suggestion": "Selecione apenas opções válidas do grupo tipousuario."
}
```

***

## 6. Log — Edição de Campos de Formulário

```json
[
  {
    "operation": "checkbox_toggle",
    "edit_id": "chk-4fbef488-92e2-4a70-bdee-252a34e46641",
    "page": 7,
    "original_checked": true,
    "new_checked": false,
    "timestamp": "2025-11-18T14:25:28Z",
    "user": "Cursor",
    "status": "success"
  },
  {
    "operation": "signature_fill",
    "edit_id": "sig-6fbe425c-c875-4dc6-9fe3-9957ae73d1e2",
    "page": 9,
    "signed": true,
    "signer_name": "Eduardo Alcantara",
    "sign_time": "2025-11-18T14:26:12Z",
    "status": "success"
  }
]
```

***

**Esses exemplos devem ser seguidos e mantidos como padrão para a implementação dos objetos e testes do projeto PDF-cli.**

---

Aqui estão exemplos complementares para objetos gráficos, anotações, desenhos vetoriais e templates de exportação/importação:

***

## 1. JSON — GraphicObject (Linha, Retângulo, Elipse)

```json
{
  "id": "gfx-23208c92-e1c2-46db-99bf-a94721d1cc98",
  "page": 4,
  "type": "line",
  "x1": 42.0,
  "y1": 250.0,
  "x2": 412.0,
  "y2": 250.0,
  "stroke_color": "#FF0000",
  "stroke_width": 2.0
}
```

```json
{
  "id": "gfx-23fdba92-9f76-433c-b91e-ddc77dda5bdf",
  "page": 4,
  "type": "rectangle",
  "x": 80.0,
  "y": 110.0,
  "width": 130.0,
  "height": 60.0,
  "fill_color": "#F0F0F0",
  "stroke_color": "#222222",
  "stroke_width": 1.5
}
```

```json
{
  "id": "gfx-2d317e3d-e208-4a36-b297-c6fbcdae9971",
  "page": 4,
  "type": "ellipse",
  "x": 250.0,
  "y": 120.0,
  "width": 100.0,
  "height": 50.0,
  "fill_color": "#00FF00",
  "stroke_color": "#333333"
}
```

***

## 2. JSON — AnnotationObject (Comentário, Marcador, Destaque)

```json
{
  "id": "ann-6b1e512a-3c1d-46f3-b454-daec678d4db8",
  "page": 2,
  "type": "highlight",
  "x": 140.0,
  "y": 180.0,
  "width": 94.0,
  "height": 18.0,
  "color": "#FFFF00",
  "comment": "Este texto deve ser revisado"
}
```

```json
{
  "id": "ann-681b712a-4e1c-46f3-b454-daec679d4dc6",
  "page": 3,
  "type": "comment",
  "x": 320.0,
  "y": 420.0,
  "content": "Sugestão de mudança no valor deste item.",
  "author": "Gerente",
  "date": "2025-11-18T14:32:01Z"
}
```

***

## 3. Template — Teste de Extração e Reconstrução de Objetos Gráficos

```python
def test_extract_graphic_objects():
    objs = extract_pdf_objects("input_graphics.pdf")
    lines = [obj for page in objs['pages'] for obj in page.get('lines',[])]
    rectangles = [obj for page in objs['pages'] for obj in page.get('rectangles',[])]
    assert len(lines) > 0
    assert rectangles[0]['fill_color'] == "#F0F0F0"
```

def test_extract_annotations():
    objs = extract_pdf_objects("input_annotations.pdf")
    highlights = [obj for page in objs['pages'] for obj in page.get('highlights',[])]
    comments = [obj for page in objs['pages'] for obj in page.get('comments',[])]
    assert highlights['color'] == "#FFFF00"
    assert comments['author'] == "Gerente"
```

---

## 4. Template — Exportação e Importação

### Exportar todos objetos para JSON
```
def export_objects_to_json(pdf_path: str, json_path: str) -> None:
    """
    Exporta todos objetos do PDF (textos, imagens, tabelas, gráficos, anotações, campos)
    para JSON estruturado conforme exemplos técnicos.
    """
    pass
```

### Importar objetos de JSON e reconstruir no PDF
```
def import_objects_from_json(json_path: str, output_pdf_path: str) -> None:
    """
    Reconstrói o PDF adicionando todos objetos especificados no JSON (textos, tabelas,
    gráficos, anotações etc.) com suas propriedades/layouts originais.
    """
    pass
```

---

## 5. Erros Reais — Recuperação em gráficos e anotações

### Erro: Cor de preenchimento inválida
```
{
  "error": "InvalidFillColorError",
  "timestamp": "2025-11-18T14:35:09Z",
  "object_id": "gfx-2d317e3d-e208-4a36-b297-c6fbcdae9971",
  "color": "FFZZ00",
  "message": "Valor de cor 'FFZZ00' não é válido (esperado formato hexadecimal #RRGGBB).",
  "suggestion": "Use valores hexadecimais corretos, exemplo: '#00FF00'."
}
```

### Erro: Comentário fora do limite da página
```
{
  "error": "AnnotationOutOfBoundsError",
  "timestamp": "2025-11-18T14:36:32Z",
  "object_id": "ann-681b712a-4e1c-46f3-b454-daec679d4dc6",
  "page": 3,
  "coordinates": {"x": 320.0, "y": 1420.0},
  "message": "Comentário está fora da área válida da página.",
  "suggestion": "Reveja coordenadas; máximo permitido é altura da página."
}
```

---

## 6. Log — Edição de Gráficos e Anotações

```
[
  {
    "operation": "rectangle_fill_change",
    "edit_id": "gfx-23fdba92-9f76-433c-b91e-ddc77dda5bdf",
    "page": 4,
    "original_fill": "#F0F0F0",
    "new_fill": "#FFCCCC",
    "timestamp": "2025-11-18T14:38:33Z",
    "status": "success"
  },
  {
    "operation": "annotation_comment_edit",
    "edit_id": "ann-681b712a-4e1c-46f3-b454-daec679d4dc6",
    "page": 3,
    "original_content": "Sugestão de mudança no valor deste item.",
    "new_content": "Valor alterado em reunião de aprovação.",
    "author": "Gerente",
    "timestamp": "2025-11-18T14:39:44Z",
    "status": "success"
  }
]
```

---

Esses exemplos devem ser usados como **padrão obrigatório** para implementação, teste, validação e documentação do projeto PDF-cli.

Aqui estão exemplos para objetos avançados: **polilinhas/vetores**, **curvas Bézier**, **layers de PDF** e **filtros** — além de templates para manipulação e logs detalhados.

***

## 1. JSON — PolylineObject (Polilinha)

```json
{
  "id": "ply-94e73288-822e-4c7e-8479-670e52ddac18",
  "page": 2,
  "type": "polyline",
  "points": [
    {"x": 60.0, "y": 100.0},
    {"x": 140.0, "y": 160.0},
    {"x": 320.0, "y": 120.0}
  ],
  "stroke_color": "#009900",
  "stroke_width": 1.0,
  "closed": false
}
```

***

## 2. JSON — BezierCurveObject (Curva Bézier)

```json
{
  "id": "bez-bbdb0908-3c55-4b70-bd2e-f821b5463b4f",
  "page": 5,
  "type": "beziercurve",
  "start": {"x": 60.0, "y": 240.0},
  "control1": {"x": 120.0, "y": 60.0},
  "control2": {"x": 180.0, "y": 340.0},
  "end": {"x": 220.0, "y": 240.0},
  "stroke_color": "#FF8800",
  "stroke_width": 2.0
}
```

***

## 3. JSON — LayerObject (Camada de PDF)

```json
{
  "id": "lyr-7dac8a46-17b8-44ff-8b23-8ad28a4b0c21",
  "name": "Marca d'água",
  "visible": true,
  "objects": [
    {
      "type": "text",
      "content": "CONFIDENCIAL",
      "x": 220.0,
      "y": 670.0,
      "font_size": 40,
      "font_name": "Arial-Bold",
      "color": "#CCCCCC",
      "rotation": 45
    }
  ]
}
```

***

## 4. JSON — FilterObject (Filtro aplicado à imagem/gráfico)

```json
{
  "id": "flt-1da2d5d6-c9b6-4a7e-9856-e1f2f4e3a3de",
  "type": "filter",
  "object_id": "img-18271c0e-9d04-4edd-abc1-022411da6e16",
  "filter_type": "grayscale",
  "params": {
    "intensity": 0.8
  }
}
```

***

## 5. Teste — Polilinha, Bézier, Layer, Filtro

```python
def test_extract_polyline_objects():
    objs = extract_pdf_objects("input_vectors.pdf")
    polylines = [obj for page in objs['pages'] for obj in page.get('polylines',[])]
    assert all(len(pl['points']) >= 2 for pl in polylines)

def test_extract_bezier_objects():
    objs = extract_pdf_objects("input_curves.pdf")
    beziers = [obj for page in objs['pages'] for obj in page.get('beziercurves',[])]
    assert beziers[0]['control1']['x'] > 0

def test_layer_extraction():
    layers = extract_layers("input_layers.pdf")
    assert layers[0]['name'] == "Marca d'água"
    assert layers[0]['visible'] is True

def test_filter_application():
    filters = extract_filters("input_filtered.pdf")
    assert filters[0]['filter_type'] == "grayscale"
    assert 0.0 <= filters[0]['params']['intensity'] <= 1.0
```

***

## 6. Logs — Manipulação Avançada

```json
[
  {
    "operation": "layer_visibility_change",
    "layer_id": "lyr-7dac8a46-17b8-44ff-8b23-8ad28a4b0c21",
    "old_visible": true,
    "new_visible": false,
    "timestamp": "2025-11-18T14:46:12Z",
    "status": "success"
  },
  {
    "operation": "apply_filter",
    "object_id": "img-18271c0e-9d04-4edd-abc1-022411da6e16",
    "filter_type": "grayscale",
    "params": {"intensity": 0.8},
    "timestamp": "2025-11-18T14:47:18Z",
    "status": "success"
  },
  {
    "operation": "bezier_edit",
    "curve_id": "bez-bbdb0908-3c55-4b70-bd2e-f821b5463b4f",
    "page": 5,
    "new_control1": {"x": 140.0, "y": 80.0},
    "timestamp": "2025-11-18T14:48:29Z",
    "status": "success"
  }
]
```

***

## 7. Erros — Vetores e Filtros

### Polilinha com menos de dois pontos
```json
{
  "error": "PolylinePointsError",
  "timestamp": "2025-11-18T14:49:41Z",
  "object_id": "ply-94e73288-822e-4c7e-8479-670e52ddac18",
  "message": "Polilinha deve conter pelo menos dois pontos.",
  "suggestion": "Adicione mais pontos."
}
```

### Filtro não suportado
```json
{
  "error": "FilterTypeError",
  "timestamp": "2025-11-18T14:50:27Z",
  "object_id": "flt-1da2d5d6-c9b6-4a7e-9856-e1f2f4e3a3de",
  "filter_type": "sepia",
  "message": "Filtro 'sepia' não é implementado.",
  "suggestion": "Use apenas os filtros disponíveis: grayscale, blur, invert."
}
```

***

**Esses padrões ampliam o escopo do projeto para toda manipulação gráfica, camadas e filtros, permitindo exportação/importação robusta e testes detalhados. Todo programador deve seguir rigorosamente estes exemplos técnicos.**

---
