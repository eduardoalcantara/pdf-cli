"""
Testes unitários para suporte PlantUML no md_converter.

Valida o pré-processamento de:
- blocos ```plantuml``` / ```plantxml```
- referências de imagem para arquivos `.plantuml` locais
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import md_converter
from core.exceptions import PlantUMLRendererNotAvailableError, PlantUMLRenderingError


def test_render_plantuml_blocks_sem_diagramas_mantem_markdown_original(tmp_path: Path) -> None:
    """Deve manter conteúdo inalterado quando não houver PlantUML."""
    markdown_input = "# Titulo\n\nTexto comum.\n\n```python\nprint('ok')\n```\n"

    markdown_output, total = md_converter._render_plantuml_blocks_in_markdown(
        md_content=markdown_input,
        md_base_dir=tmp_path,
    )

    assert total == 0
    assert markdown_output == markdown_input


def test_render_plantuml_block_gera_data_uri(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Deve renderizar bloco plantuml e substituir por imagem data URI."""

    def fake_which(command_name: str):
        if command_name == "plantuml":
            return "/usr/bin/plantuml"
        return None

    def fake_run(command, capture_output, check):
        input_path = Path(command[-1])
        output_path = input_path.with_suffix(".png")
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nplantuml-png-data")
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(md_converter.shutil, "which", fake_which)
    monkeypatch.setattr(md_converter.subprocess, "run", fake_run)

    markdown_input = (
        "# Arquitetura\n\n"
        "```plantuml\n"
        "Alice -> Bob: Teste\n"
        "```\n"
    )

    markdown_output, total = md_converter._render_plantuml_blocks_in_markdown(
        md_content=markdown_input,
        md_base_dir=tmp_path,
    )

    assert total == 1
    assert "```plantuml" not in markdown_output
    assert "data:image/png;base64," in markdown_output
    assert "Diagrama PlantUML 1" in markdown_output


def test_render_plantxml_block_gera_data_uri(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Deve tratar `plantxml` como alias de bloco PlantUML."""

    def fake_which(command_name: str):
        if command_name == "plantuml":
            return "/usr/bin/plantuml"
        return None

    def fake_run(command, capture_output, check):
        input_path = Path(command[-1])
        output_path = input_path.with_suffix(".png")
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nplantxml-png-data")
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(md_converter.shutil, "which", fake_which)
    monkeypatch.setattr(md_converter.subprocess, "run", fake_run)

    markdown_input = (
        "```plantxml\n"
        "Alice -> Bob: Alias plantxml\n"
        "```\n"
    )

    markdown_output, total = md_converter._render_plantuml_blocks_in_markdown(
        md_content=markdown_input,
        md_base_dir=tmp_path,
    )

    assert total == 1
    assert "```plantxml" not in markdown_output
    assert "data:image/png;base64," in markdown_output


def test_render_plantuml_file_reference_gera_data_uri(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Deve renderizar referência markdown para arquivo `.plantuml` local."""

    def fake_which(command_name: str):
        if command_name == "plantuml":
            return "/usr/bin/plantuml"
        return None

    def fake_run(command, capture_output, check):
        input_path = Path(command[-1])
        output_path = input_path.with_suffix(".png")
        output_path.write_bytes(b"\x89PNG\r\n\x1a\nplantuml-file-png")
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(md_converter.shutil, "which", fake_which)
    monkeypatch.setattr(md_converter.subprocess, "run", fake_run)

    diagram_file = tmp_path / "modelo.plantuml"
    diagram_file.write_text("@startuml\nA -> B\n@enduml\n", encoding="utf-8")

    markdown_input = "![Diagrama](modelo.plantuml)\n"
    markdown_output, total = md_converter._render_plantuml_blocks_in_markdown(
        md_content=markdown_input,
        md_base_dir=tmp_path,
    )

    assert total == 1
    assert "modelo.plantuml" not in markdown_output
    assert "data:image/png;base64," in markdown_output
    assert "![Diagrama](" in markdown_output


def test_render_plantuml_sem_renderer_disponivel_lanca_erro(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Deve falhar com mensagem clara quando PlantUML existir sem renderer."""

    monkeypatch.setattr(md_converter.shutil, "which", lambda *_: None)

    markdown_input = "```plantuml\nA -> B\n```\n"
    with pytest.raises(PlantUMLRendererNotAvailableError):
        md_converter._render_plantuml_blocks_in_markdown(
            md_content=markdown_input,
            md_base_dir=tmp_path,
        )


def test_render_plantuml_arquivo_inexistente_lanca_erro(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Deve falhar quando referência `.plantuml` local não existir."""

    def fake_which(command_name: str):
        if command_name == "plantuml":
            return "/usr/bin/plantuml"
        return None

    monkeypatch.setattr(md_converter.shutil, "which", fake_which)

    markdown_input = "![Diagrama](arquivo_inexistente.plantuml)\n"

    with pytest.raises(PlantUMLRenderingError) as exc:
        md_converter._render_plantuml_blocks_in_markdown(
            md_content=markdown_input,
            md_base_dir=tmp_path,
        )

    assert "nao encontrado" in str(exc.value)
