"""
Modelos de dados para objetos extraídos de PDF.

Este módulo define os DTOs (Data Transfer Objects) e modelos utilizados
para representar elementos textuais extraídos de arquivos PDF, incluindo
metadados como posição, fonte, tamanho e identificadores únicos.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class TextObject:
    """
    DTO representando um objeto de texto extraído de um PDF.

    Cada objeto textural possui um identificador único (UUID), página de origem,
    coordenadas, informações de fonte e o texto propriamente dito. Este modelo
    facilita a exportação para JSON e a edição posterior do PDF.

    Attributes:
        id: Identificador único (UUID) do objeto de texto.
        page: Número da página (0-indexed) onde o texto está localizado.
        x0: Coordenada X inicial (esquerda) da caixa delimitadora.
        y0: Coordenada Y inicial (superior) da caixa delimitadora.
        x1: Coordenada X final (direita) da caixa delimitadora.
        y1: Coordenada Y final (inferior) da caixa delimitadora.
        text: Conteúdo textual do objeto.
        fontname: Nome da fonte utilizada (se disponível).
        fontsize: Tamanho da fonte em pontos (se disponível).
        flags: Flags de formatação (negrito, itálico, etc.) - padrão do PyMuPDF.

    TODO (Fase 2):
        - Adicionar suporte a cores (RGB/RGB) do texto
        - Adicionar rotação/ângulo do texto
        - Adicionar informações de espaçamento entre caracteres
        - Implementar métodos de serialização/deserialização JSON
        - Adicionar validação de coordenadas
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page: int = 0
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0
    text: str = ""
    fontname: Optional[str] = None
    fontsize: Optional[float] = None
    flags: Optional[int] = None

    def to_dict(self) -> dict:
        """
        Converte o objeto TextObject para um dicionário.

        Returns:
            dict: Representação em dicionário do objeto.
        """
        return {
            "id": self.id,
            "page": self.page,
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "text": self.text,
            "fontname": self.fontname,
            "fontsize": self.fontsize,
            "flags": self.flags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TextObject":
        """
        Cria um TextObject a partir de um dicionário.

        Args:
            data: Dicionário contendo os dados do objeto.

        Returns:
            TextObject: Instância criada a partir do dicionário.
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            page=data.get("page", 0),
            x0=data.get("x0", 0.0),
            y0=data.get("y0", 0.0),
            x1=data.get("x1", 0.0),
            y1=data.get("y1", 0.0),
            text=data.get("text", ""),
            fontname=data.get("fontname"),
            fontsize=data.get("fontsize"),
            flags=data.get("flags"),
        )
