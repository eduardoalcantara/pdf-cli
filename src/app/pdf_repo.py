"""
Camada de infraestrutura para operações com arquivos PDF.

Este módulo encapsula todas as operações de baixo nível com PDFs,
utilizando PyMuPDF (fitz) e PyPDF2 para manipulação, leitura e escrita
de arquivos PDF. Serve como camada de abstração entre a lógica de negócio
e as bibliotecas específicas de PDF.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import fitz  # PyMuPDF
import base64
import shutil
from core.exceptions import PDFFileNotFoundError, PDFMalformedError, InvalidPageError
from core.models import (
    TextObject, ImageObject, TableObject, LinkObject,
    FormFieldObject, CheckboxFieldObject, RadioButtonFieldObject, SignatureFieldObject,
    LineObject, RectangleObject, EllipseObject, PolylineObject, BezierCurveObject,
    HighlightAnnotation, CommentAnnotation, MarkerAnnotation,
    LayerObject, FilterObject
)



class PDFRepository:
    """
    Repositório para operações de infraestrutura com arquivos PDF.

    Esta classe encapsula todas as interações de baixo nível com bibliotecas
    de manipulação de PDF, fornecendo uma interface limpa para a camada de
    serviços de aplicação.
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
                str(self.pdf_path)
            )
        if not self.pdf_path.is_file():
            raise PDFFileNotFoundError(
                str(self.pdf_path)
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
                str(self.pdf_path),
                f"Erro ao abrir: {str(e)}"
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

    def set_metadata(self, metadata: Dict[str, str]) -> None:
        """
        Define metadados do PDF.

        Args:
            metadata: Dicionário com metadados a serem definidos.
        """
        doc = self.open()
        doc.set_metadata(metadata)

    def extract_text_objects(self) -> List[TextObject]:
        """
        Extrai todos os objetos de texto do PDF.

        Returns:
            List[TextObject]: Lista de objetos de texto extraídos.
        """
        doc = self.open()
        text_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")

            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text_obj = TextObject(
                                page=page_num,
                                content=span.get("text", "").strip(),
                                x=span.get("bbox", [0, 0, 0, 0])[0],
                                y=span.get("bbox", [0, 0, 0, 0])[1],
                                width=span.get("bbox", [0, 0, 0, 0])[2] - span.get("bbox", [0, 0, 0, 0])[0],
                                height=span.get("bbox", [0, 0, 0, 0])[3] - span.get("bbox", [0, 0, 0, 0])[1],
                                font_name=span.get("font", ""),
                                font_size=int(span.get("size", 0)),
                                color=f"#{span.get('color', 0):06x}" if isinstance(span.get("color"), int) else "#000000",
                                rotation=0.0
                            )
                            if text_obj.content:
                                text_objects.append(text_obj)

        return text_objects

    def extract_image_objects(self) -> List[ImageObject]:
        """
        Extrai todas as imagens do PDF.

        Returns:
            List[ImageObject]: Lista de imagens extraídas.
        """
        doc = self.open()
        image_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Buscar posição da imagem na página
                image_rects = page.get_image_rects(xref)

                for rect in image_rects:
                    img_obj = ImageObject(
                        page=page_num,
                        mime_type=f"image/{image_ext}",
                        x=rect.x0,
                        y=rect.y0,
                        width=rect.width,
                        height=rect.height,
                        data_base64=base64.b64encode(image_bytes).decode("utf-8")
                    )
                    image_objects.append(img_obj)

        return image_objects

    def extract_link_objects(self) -> List[LinkObject]:
        """
        Extrai todos os links do PDF.

        Returns:
            List[LinkObject]: Lista de links extraídos.
        """
        doc = self.open()
        link_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            links = page.get_links()

            for link in links:
                link_obj = LinkObject(
                    page=page_num,
                    url=link.get("uri", ""),
                    x=link.get("from", fitz.Rect(0, 0, 0, 0)).x0,
                    y=link.get("from", fitz.Rect(0, 0, 0, 0)).y0,
                    width=link.get("from", fitz.Rect(0, 0, 0, 0)).width,
                    height=link.get("from", fitz.Rect(0, 0, 0, 0)).height,
                    link_type="uri"
                )
                link_objects.append(link_obj)

        return link_objects

    def extract_annotation_objects(self) -> List:
        """
        Extrai todas as anotações do PDF.

        Returns:
            List: Lista de anotações extraídas (HighlightAnnotation, CommentAnnotation, etc.).
        """
        doc = self.open()
        annotation_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            annots = page.annots()

            for annot in annots:
                annot_type = annot.type[1] if annot.type else ""
                info = annot.info
                rect = annot.rect

                if annot_type == "Highlight":
                    annot_obj = HighlightAnnotation(
                        page=page_num,
                        x=rect.x0,
                        y=rect.y0,
                        width=rect.width,
                        height=rect.height,
                        color=info.get("color", "#FFFF00"),
                        text=info.get("content", "")
                    )
                    annotation_objects.append(annot_obj)
                elif annot_type == "Text" or annot_type == "FreeText":
                    annot_obj = CommentAnnotation(
                        page=page_num,
                        x=rect.x0,
                        y=rect.y0,
                        width=rect.width,
                        height=rect.height,
                        author=info.get("title", ""),
                        content=info.get("content", ""),
                        date=info.get("modDate", "")
                    )
                    annotation_objects.append(annot_obj)

        return annotation_objects

    def save(self, output_path: Optional[str] = None) -> str:
        """
        Salva o documento PDF modificado.

        Args:
            output_path: Caminho de saída. Se None, sobrescreve o original.

        Returns:
            str: Caminho do arquivo salvo.
        """
        doc = self.open()
        if output_path is None:
            output_path = str(self.pdf_path)
        else:
            output_path = str(Path(output_path))

        doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        return output_path

    def merge_pdfs(self, pdf_paths: List[str]) -> fitz.Document:
        """
        Une múltiplos PDFs em um único documento.

        Args:
            pdf_paths: Lista de caminhos para os PDFs a serem unidos.

        Returns:
            fitz.Document: Documento PDF resultante da união.

        Raises:
            PDFFileNotFoundError: Se algum PDF não for encontrado.
        """
        # Validar todos os PDFs
        for pdf_path in pdf_paths:
            if not Path(pdf_path).exists():
                raise PDFFileNotFoundError(str(pdf_path))

        # Abrir PDF de base (este)
        merged_doc = fitz.open(str(self.pdf_path))

        # Inserir páginas dos outros PDFs
        for pdf_path in pdf_paths:
            if str(pdf_path) != str(self.pdf_path):
                other_doc = fitz.open(str(pdf_path))
                merged_doc.insert_pdf(other_doc)
                other_doc.close()

        return merged_doc

    def delete_pages(self, page_numbers: List[int]) -> fitz.Document:
        """
        Exclui páginas específicas do PDF.

        Args:
            page_numbers: Lista de números de páginas a serem excluídas (0-indexed).

        Returns:
            fitz.Document: Documento PDF modificado.

        Raises:
            InvalidPageError: Se algum número de página for inválido.
        """
        doc = self.open()
        max_pages = len(doc)

        # Validar páginas
        for page_num in page_numbers:
            if page_num < 0 or page_num >= max_pages:
                raise InvalidPageError(page_num, max_pages)

        # Ordenar páginas em ordem decrescente para deletar corretamente
        sorted_pages = sorted(set(page_numbers), reverse=True)

        # Criar novo documento com páginas mantidas
        new_doc = fitz.open()
        pages_to_keep = [i for i in range(max_pages) if i not in set(page_numbers)]

        for page_num in pages_to_keep:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        doc.close()
        self._doc = new_doc
        return new_doc

    def split_pages(self, ranges: List[tuple]) -> List[fitz.Document]:
        """
        Divide o PDF em múltiplos documentos conforme faixas de páginas.

        Args:
            ranges: Lista de tuplas (start, end) indicando faixas de páginas (0-indexed).

        Returns:
            List[fitz.Document]: Lista de documentos PDF resultantes.
        """
        doc = self.open()
        result_docs = []

        for start, end in ranges:
            if start < 0 or end >= len(doc) or start > end:
                raise InvalidPageError(start, len(doc))

            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)
            result_docs.append(new_doc)

        return result_docs

    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """
        Cria um backup do arquivo PDF original.

        Args:
            backup_path: Caminho do backup. Se None, usa nome automático.

        Returns:
            str: Caminho do arquivo de backup criado.
        """
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = str(self.pdf_path.parent / f"{self.pdf_path.stem}_backup_{timestamp}.pdf")

        shutil.copy2(str(self.pdf_path), backup_path)
        return backup_path

    def __enter__(self):
        """Context manager: abre o documento."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: fecha o documento."""
        self.close()
