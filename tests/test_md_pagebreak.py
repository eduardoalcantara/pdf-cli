"""
Testes unitários para marcadores de quebra de página no md-to-pdf.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.md_converter import _preprocess_markdown, _PAGE_BREAK_HTML


@pytest.mark.parametrize(
    "marker",
    [
        "<!-- pdf-cli:pagebreak -->",
        "<!-- PDF-CLI:PAGEBREAK -->",
        "\\pagebreak",
        "[pagebreak]",
        "[PAGEBREAK]",
    ],
)
def test_pagebreak_markers_are_converted(marker: str) -> None:
    """Marcadores explícitos devem virar bloco HTML de quebra de página."""
    md = f"# Titulo\n\n{marker}\n\n## Proxima"
    result = _preprocess_markdown(md)

    assert _PAGE_BREAK_HTML.strip() in result
    assert marker not in result


def test_hr_is_not_pagebreak_by_default() -> None:
    """'---' isolado permanece regra horizontal Markdown por padrão."""
    md = "# Titulo\n\n---\n\n## Proxima"
    result = _preprocess_markdown(md)

    assert _PAGE_BREAK_HTML.strip() not in result
    assert "---" in result


def test_hr_pagebreak_with_legacy_flag() -> None:
    """'---' isolado vira quebra de página apenas com pagebreak_on_hr=True."""
    md = "# Titulo\n\n---\n\n## Proxima"
    result = _preprocess_markdown(md, pagebreak_on_hr=True)

    assert _PAGE_BREAK_HTML.strip() in result
    assert "---" not in result


def test_table_separator_is_not_pagebreak() -> None:
    """Separadores de tabela (|------|) não devem ser alterados."""
    md = "| Col | Val |\n|-----|-----|\n| A   | 1   |"
    result_default = _preprocess_markdown(md)
    result_legacy = _preprocess_markdown(md, pagebreak_on_hr=True)

    assert _PAGE_BREAK_HTML.strip() not in result_default
    assert _PAGE_BREAK_HTML.strip() not in result_legacy
    assert "|-----|" in result_default
    assert "|-----|" in result_legacy
