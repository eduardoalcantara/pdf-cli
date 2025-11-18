**Prompt para Cursor IDE — Modelos e Schemas Python (Fase 2)**

Você deve ler integralmente as especificações da Fase 2 (arquivo de instruções) e seguir à risca todos os exemplos e templates de objetos, erros e logs lá definidos.

**Sua tarefa:**

1. **Crie em `src/core/models.py` uma coleção de classes Python (preferencialmente usando dataclasses e type hints) para cada tipo de objeto do PDF mostrado nos exemplos, incluindo:**
   - TextObject
   - ImageObject
   - TableObject
   - LinkObject
   - FormFieldObject (e subclasses: Checkbox, RadioButton, Signature)
   - GraphicObject (e subclasses: Line, Rectangle, Ellipse, Polyline, BezierCurve)
   - LayerObject
   - FilterObject
   - AnnotationObject (Highlight, Comment, Marker)

2. **Implemente para cada classe:**
   - Campos exatos conforme o schema do template (nome/capitalização igual!)
   - Métodos de serialização para JSON (`to_dict`, `from_dict`)
   - Docstring explicativa com exemplo de uso e exemplo de saída JSON.

3. **Adicione classes customizadas para erros em `src/core/exceptions.py`, usando os exemplos de erros fornecidos:**
   - TextNotFoundError, PaddingError, InvalidFillColorError, AnnotationOutOfBoundsError, FormFieldRequiredError, RadioButtonInvalidOptionError, PolylinePointsError, FilterTypeError etc.
   - Cada erro com mensagem padrão, parâmetros do contexto (id/label/suggestion), docstring de uso.

4. **Garanta que todos objetos modelos possam ser reconhecidos/recebidos pelo CLI para validação, exportação e edição. Use enums ou subclasses para tipos específicos (ex: tipo do field, tipo do gráfico etc.)**

5. **Não altere os nomes dos campos! Caso haja ambiguidade, consulte o engenheiro antes de decidir.**

6. **Inclua exemplo de instancialização e serialização para cada classe em comentários/docstrings.**

7. **Ao terminar, teste que cada classe pode ser convertida para JSON usando `.to_dict()` e reconstruída usando `.from_dict()` sem perda de dados.**

**Exemplo de classe a implementar — TextObject:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TextObject:
    id: str
    page: int
    content: str
    x: float
    y: float
    width: float
    height: float
    font_name: str
    font_size: int
    color: str
    align: Optional[str] = None
    rotation: Optional[float] = 0

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d: dict):
        return TextObject(**d)

    """
    Example:
        obj = TextObject(
            id="bd2e4742-1373-4a74-bf58-67ecbe537d5a",
            page=3,
            content="Relação de Inscritos",
            x=110.0, y=80.0, width=180.0, height=22.0,
            font_name="Times-New-Roman-Bold",
            font_size=18,
            color="#222222",
            align="center"
        )
        print(obj.to_dict())
    """
```

**Repita esse padrão para todos os tipos de objeto e todos os erros listados. Quando concluir, documente em commit que todas as classes e modelos obrigatórios da Fase 2 estão implementados e prontos para testes.**

Ao final do trabalho, crie um documento de resultado da implementação da Fase 2, com o nome de FASE-1-RELATÓRIO.md em ./results/FASE-1-RELATÓRIO.md.
