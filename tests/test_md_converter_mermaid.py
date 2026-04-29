"""
Testes unitários para suporte Mermaid no md_converter.

Valida o pré-processamento de blocos ```mermaid``` para imagens PNG embutidas
via data URI, sem depender de instalação real de Node durante os testes.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import md_converter
from core.exceptions import MermaidRendererNotAvailableError, MermaidRenderingError


def test_render_mermaid_blocks_sem_diagramas_mantem_markdown_original() -> None:
    """Deve manter o conteúdo inalterado quando não houver blocos Mermaid."""
    markdown_input = "# Titulo\n\nTexto comum.\n\n```python\nprint('ok')\n```\n"

    markdown_output, total = md_converter._render_mermaid_blocks_in_markdown(markdown_input)

    assert total == 0
    assert markdown_output == markdown_input


def test_render_mermaid_blocks_com_mmdc_gera_data_uri(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deve renderizar Mermaid com mmdc e substituir por imagem data URI."""

    def fake_which(command_name: str):
        if command_name == "mmdc":
            return "/usr/bin/mmdc"
        return None

    def fake_run(command, capture_output, text, check):
        output_path = Path(command[command.index("-o") + 1])
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nfake-png-data")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(md_converter.shutil, "which", fake_which)
    monkeypatch.setattr(md_converter.subprocess, "run", fake_run)

    markdown_input = (
        "# Arquitetura\n\n"
        "```mermaid\n"
        "graph TD\n"
        "    A[Inicio] --> B[Fim]\n"
        "```\n"
    )

    markdown_output, total = md_converter._render_mermaid_blocks_in_markdown(markdown_input)

    assert total == 1
    assert "```mermaid" not in markdown_output
    assert "data:image/png;base64," in markdown_output
    assert "Diagrama Mermaid 1" in markdown_output


def test_render_mermaid_blocks_sem_renderer_disponivel_lanca_erro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deve falhar com mensagem clara quando Mermaid existir sem renderer."""

    monkeypatch.setattr(md_converter.shutil, "which", lambda *_: None)

    markdown_input = "```mermaid\ngraph TD\nA-->B\n```\n"

    with pytest.raises(MermaidRendererNotAvailableError):
        md_converter._render_mermaid_blocks_in_markdown(markdown_input)


def test_render_mermaid_blocks_falha_no_renderer_lanca_erro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deve lançar MermaidRenderingError quando o processo externo falhar."""

    def fake_which(command_name: str):
        if command_name == "mmdc":
            return "/usr/bin/mmdc"
        return None

    def fake_run(command, capture_output, text, check):
        return SimpleNamespace(returncode=1, stdout="", stderr="Parse error in Mermaid source")

    monkeypatch.setattr(md_converter.shutil, "which", fake_which)
    monkeypatch.setattr(md_converter.subprocess, "run", fake_run)

    markdown_input = "```mermaid\ngraph TD\nA-->B\n```\n"

    with pytest.raises(MermaidRenderingError) as exc:
        md_converter._render_mermaid_blocks_in_markdown(markdown_input)

    assert "Falha ao renderizar diagrama Mermaid" in str(exc.value)
