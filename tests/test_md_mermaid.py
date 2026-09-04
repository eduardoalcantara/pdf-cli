"""
Testes unitários para renderização de blocos Mermaid no md-to-pdf.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.md_converter import (
    _MERMAID_WORKDIR_NAME,
    _find_mermaid_cli,
    _render_mermaid_blocks,
)


SAMPLE_MERMAID_MD = """# Titulo

```mermaid
graph TD
    A --> B
```

Texto apos.
"""


def test_no_mermaid_blocks_unchanged(tmp_path: Path) -> None:
    """Markdown sem Mermaid permanece igual."""
    md = "# Sem diagrama\n\nApenas texto.\n"
    out, count = _render_mermaid_blocks(md, tmp_path / _MERMAID_WORKDIR_NAME)
    assert out == md
    assert count == 0


def test_render_mermaid_disabled_keeps_fence(tmp_path: Path) -> None:
    """Com enabled=False, o fence Mermaid nao e alterado."""
    out, count = _render_mermaid_blocks(
        SAMPLE_MERMAID_MD,
        tmp_path / _MERMAID_WORKDIR_NAME,
        enabled=False,
    )
    assert "```mermaid" in out
    assert count == 0


def test_render_mermaid_without_cli_keeps_fence(tmp_path: Path, capsys) -> None:
    """Sem mmdc/npx, mantem o bloco e emite aviso."""
    with patch("app.md_converter._find_mermaid_cli", return_value=None):
        out, count = _render_mermaid_blocks(
            SAMPLE_MERMAID_MD,
            tmp_path / _MERMAID_WORKDIR_NAME,
        )
    assert "```mermaid" in out
    assert count == 0
    captured = capsys.readouterr()
    assert "AVISO" in captured.out
    assert "mmdc" in captured.out.lower() or "npx" in captured.out.lower()


def test_render_mermaid_replaces_with_image(tmp_path: Path) -> None:
    """Com CLI mockado, o bloco vira imagem Markdown relativa."""
    work = tmp_path / _MERMAID_WORKDIR_NAME

    def fake_run_mmdc(cli, input_mmd, output_png, timeout=180):
        output_png.parent.mkdir(parents=True, exist_ok=True)
        output_png.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    with patch("app.md_converter._find_mermaid_cli", return_value=["mmdc"]), patch(
        "app.md_converter._run_mmdc", side_effect=fake_run_mmdc
    ):
        out, count = _render_mermaid_blocks(SAMPLE_MERMAID_MD, work, verbose=False)

    assert count == 1
    assert "```mermaid" not in out
    assert f"![Diagrama Mermaid 1]({_MERMAID_WORKDIR_NAME}/mermaid-1.png)" in out
    assert (work / "mermaid-1.mmd").is_file()
    assert (work / "mermaid-1.png").is_file()


def test_render_mermaid_cli_failure_keeps_fence(tmp_path: Path, capsys) -> None:
    """Falha no CLI mantem o bloco original."""
    with patch("app.md_converter._find_mermaid_cli", return_value=["mmdc"]), patch(
        "app.md_converter._run_mmdc", side_effect=RuntimeError("boom")
    ):
        out, count = _render_mermaid_blocks(
            SAMPLE_MERMAID_MD,
            tmp_path / _MERMAID_WORKDIR_NAME,
        )
    assert count == 0
    assert "```mermaid" in out
    assert "AVISO" in capsys.readouterr().out


def test_find_mermaid_cli_prefers_mmdc() -> None:
    """Prefere mmdc quando disponivel no PATH."""
    with patch("app.md_converter.shutil.which") as which_mock:
        which_mock.side_effect = lambda name: (
            "C:\\tools\\mmdc.cmd" if name == "mmdc.cmd" else None
        )
        cli = _find_mermaid_cli()
    assert cli == ["C:\\tools\\mmdc.cmd"]


def test_find_mermaid_cli_falls_back_to_npx() -> None:
    """Sem mmdc, usa npx @mermaid-js/mermaid-cli."""
    with patch("app.md_converter.shutil.which") as which_mock:
        which_mock.side_effect = lambda name: (
            "C:\\nodejs\\npx.cmd" if name == "npx.cmd" else None
        )
        cli = _find_mermaid_cli()
    assert cli == ["C:\\nodejs\\npx.cmd", "--yes", "@mermaid-js/mermaid-cli"]


@pytest.mark.integration
def test_integration_mmdc_or_npx_if_available(tmp_path: Path) -> None:
    """Integração real com Mermaid CLI, se instalado no ambiente."""
    cli = _find_mermaid_cli()
    if cli is None:
        pytest.skip("mmdc/npx nao disponivel")

    work = tmp_path / _MERMAID_WORKDIR_NAME
    out, count = _render_mermaid_blocks(SAMPLE_MERMAID_MD, work, verbose=True)
    assert count == 1
    assert "```mermaid" not in out
    assert (work / "mermaid-1.png").is_file()
    assert (work / "mermaid-1.png").stat().st_size > 0
