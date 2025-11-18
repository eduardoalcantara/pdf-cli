"""
Módulo core - Modelos de dados e DTOs.

Este módulo contém as definições de objetos de domínio, DTOs e modelos
usados para representar elementos extraídos de arquivos PDF.

Todas as classes estão disponíveis para importação direta.
"""

# Exceções
from .exceptions import (
    PDFCliException,
    PDFFileNotFoundError,
    PDFMalformedError,
    TextNotFoundError,
    InvalidPageError,
    InvalidOperationError,
    PaddingError,
    InvalidFillColorError,
    AnnotationOutOfBoundsError,
    FormFieldRequiredError,
    SignatureNotFilledError,
    RadioButtonInvalidOptionError,
    PolylinePointsError,
    FilterTypeError,
)

# Modelos de objetos
from .models import (
    # Enums
    Alignment,
    FormFieldType,
    GraphicType,
    AnnotationType,
    FilterType,
    # Objetos básicos
    TextObject,
    ImageObject,
    TableObject,
    LinkObject,
    # Campos de formulário
    FormFieldObject,
    CheckboxFieldObject,
    RadioButtonFieldObject,
    SignatureFieldObject,
    # Objetos gráficos
    GraphicObject,
    LineObject,
    RectangleObject,
    EllipseObject,
    PolylineObject,
    BezierCurveObject,
    # Anotações
    AnnotationObject,
    HighlightAnnotation,
    CommentAnnotation,
    MarkerAnnotation,
    # Camadas e filtros
    LayerObject,
    FilterObject,
)

__all__ = [
    # Exceções
    "PDFCliException",
    "PDFFileNotFoundError",
    "PDFMalformedError",
    "TextNotFoundError",
    "InvalidPageError",
    "InvalidOperationError",
    "PaddingError",
    "InvalidFillColorError",
    "AnnotationOutOfBoundsError",
    "FormFieldRequiredError",
    "SignatureNotFilledError",
    "RadioButtonInvalidOptionError",
    "PolylinePointsError",
    "FilterTypeError",
    # Enums
    "Alignment",
    "FormFieldType",
    "GraphicType",
    "AnnotationType",
    "FilterType",
    # Objetos básicos
    "TextObject",
    "ImageObject",
    "TableObject",
    "LinkObject",
    # Campos de formulário
    "FormFieldObject",
    "CheckboxFieldObject",
    "RadioButtonFieldObject",
    "SignatureFieldObject",
    # Objetos gráficos
    "GraphicObject",
    "LineObject",
    "RectangleObject",
    "EllipseObject",
    "PolylineObject",
    "BezierCurveObject",
    # Anotações
    "AnnotationObject",
    "HighlightAnnotation",
    "CommentAnnotation",
    "MarkerAnnotation",
    # Camadas e filtros
    "LayerObject",
    "FilterObject",
]
