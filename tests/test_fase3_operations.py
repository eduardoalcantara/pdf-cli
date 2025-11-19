"""
Testes para operações da Fase 3 - Manipulação de Objetos PDF.

Este módulo contém testes unitários para validar as funcionalidades
implementadas na Fase 3, incluindo extração, edição, inserção, merge,
split e demais operações.
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import services
from app.pdf_repo import PDFRepository
from app.logging import OperationLogger
from core.exceptions import (
    PDFFileNotFoundError, TextNotFoundError, InvalidPageError,
    PaddingError
)
from core.models import TextObject


def test_parse_page_numbers():
    """Testa parsing de números de página."""
    assert services.parse_page_numbers("1,3,5") == [1, 3, 5]
    assert services.parse_page_numbers("1-5") == [1, 2, 3, 4, 5]
    assert services.parse_page_numbers("1,3-5,7") == [1, 3, 4, 5, 7]


def test_parse_page_ranges():
    """Testa parsing de faixas de páginas."""
    assert services.parse_page_ranges("1-3,4-6") == [(1, 3), (4, 6)]
    assert services.parse_page_ranges("1-5") == [(1, 5)]
    assert services.parse_page_ranges("1,3-5") == [(1, 1), (3, 5)]


def test_center_and_pad_text():
    """Testa cálculo de centralização e padding de texto."""
    text_obj = TextObject(
        id="test-123",
        page=0,
        content="Texto Original",
        x=100.0,
        y=100.0,
        width=200.0,
        height=20.0,
        font_name="Arial",
        font_size=12,
        color="#000000"
    )

    # Texto menor
    padded = services.center_and_pad_text(text_obj, "Novo")
    assert "Novo" in padded
    assert len(padded) >= len("Novo")

    # Teste de erro com texto muito grande
    try:
        services.center_and_pad_text(text_obj, "A" * 1000)
        assert False, "Deveria ter lançado PaddingError"
    except PaddingError:
        pass


def test_operation_logger():
    """Testa sistema de logging de operações."""
    logger = OperationLogger(log_dir=tempfile.mkdtemp())

    log = logger.create_operation_log(
        operation_type="test-operation",
        input_file="test.pdf",
        output_file="output.pdf",
        parameters={"key": "value"},
        result={"status": "success"}
    )

    assert log["operation_type"] == "test-operation"
    assert log["input_file"] == "test.pdf"
    assert log["status"] == "success"
    assert "operation_id" in log
    assert "timestamp" in log

    # Teste salvamento
    log_path = logger.save_log(log)
    assert Path(log_path).exists()

    # Verificar conteúdo
    with open(log_path, "r", encoding="utf-8") as f:
        loaded_log = json.load(f)
    assert loaded_log["operation_type"] == "test-operation"


def test_edit_metadata_structure():
    """Testa estrutura da função edit_metadata."""
    # Função deve aceitar os parâmetros corretos
    import inspect
    sig = inspect.signature(services.edit_metadata)
    params = list(sig.parameters.keys())

    assert "pdf_path" in params
    assert "output_path" in params
    assert "title" in params
    assert "author" in params
    assert "keywords" in params


def test_merge_pdf_structure():
    """Testa estrutura da função merge_pdf."""
    import inspect
    sig = inspect.signature(services.merge_pdf)
    params = list(sig.parameters.keys())

    assert "pdf_paths" in params
    assert "output_path" in params


def test_split_pdf_structure():
    """Testa estrutura da função split_pdf."""
    import inspect
    sig = inspect.signature(services.split_pdf)
    params = list(sig.parameters.keys())

    assert "pdf_path" in params
    assert "ranges" in params
    assert "output_prefix" in params


def test_export_objects_structure():
    """Testa estrutura da função export_objects."""
    import inspect
    sig = inspect.signature(services.export_objects)
    params = list(sig.parameters.keys())

    assert "pdf_path" in params
    assert "output_path" in params
    assert "types" in params


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("Testes da Fase 3 - Operações")
    print("=" * 60)

    tests = [
        test_parse_page_numbers,
        test_parse_page_ranges,
        test_center_and_pad_text,
        test_operation_logger,
        test_edit_metadata_structure,
        test_merge_pdf_structure,
        test_split_pdf_structure,
        test_export_objects_structure,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            print(f"\nTestando {test_func.__name__}...")
            test_func()
            print(f"  ✓ {test_func.__name__} OK")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test_func.__name__} FALHOU: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Resultado: {passed} passaram, {failed} falharam")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
