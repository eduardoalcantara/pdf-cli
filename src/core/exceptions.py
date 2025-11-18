"""
Exceções customizadas para o projeto PDF-cli.

Este módulo define exceções específicas para tratamento de erros
comuns ao trabalhar com arquivos PDF, como PDFs malformados,
textos não encontrados, operações inválidas, etc.
"""


class PDFCliException(Exception):
    """Exceção base para todos os erros do PDF-cli."""
    pass


class PDFFileNotFoundError(PDFCliException):
    """Exceção lançada quando um arquivo PDF não é encontrado."""
    pass


class PDFMalformedError(PDFCliException):
    """Exceção lançada quando um PDF está corrompido ou malformado."""
    pass


class TextNotFoundError(PDFCliException):
    """Exceção lançada quando um texto não é encontrado no PDF."""
    pass


class InvalidPageError(PDFCliException):
    """Exceção lançada quando uma página inválida é referenciada."""
    pass


class InvalidOperationError(PDFCliException):
    """Exceção lançada quando uma operação inválida é tentada."""
    pass
