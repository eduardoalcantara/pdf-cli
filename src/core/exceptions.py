"""
Exceções customizadas para o projeto PDF-cli.

Este módulo define exceções específicas para tratamento de erros
comuns ao trabalhar com arquivos PDF, como PDFs malformados,
textos não encontrados, operações inválidas, etc.

Todas as exceções seguem os padrões definidos em ESPECIFICACOES-FASE-2-EXTRACAO-EDICAO-TEXTO.md.
"""

from typing import Optional
from datetime import datetime


class PDFCliException(Exception):
    """
    Exceção base para todos os erros do PDF-cli.

    Todas as exceções customizadas herdam desta classe.
    """
    pass


class PDFFileNotFoundError(PDFCliException):
    """
    Exceção lançada quando um arquivo PDF não é encontrado.

    Example:
        >>> raise PDFFileNotFoundError("documento.pdf")
    """
    def __init__(self, pdf_path: str, message: Optional[str] = None):
        self.pdf_path = pdf_path
        self.message = message or f"Arquivo PDF não encontrado: {pdf_path}"
        super().__init__(self.message)


class PDFMalformedError(PDFCliException):
    """
    Exceção lançada quando um PDF está corrompido ou malformado.

    Example:
        >>> raise PDFMalformedError("documento.pdf", "Cabeçalho inválido")
    """
    def __init__(self, pdf_path: str, reason: str):
        self.pdf_path = pdf_path
        self.reason = reason
        message = f"PDF malformado em {pdf_path}: {reason}"
        super().__init__(message)


class TextNotFoundError(PDFCliException):
    """
    Exceção lançada quando um texto não é encontrado no PDF.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "TextNotFoundError",
        "timestamp": "2025-11-18T14:05:03Z",
        "search": "Documento válido",
        "page": "all",
        "message": "Texto 'Documento válido' não encontrado em nenhuma página.",
        "suggestion": "Use o comando 'export-text' para obter todos os textos presentes."
    }

    Example:
        >>> raise TextNotFoundError(
        ...     search="Documento válido",
        ...     page="all",
        ...     suggestion="Use o comando 'export-text' para obter todos os textos presentes."
        ... )
    """
    def __init__(
        self,
        search: str,
        page: str = "all",
        suggestion: Optional[str] = None
    ):
        self.search = search
        self.page = page
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Use o comando 'export-text' para obter todos os textos presentes."
        message = f"Texto '{search}' não encontrado em nenhuma página."
        if page != "all":
            message = f"Texto '{search}' não encontrado na página {page}."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "TextNotFoundError",
            "timestamp": self.timestamp,
            "search": self.search,
            "page": self.page,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class PaddingError(PDFCliException):
    """
    Exceção lançada quando o padding não pode ser aplicado.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
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

    Example:
        >>> raise PaddingError(
        ...     edit_id="b1a233de-eef2-477c-85de-c234bdc6ab06",
        ...     original_content="Prazo final",
        ...     new_content="Este texto novo ficou maior que o bloco original.",
        ...     width_original=140.2,
        ...     width_new=178.0
        ... )
    """
    def __init__(
        self,
        edit_id: str,
        original_content: str,
        new_content: str,
        width_original: float,
        width_new: float,
        suggestion: Optional[str] = None
    ):
        self.edit_id = edit_id
        self.original_content = original_content
        self.new_content = new_content
        self.width_original = width_original
        self.width_new = width_new
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Reduza o texto ou aumente tamanho do bloco/font."
        message = "Texto novo ultrapassa largura máxima do bloco."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "PaddingError",
            "timestamp": self.timestamp,
            "edit_id": self.edit_id,
            "original_content": self.original_content,
            "new_content": self.new_content,
            "width_original": self.width_original,
            "width_new": self.width_new,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class InvalidPageError(PDFCliException):
    """
    Exceção lançada quando uma página inválida é referenciada.

    Example:
        >>> raise InvalidPageError(page_number=100, max_pages=10)
    """
    def __init__(self, page_number: int, max_pages: int):
        self.page_number = page_number
        self.max_pages = max_pages
        message = f"Página {page_number} inválida. O PDF possui apenas {max_pages} página(s)."
        super().__init__(message)


class InvalidOperationError(PDFCliException):
    """
    Exceção lançada quando uma operação inválida é tentada.

    Example:
        >>> raise InvalidOperationError("Não é possível editar um PDF somente leitura")
    """
    pass


class InvalidFillColorError(PDFCliException):
    """
    Exceção lançada quando uma cor de preenchimento inválida é fornecida.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "InvalidFillColorError",
        "timestamp": "2025-11-18T14:35:09Z",
        "object_id": "gfx-2d317e3d-e208-4a36-b297-c6fbcdae9971",
        "color": "FFZZ00",
        "message": "Valor de cor 'FFZZ00' não é válido (esperado formato hexadecimal #RRGGBB).",
        "suggestion": "Use valores hexadecimais corretos, exemplo: '#00FF00'."
    }

    Example:
        >>> raise InvalidFillColorError(
        ...     object_id="gfx-2d317e3d-e208-4a36-b297-c6fbcdae9971",
        ...     color="FFZZ00"
        ... )
    """
    def __init__(
        self,
        object_id: str,
        color: str,
        suggestion: Optional[str] = None
    ):
        self.object_id = object_id
        self.color = color
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Use valores hexadecimais corretos, exemplo: '#00FF00'."
        message = f"Valor de cor '{color}' não é válido (esperado formato hexadecimal #RRGGBB)."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "InvalidFillColorError",
            "timestamp": self.timestamp,
            "object_id": self.object_id,
            "color": self.color,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class AnnotationOutOfBoundsError(PDFCliException):
    """
    Exceção lançada quando uma anotação está fora dos limites da página.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "AnnotationOutOfBoundsError",
        "timestamp": "2025-11-18T14:36:32Z",
        "object_id": "ann-681b712a-4e1c-46f3-b454-daec679d4dc6",
        "page": 3,
        "coordinates": {"x": 320.0, "y": 1420.0},
        "message": "Comentário está fora da área válida da página.",
        "suggestion": "Reveja coordenadas; máximo permitido é altura da página."
    }

    Example:
        >>> raise AnnotationOutOfBoundsError(
        ...     object_id="ann-681b712a-4e1c-46f3-b454-daec679d4dc6",
        ...     page=3,
        ...     coordinates={"x": 320.0, "y": 1420.0}
        ... )
    """
    def __init__(
        self,
        object_id: str,
        page: int,
        coordinates: dict,
        suggestion: Optional[str] = None
    ):
        self.object_id = object_id
        self.page = page
        self.coordinates = coordinates
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Reveja coordenadas; máximo permitido é altura da página."
        message = "Comentário está fora da área válida da página."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "AnnotationOutOfBoundsError",
            "timestamp": self.timestamp,
            "object_id": self.object_id,
            "page": self.page,
            "coordinates": self.coordinates,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class FormFieldRequiredError(PDFCliException):
    """
    Exceção lançada quando um campo de formulário obrigatório não está preenchido.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
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

    Example:
        >>> raise FormFieldRequiredError(
        ...     field_id="fld-747a0f71-c6af-4db2-8111-e3c0bd126d9a",
        ...     page=8,
        ...     field_type="text",
        ...     label="Nome do usuário"
        ... )
    """
    def __init__(
        self,
        field_id: str,
        page: int,
        field_type: str,
        label: str,
        suggestion: Optional[str] = None
    ):
        self.field_id = field_id
        self.page = page
        self.field_type = field_type
        self.label = label
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Preencha o campo antes de salvar/editar o PDF."
        message = f"Campo obrigatório '{label}' sem valor preenchido."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "FormFieldRequiredError",
            "timestamp": self.timestamp,
            "field_id": self.field_id,
            "page": self.page,
            "field_type": self.field_type,
            "label": self.label,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class SignatureNotFilledError(PDFCliException):
    """
    Exceção lançada quando um campo de assinatura obrigatório não está preenchido.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "SignatureNotFilledError",
        "timestamp": "2025-11-18T14:22:41Z",
        "field_id": "sig-6fbe425c-c875-4dc6-9fe3-9957ae73d1e2",
        "label": "Assinatura do responsável",
        "message": "Campo de assinatura obrigatório não está preenchido.",
        "suggestion": "Preencha, digitalize ou assine antes de salvar o PDF."
    }

    Example:
        >>> raise SignatureNotFilledError(
        ...     field_id="sig-6fbe425c-c875-4dc6-9fe3-9957ae73d1e2",
        ...     label="Assinatura do responsável"
        ... )
    """
    def __init__(
        self,
        field_id: str,
        label: str,
        suggestion: Optional[str] = None
    ):
        self.field_id = field_id
        self.label = label
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Preencha, digitalize ou assine antes de salvar o PDF."
        message = "Campo de assinatura obrigatório não está preenchido."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "SignatureNotFilledError",
            "timestamp": self.timestamp,
            "field_id": self.field_id,
            "label": self.label,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class RadioButtonInvalidOptionError(PDFCliException):
    """
    Exceção lançada quando uma opção inválida é selecionada para um radio button.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "RadioButtonInvalidOptionError",
        "timestamp": "2025-11-18T14:24:03Z",
        "field_id": "rbn-0d12cafe-7183-4ca4-8636-1be0f5b4c318",
        "selected": "Gestor",
        "valid_options": ["Administrador", "Usuário geral", "Visitante"],
        "message": "Opção de radio button 'Gestor' não pertence ao grupo permitido.",
        "suggestion": "Selecione apenas opções válidas do grupo tipousuario."
    }

    Example:
        >>> raise RadioButtonInvalidOptionError(
        ...     field_id="rbn-0d12cafe-7183-4ca4-8636-1be0f5b4c318",
        ...     selected="Gestor",
        ...     valid_options=["Administrador", "Usuário geral", "Visitante"]
        ... )
    """
    def __init__(
        self,
        field_id: str,
        selected: str,
        valid_options: list,
        suggestion: Optional[str] = None
    ):
        self.field_id = field_id
        self.selected = selected
        self.valid_options = valid_options
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Selecione apenas opções válidas do grupo."
        message = f"Opção de radio button '{selected}' não pertence ao grupo permitido."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "RadioButtonInvalidOptionError",
            "timestamp": self.timestamp,
            "field_id": self.field_id,
            "selected": self.selected,
            "valid_options": self.valid_options,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class PolylinePointsError(PDFCliException):
    """
    Exceção lançada quando uma polilinha não possui pontos suficientes.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "PolylinePointsError",
        "timestamp": "2025-11-18T14:49:41Z",
        "object_id": "ply-94e73288-822e-4c7e-8479-670e52ddac18",
        "message": "Polilinha deve conter pelo menos dois pontos.",
        "suggestion": "Adicione mais pontos."
    }

    Example:
        >>> raise PolylinePointsError(object_id="ply-94e73288-822e-4c7e-8479-670e52ddac18")
    """
    def __init__(
        self,
        object_id: str,
        suggestion: Optional[str] = None
    ):
        self.object_id = object_id
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.suggestion = suggestion or "Adicione mais pontos."
        message = "Polilinha deve conter pelo menos dois pontos."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "PolylinePointsError",
            "timestamp": self.timestamp,
            "object_id": self.object_id,
            "message": str(self),
            "suggestion": self.suggestion,
        }


class FilterTypeError(PDFCliException):
    """
    Exceção lançada quando um tipo de filtro não é suportado.

    Segue o schema de erro conforme ESPECIFICACOES-FASE-2:
    {
        "error": "FilterTypeError",
        "timestamp": "2025-11-18T14:50:27Z",
        "object_id": "flt-1da2d5d6-c9b6-4a7e-9856-e1f2f4e3a3de",
        "filter_type": "sepia",
        "message": "Filtro 'sepia' não é implementado.",
        "suggestion": "Use apenas os filtros disponíveis: grayscale, blur, invert."
    }

    Example:
        >>> raise FilterTypeError(
        ...     object_id="flt-1da2d5d6-c9b6-4a7e-9856-e1f2f4e3a3de",
        ...     filter_type="sepia"
        ... )
    """
    def __init__(
        self,
        object_id: str,
        filter_type: str,
        available_filters: Optional[list] = None,
        suggestion: Optional[str] = None
    ):
        self.object_id = object_id
        self.filter_type = filter_type
        self.available_filters = available_filters or ["grayscale", "blur", "invert"]
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        default_suggestion = f"Use apenas os filtros disponíveis: {', '.join(self.available_filters)}."
        self.suggestion = suggestion or default_suggestion
        message = f"Filtro '{filter_type}' não é implementado."
        super().__init__(message)

    def to_dict(self) -> dict:
        """Converte o erro para dicionário JSON."""
        return {
            "error": "FilterTypeError",
            "timestamp": self.timestamp,
            "object_id": self.object_id,
            "filter_type": self.filter_type,
            "message": str(self),
            "suggestion": self.suggestion,
        }
