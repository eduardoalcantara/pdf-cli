"""
Camada de infraestrutura para operações com arquivos PDF.

Este módulo encapsula todas as operações de baixo nível com PDFs,
utilizando PyMuPDF (fitz) e PyPDF2 para manipulação, leitura e escrita
de arquivos PDF. Serve como camada de abstração entre a lógica de negócio
e as bibliotecas específicas de PDF.

TODO (Fase 1):
    - Implementar abertura e validação de arquivos PDF
    - Implementar leitura de metadados básicos
    - Implementar verificação de integridade de PDF

TODO (Fase 2):
    - Implementar extração de objetos de texto (TextObjects)
    - Implementar escrita/atualização de textos no PDF
    - Implementar salvamento de PDF modificado

TODO (Fase 3):
    - Implementar merge de múltiplos PDFs
    - Implementar exclusão de páginas
    - Implementar cópia/duplicação de páginas
"""

from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from core.exceptions import PDFFileNotFoundError, PDFMalformedError
from core.models import TextObject


class PDFRepository:
    """
    Repositório para operações de infraestrutura com arquivos PDF.

    Esta classe encapsula todas as interações de baixo nível com bibliotecas
    de manipulação de PDF, fornecendo uma interface limpa para a camada de
    serviços de aplicação.

    TODO: Implementar métodos conforme fases do projeto.
    """

    def __init__(self, pdf_path: str):
        """
        Inicializa o repositório com um arquivo PDF.

        Args:
            pdf_path: Caminho para o arquivo PDF.

        Raises:
            PDFFileNotFoundError: Se o arquivo não for encontrado.
            PDFMalformedError: Se o arquivo estiver corrompido.
        """
        self.pdf_path = Path(pdf_path)
        self._validate_pdf_path()
        self._doc: Optional[fitz.Document] = None

    def _validate_pdf_path(self) -> None:
        """
        Valida se o caminho do PDF existe e é um arquivo válido.

        Raises:
            PDFFileNotFoundError: Se o arquivo não for encontrado.
        """
        if not self.pdf_path.exists():
            raise PDFFileNotFoundError(
                f"Arquivo PDF não encontrado: {self.pdf_path}"
            )
        if not self.pdf_path.is_file():
            raise PDFFileNotFoundError(
                f"O caminho não é um arquivo: {self.pdf_path}"
            )

    def open(self) -> fitz.Document:
        """
        Abre o documento PDF e retorna a instância do PyMuPDF.

        Returns:
            fitz.Document: Documento PDF aberto.

        Raises:
            PDFMalformedError: Se o PDF estiver corrompido.
        """
        try:
            if self._doc is None:
                self._doc = fitz.open(str(self.pdf_path))
            return self._doc
        except Exception as e:
            raise PDFMalformedError(
                f"Erro ao abrir PDF {self.pdf_path}: {str(e)}"
            ) from e

    def close(self) -> None:
        """Fecha o documento PDF, liberando recursos."""
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def get_page_count(self) -> int:
        """
        Retorna o número de páginas do PDF.

        Returns:
            int: Número de páginas.
        """
        doc = self.open()
        return len(doc)

    def get_metadata(self) -> dict:
        """
        Retorna os metadados do PDF.

        Returns:
            dict: Dicionário com metadados do PDF.
        """
        doc = self.open()
        return doc.metadata

    def __enter__(self):
        """Context manager: abre o documento."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: fecha o documento."""
        self.close()

    # TODO (Fase 2): Implementar métodos de extração e escrita de textos
    # def extract_text_objects(self) -> List[TextObject]:
    #     """Extrai todos os objetos de texto do PDF."""
    #     pass

    # TODO (Fase 3): Implementar métodos de manipulação estrutural
    # def merge_pdfs(self, pdf_paths: List[str]) -> fitz.Document:
    #     """Une múltiplos PDFs em um único documento."""
    #     pass

    # def delete_pages(self, page_numbers: List[int]) -> fitz.Document:
    #     """Exclui páginas específicas do PDF."""
    #     pass
