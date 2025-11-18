"""
Modelos de dados para objetos extraídos de PDF.

Este módulo define os DTOs (Data Transfer Objects) e modelos utilizados
para representar elementos extraídos de arquivos PDF, incluindo textos,
imagens, tabelas, links, campos de formulário, gráficos, anotações, camadas e filtros.

Todos os modelos seguem os schemas JSON definidos em ESPECIFICACOES-FASE-2-EXTRACAO-EDICAO-TEXTO.md.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class Alignment(str, Enum):
    """Alinhamento de texto."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class FormFieldType(str, Enum):
    """Tipos de campos de formulário."""
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIOBUTTON = "radiobutton"
    SIGNATURE = "signature"


class GraphicType(str, Enum):
    """Tipos de objetos gráficos."""
    LINE = "line"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    POLYLINE = "polyline"
    BEZIER_CURVE = "beziercurve"


class AnnotationType(str, Enum):
    """Tipos de anotações."""
    HIGHLIGHT = "highlight"
    COMMENT = "comment"
    MARKER = "marker"


class FilterType(str, Enum):
    """Tipos de filtros."""
    GRAYSCALE = "grayscale"
    BLUR = "blur"
    INVERT = "invert"


# ============================================================================
# OBJETOS BÁSICOS
# ============================================================================

@dataclass
class TextObject:
    """
    DTO representando um objeto de texto extraído de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
        "align": "center",
        "rotation": 0
    }

    Example:
        >>> obj = TextObject(
        ...     id="bd2e4742-1373-4a74-bf58-67ecbe537d5a",
        ...     page=3,
        ...     content="Relação de Inscritos",
        ...     x=120.0,
        ...     y=80.0,
        ...     width=180.0,
        ...     height=22.0,
        ...     font_name="Times-New-Roman-Bold",
        ...     font_size=18,
        ...     color="#222222",
        ...     align="center"
        ... )
        >>> json_data = obj.to_dict()
        >>> reconstructed = TextObject.from_dict(json_data)
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    content: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    font_name: str = ""
    font_size: int = 0
    color: str = "#000000"
    align: Optional[str] = None
    rotation: Optional[float] = 0.0

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "content": self.content,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "color": self.color,
        }
        if self.align is not None:
            result["align"] = self.align
        if self.rotation is not None:
            result["rotation"] = self.rotation
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "TextObject":
        """Cria um TextObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            content=data.get("content", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            font_name=data.get("font_name", ""),
            font_size=data.get("font_size", 0),
            color=data.get("color", "#000000"),
            align=data.get("align"),
            rotation=data.get("rotation", 0.0),
        )


@dataclass
class ImageObject:
    """
    DTO representando uma imagem extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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

    Example:
        >>> obj = ImageObject(
        ...     id="img-18271c0e-9d04-4edd-abc1-022411da6e16",
        ...     page=2,
        ...     mime_type="image/png",
        ...     x=135.0,
        ...     y=220.0,
        ...     width=120,
        ...     height=64,
        ...     data_base64="iVBORw0KGgoAAAANSU...AgAA",
        ...     caption="Logo da empresa"
        ... )
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    mime_type: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    data_base64: str = ""
    caption: Optional[str] = None

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "mime_type": self.mime_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "data_base64": self.data_base64,
        }
        if self.caption is not None:
            result["caption"] = self.caption
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ImageObject":
        """Cria um ImageObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            mime_type=data.get("mime_type", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            data_base64=data.get("data_base64", ""),
            caption=data.get("caption"),
        )


@dataclass
class TableObject:
    """
    DTO representando uma tabela extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    type: str = "table"
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    cell_fonts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "headers": self.headers,
            "rows": self.rows,
            "cell_fonts": self.cell_fonts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TableObject":
        """Cria um TableObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type=data.get("type", "table"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            headers=data.get("headers", []),
            rows=data.get("rows", []),
            cell_fonts=data.get("cell_fonts", []),
        )


@dataclass
class LinkObject:
    """
    DTO representando um hiperlink extraído de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    type: str = "hyperlink"
    content: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    font_name: str = ""
    font_size: int = 0
    color: str = "#0055FF"
    url: str = ""

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "content": self.content,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "color": self.color,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LinkObject":
        """Cria um LinkObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type=data.get("type", "hyperlink"),
            content=data.get("content", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            font_name=data.get("font_name", ""),
            font_size=data.get("font_size", 0),
            color=data.get("color", "#0055FF"),
            url=data.get("url", ""),
        )


# ============================================================================
# CAMPOS DE FORMULÁRIO
# ============================================================================

@dataclass
class FormFieldObject:
    """
    DTO base para campos de formulário extraídos de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    type: str = "formfield"
    field_type: str = ""
    label: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    required: bool = False
    value: str = ""
    font_name: Optional[str] = None
    font_size: Optional[int] = None
    border_color: Optional[str] = None

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "field_type": self.field_type,
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "required": self.required,
            "value": self.value,
        }
        if self.font_name is not None:
            result["font_name"] = self.font_name
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.border_color is not None:
            result["border_color"] = self.border_color
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "FormFieldObject":
        """Cria um FormFieldObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type=data.get("type", "formfield"),
            field_type=data.get("field_type", ""),
            label=data.get("label", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            required=data.get("required", False),
            value=data.get("value", ""),
            font_name=data.get("font_name"),
            font_size=data.get("font_size"),
            border_color=data.get("border_color"),
        )


@dataclass
class CheckboxFieldObject(FormFieldObject):
    """
    DTO representando um campo checkbox extraído de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    checked: bool = False

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.field_type = "checkbox"
        if self.type == "formfield":
            self.type = "checkbox"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = super().to_dict()
        result["checked"] = self.checked
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "CheckboxFieldObject":
        """Cria um CheckboxFieldObject a partir de um dicionário."""
        obj = super().from_dict(data)
        obj.checked = data.get("checked", False)
        return cls(
            id=obj.id,
            page=obj.page,
            type="checkbox",
            field_type="checkbox",
            label=obj.label,
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            required=obj.required,
            value=obj.value,
            font_name=obj.font_name,
            font_size=obj.font_size,
            border_color=obj.border_color,
            checked=data.get("checked", False),
        )


@dataclass
class RadioButtonFieldObject(FormFieldObject):
    """
    DTO representando um campo radiobutton extraído de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    group: str = ""
    selected: bool = False
    options: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.field_type = "radiobutton"
        if self.type == "formfield":
            self.type = "radiobutton"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = super().to_dict()
        result["group"] = self.group
        result["selected"] = self.selected
        result["options"] = self.options
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "RadioButtonFieldObject":
        """Cria um RadioButtonFieldObject a partir de um dicionário."""
        obj = super().from_dict(data)
        return cls(
            id=obj.id,
            page=obj.page,
            type="radiobutton",
            field_type="radiobutton",
            label=obj.label,
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            required=obj.required,
            value=obj.value,
            font_name=obj.font_name,
            font_size=obj.font_size,
            border_color=obj.border_color,
            group=data.get("group", ""),
            selected=data.get("selected", False),
            options=data.get("options", []),
        )


@dataclass
class SignatureFieldObject(FormFieldObject):
    """
    DTO representando um campo de assinatura extraído de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    signed: bool = False
    signer_name: str = ""
    sign_time: Optional[str] = None

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.field_type = "signature"
        if self.type == "formfield":
            self.type = "signature"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = super().to_dict()
        result["signed"] = self.signed
        result["signer_name"] = self.signer_name
        if self.sign_time is not None:
            result["sign_time"] = self.sign_time
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "SignatureFieldObject":
        """Cria um SignatureFieldObject a partir de um dicionário."""
        obj = super().from_dict(data)
        return cls(
            id=obj.id,
            page=obj.page,
            type="signature",
            field_type="signature",
            label=obj.label,
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            required=obj.required,
            value=obj.value,
            font_name=obj.font_name,
            font_size=obj.font_size,
            border_color=obj.border_color,
            signed=data.get("signed", False),
            signer_name=data.get("signer_name", ""),
            sign_time=data.get("sign_time"),
        )


# ============================================================================
# OBJETOS GRÁFICOS
# ============================================================================

@dataclass
class GraphicObject:
    """Classe base para objetos gráficos."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    type: str = ""


@dataclass
class LineObject(GraphicObject):
    """
    DTO representando uma linha extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    stroke_color: str = "#000000"
    stroke_width: float = 1.0

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "line"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LineObject":
        """Cria um LineObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="line",
            x1=data.get("x1", 0.0),
            y1=data.get("y1", 0.0),
            x2=data.get("x2", 0.0),
            y2=data.get("y2", 0.0),
            stroke_color=data.get("stroke_color", "#000000"),
            stroke_width=data.get("stroke_width", 1.0),
        )


@dataclass
class RectangleObject(GraphicObject):
    """
    DTO representando um retângulo extraído de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    fill_color: Optional[str] = None
    stroke_color: str = "#000000"
    stroke_width: float = 1.0

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "rectangle"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
        }
        if self.fill_color is not None:
            result["fill_color"] = self.fill_color
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "RectangleObject":
        """Cria um RectangleObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="rectangle",
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            fill_color=data.get("fill_color"),
            stroke_color=data.get("stroke_color", "#000000"),
            stroke_width=data.get("stroke_width", 1.0),
        )


@dataclass
class EllipseObject(GraphicObject):
    """
    DTO representando uma elipse extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    fill_color: Optional[str] = None
    stroke_color: str = "#000000"

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "ellipse"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "stroke_color": self.stroke_color,
        }
        if self.fill_color is not None:
            result["fill_color"] = self.fill_color
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "EllipseObject":
        """Cria um EllipseObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="ellipse",
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            fill_color=data.get("fill_color"),
            stroke_color=data.get("stroke_color", "#000000"),
        )


@dataclass
class PolylineObject(GraphicObject):
    """
    DTO representando uma polilinha extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    points: List[Dict[str, float]] = field(default_factory=list)
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    closed: bool = False

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "polyline"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "points": self.points,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "closed": self.closed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PolylineObject":
        """Cria um PolylineObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="polyline",
            points=data.get("points", []),
            stroke_color=data.get("stroke_color", "#000000"),
            stroke_width=data.get("stroke_width", 1.0),
            closed=data.get("closed", False),
        )


@dataclass
class BezierCurveObject(GraphicObject):
    """
    DTO representando uma curva Bézier extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    start: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    control1: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    control2: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    end: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    stroke_color: str = "#000000"
    stroke_width: float = 1.0

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "beziercurve"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "start": self.start,
            "control1": self.control1,
            "control2": self.control2,
            "end": self.end,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BezierCurveObject":
        """Cria um BezierCurveObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="beziercurve",
            start=data.get("start", {"x": 0.0, "y": 0.0}),
            control1=data.get("control1", {"x": 0.0, "y": 0.0}),
            control2=data.get("control2", {"x": 0.0, "y": 0.0}),
            end=data.get("end", {"x": 0.0, "y": 0.0}),
            stroke_color=data.get("stroke_color", "#000000"),
            stroke_width=data.get("stroke_width", 1.0),
        )


# ============================================================================
# ANOTAÇÕES
# ============================================================================

@dataclass
class AnnotationObject:
    """Classe base para anotações."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    type: str = ""


@dataclass
class HighlightAnnotation(AnnotationObject):
    """
    DTO representando uma anotação de destaque (highlight) extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    color: str = "#FFFF00"
    comment: Optional[str] = None

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "highlight"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
        }
        if self.comment is not None:
            result["comment"] = self.comment
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "HighlightAnnotation":
        """Cria um HighlightAnnotation a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="highlight",
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            color=data.get("color", "#FFFF00"),
            comment=data.get("comment"),
        )


@dataclass
class CommentAnnotation(AnnotationObject):
    """
    DTO representando uma anotação de comentário extraída de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    x: float = 0.0
    y: float = 0.0
    content: str = ""
    author: Optional[str] = None
    date: Optional[str] = None

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "comment"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        result = {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "content": self.content,
        }
        if self.author is not None:
            result["author"] = self.author
        if self.date is not None:
            result["date"] = self.date
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "CommentAnnotation":
        """Cria um CommentAnnotation a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="comment",
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            content=data.get("content", ""),
            author=data.get("author"),
            date=data.get("date"),
        )


@dataclass
class MarkerAnnotation(AnnotationObject):
    """
    DTO representando uma anotação de marcador extraída de um PDF.

    Schema JSON similar a HighlightAnnotation.
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    color: str = "#FF0000"
    marker_type: str = "bookmark"

    def __post_init__(self):
        """Configura tipo após inicialização."""
        self.type = "marker"

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "page": self.page,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "marker_type": self.marker_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarkerAnnotation":
        """Cria um MarkerAnnotation a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            type="marker",
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            color=data.get("color", "#FF0000"),
            marker_type=data.get("marker_type", "bookmark"),
        )


# ============================================================================
# CAMADAS E FILTROS
# ============================================================================

@dataclass
class LayerObject:
    """
    DTO representando uma camada (layer) de um PDF.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
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
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    visible: bool = True
    objects: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "visible": self.visible,
            "objects": self.objects,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LayerObject":
        """Cria um LayerObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            visible=data.get("visible", True),
            objects=data.get("objects", []),
        )


@dataclass
class FilterObject:
    """
    DTO representando um filtro aplicado a uma imagem/gráfico.

    Schema JSON conforme ESPECIFICACOES-FASE-2:
    {
        "id": "flt-1da2d5d6-c9b6-4a7e-9856-e1f2f4e3a3de",
        "type": "filter",
        "object_id": "img-18271c0e-9d04-4edd-abc1-022411da6e16",
        "filter_type": "grayscale",
        "params": {
            "intensity": 0.8
        }
    }
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "filter"
    object_id: str = ""
    filter_type: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário JSON."""
        return {
            "id": self.id,
            "type": self.type,
            "object_id": self.object_id,
            "filter_type": self.filter_type,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FilterObject":
        """Cria um FilterObject a partir de um dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=data.get("type", "filter"),
            object_id=data.get("object_id", ""),
            filter_type=data.get("filter_type", ""),
            params=data.get("params", {}),
        )
