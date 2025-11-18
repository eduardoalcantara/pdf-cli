"""
Testes de serialização/deserialização para todos os modelos da Fase 2.

Este script valida que todas as classes podem ser convertidas para JSON
e reconstruídas sem perda de dados.
"""

import json
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.models import (
    TextObject,
    ImageObject,
    TableObject,
    LinkObject,
    FormFieldObject,
    CheckboxFieldObject,
    RadioButtonFieldObject,
    SignatureFieldObject,
    LineObject,
    RectangleObject,
    EllipseObject,
    PolylineObject,
    BezierCurveObject,
    HighlightAnnotation,
    CommentAnnotation,
    MarkerAnnotation,
    LayerObject,
    FilterObject,
)


def test_text_object():
    """Testa serialização/deserialização de TextObject."""
    print("Testando TextObject...")
    original = TextObject(
        id="bd2e4742-1373-4a74-bf58-67ecbe537d5a",
        page=3,
        content="Relação de Inscritos",
        x=120.0,
        y=80.0,
        width=180.0,
        height=22.0,
        font_name="Times-New-Roman-Bold",
        font_size=18,
        color="#222222",
        align="center",
        rotation=0
    )
    json_data = original.to_dict()
    reconstructed = TextObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.content == reconstructed.content
    assert original.x == reconstructed.x
    print("  ✓ TextObject OK")


def test_image_object():
    """Testa serialização/deserialização de ImageObject."""
    print("Testando ImageObject...")
    original = ImageObject(
        id="img-18271c0e-9d04-4edd-abc1-022411da6e16",
        page=2,
        mime_type="image/png",
        x=135.0,
        y=220.0,
        width=120,
        height=64,
        data_base64="iVBORw0KGgoAAAANSU...AgAA",
        caption="Logo da empresa"
    )
    json_data = original.to_dict()
    reconstructed = ImageObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.mime_type == reconstructed.mime_type
    assert original.caption == reconstructed.caption
    print("  ✓ ImageObject OK")


def test_table_object():
    """Testa serialização/deserialização de TableObject."""
    print("Testando TableObject...")
    original = TableObject(
        id="tbl-7cbbdf10-f645-4a6b-89ef-cfdaad4b30c8",
        page=5,
        x=60.0,
        y=340.0,
        width=400.0,
        height=260.0,
        headers=["Nome", "Cargo", "Data"],
        rows=[
            ["Paulo", "Analista", "2025-11-11"],
            ["Ana", "Gerente", "2025-11-12"]
        ],
        cell_fonts=[
            {"row": 0, "col": 0, "font": "Arial", "size": 12, "color": "#333333"}
        ]
    )
    json_data = original.to_dict()
    reconstructed = TableObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.headers == reconstructed.headers
    assert len(original.rows) == len(reconstructed.rows)
    print("  ✓ TableObject OK")


def test_link_object():
    """Testa serialização/deserialização de LinkObject."""
    print("Testando LinkObject...")
    original = LinkObject(
        id="lnk-cfee1327-57cd-41cf-b286-621677293219",
        page=1,
        content="Clique aqui para acessar",
        x=490.5,
        y=98.0,
        width=180,
        height=22,
        font_name="Arial-Bold",
        font_size=12,
        color="#0055FF",
        url="https://meusite.com/docs"
    )
    json_data = original.to_dict()
    reconstructed = LinkObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.url == reconstructed.url
    print("  ✓ LinkObject OK")


def test_checkbox_field():
    """Testa serialização/deserialização de CheckboxFieldObject."""
    print("Testando CheckboxFieldObject...")
    original = CheckboxFieldObject(
        id="chk-4fbef488-92e2-4a70-bdee-252a34e46641",
        page=7,
        label="Aceito os termos",
        x=68.0,
        y=307.0,
        width=14.0,
        height=14.0,
        checked=True,
        required=True
    )
    json_data = original.to_dict()
    reconstructed = CheckboxFieldObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.checked == reconstructed.checked
    print("  ✓ CheckboxFieldObject OK")


def test_radio_button_field():
    """Testa serialização/deserialização de RadioButtonFieldObject."""
    print("Testando RadioButtonFieldObject...")
    original = RadioButtonFieldObject(
        id="rbn-0d12cafe-7183-4ca4-8636-1be0f5b4c318",
        page=7,
        group="tipousuario",
        label="Administrador",
        x=95.0,
        y=350.0,
        width=14.0,
        height=14.0,
        selected=False,
        options=["Administrador", "Usuário geral", "Visitante"]
    )
    json_data = original.to_dict()
    reconstructed = RadioButtonFieldObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.group == reconstructed.group
    assert original.options == reconstructed.options
    print("  ✓ RadioButtonFieldObject OK")


def test_signature_field():
    """Testa serialização/deserialização de SignatureFieldObject."""
    print("Testando SignatureFieldObject...")
    original = SignatureFieldObject(
        id="sig-6fbe425c-c875-4dc6-9fe3-9957ae73d1e2",
        page=9,
        label="Assinatura do responsável",
        x=130.0,
        y=540.0,
        width=200.0,
        height=28.0,
        signed=False,
        signer_name="",
        sign_time=None,
        border_color="#333333"
    )
    json_data = original.to_dict()
    reconstructed = SignatureFieldObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.signed == reconstructed.signed
    print("  ✓ SignatureFieldObject OK")


def test_line_object():
    """Testa serialização/deserialização de LineObject."""
    print("Testando LineObject...")
    original = LineObject(
        id="gfx-23208c92-e1c2-46db-99bf-a94721d1cc98",
        page=4,
        x1=42.0,
        y1=250.0,
        x2=412.0,
        y2=250.0,
        stroke_color="#FF0000",
        stroke_width=2.0
    )
    json_data = original.to_dict()
    reconstructed = LineObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.x1 == reconstructed.x1
    assert original.stroke_color == reconstructed.stroke_color
    print("  ✓ LineObject OK")


def test_rectangle_object():
    """Testa serialização/deserialização de RectangleObject."""
    print("Testando RectangleObject...")
    original = RectangleObject(
        id="gfx-23fdba92-9f76-433c-b91e-ddc77dda5bdf",
        page=4,
        x=80.0,
        y=110.0,
        width=130.0,
        height=60.0,
        fill_color="#F0F0F0",
        stroke_color="#222222",
        stroke_width=1.5
    )
    json_data = original.to_dict()
    reconstructed = RectangleObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.fill_color == reconstructed.fill_color
    print("  ✓ RectangleObject OK")


def test_ellipse_object():
    """Testa serialização/deserialização de EllipseObject."""
    print("Testando EllipseObject...")
    original = EllipseObject(
        id="gfx-2d317e3d-e208-4a36-b297-c6fbcdae9971",
        page=4,
        x=250.0,
        y=120.0,
        width=100.0,
        height=50.0,
        fill_color="#00FF00",
        stroke_color="#333333"
    )
    json_data = original.to_dict()
    reconstructed = EllipseObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.fill_color == reconstructed.fill_color
    print("  ✓ EllipseObject OK")


def test_polyline_object():
    """Testa serialização/deserialização de PolylineObject."""
    print("Testando PolylineObject...")
    original = PolylineObject(
        id="ply-94e73288-822e-4c7e-8479-670e52ddac18",
        page=2,
        points=[
            {"x": 60.0, "y": 100.0},
            {"x": 140.0, "y": 160.0},
            {"x": 320.0, "y": 120.0}
        ],
        stroke_color="#009900",
        stroke_width=1.0,
        closed=False
    )
    json_data = original.to_dict()
    reconstructed = PolylineObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert len(original.points) == len(reconstructed.points)
    print("  ✓ PolylineObject OK")


def test_bezier_curve_object():
    """Testa serialização/deserialização de BezierCurveObject."""
    print("Testando BezierCurveObject...")
    original = BezierCurveObject(
        id="bez-bbdb0908-3c55-4b70-bd2e-f821b5463b4f",
        page=5,
        start={"x": 60.0, "y": 240.0},
        control1={"x": 120.0, "y": 60.0},
        control2={"x": 180.0, "y": 340.0},
        end={"x": 220.0, "y": 240.0},
        stroke_color="#FF8800",
        stroke_width=2.0
    )
    json_data = original.to_dict()
    reconstructed = BezierCurveObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.start == reconstructed.start
    print("  ✓ BezierCurveObject OK")


def test_highlight_annotation():
    """Testa serialização/deserialização de HighlightAnnotation."""
    print("Testando HighlightAnnotation...")
    original = HighlightAnnotation(
        id="ann-6b1e512a-3c1d-46f3-b454-daec678d4db8",
        page=2,
        x=140.0,
        y=180.0,
        width=94.0,
        height=18.0,
        color="#FFFF00",
        comment="Este texto deve ser revisado"
    )
    json_data = original.to_dict()
    reconstructed = HighlightAnnotation.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.comment == reconstructed.comment
    print("  ✓ HighlightAnnotation OK")


def test_comment_annotation():
    """Testa serialização/deserialização de CommentAnnotation."""
    print("Testando CommentAnnotation...")
    original = CommentAnnotation(
        id="ann-681b712a-4e1c-46f3-b454-daec679d4dc6",
        page=3,
        x=320.0,
        y=420.0,
        content="Sugestão de mudança no valor deste item.",
        author="Gerente",
        date="2025-11-18T14:32:01Z"
    )
    json_data = original.to_dict()
    reconstructed = CommentAnnotation.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.author == reconstructed.author
    print("  ✓ CommentAnnotation OK")


def test_marker_annotation():
    """Testa serialização/deserialização de MarkerAnnotation."""
    print("Testando MarkerAnnotation...")
    original = MarkerAnnotation(
        id="ann-mark-001",
        page=1,
        x=100.0,
        y=200.0,
        width=50.0,
        height=50.0,
        color="#FF0000",
        marker_type="bookmark"
    )
    json_data = original.to_dict()
    reconstructed = MarkerAnnotation.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.marker_type == reconstructed.marker_type
    print("  ✓ MarkerAnnotation OK")


def test_layer_object():
    """Testa serialização/deserialização de LayerObject."""
    print("Testando LayerObject...")
    original = LayerObject(
        id="lyr-7dac8a46-17b8-44ff-8b23-8ad28a4b0c21",
        name="Marca d'água",
        visible=True,
        objects=[
            {
                "type": "text",
                "content": "CONFIDENCIAL",
                "x": 220.0,
                "y": 670.0,
                "font_size": 40,
                "font_name": "Arial-Bold",
                "color": "#CCCCCC",
                "rotation": 45
            }
        ]
    )
    json_data = original.to_dict()
    reconstructed = LayerObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.name == reconstructed.name
    assert len(original.objects) == len(reconstructed.objects)
    print("  ✓ LayerObject OK")


def test_filter_object():
    """Testa serialização/deserialização de FilterObject."""
    print("Testando FilterObject...")
    original = FilterObject(
        id="flt-1da2d5d6-c9b6-4a7e-9856-e1f2f4e3a3de",
        object_id="img-18271c0e-9d04-4edd-abc1-022411da6e16",
        filter_type="grayscale",
        params={"intensity": 0.8}
    )
    json_data = original.to_dict()
    reconstructed = FilterObject.from_dict(json_data)
    assert original.id == reconstructed.id
    assert original.filter_type == reconstructed.filter_type
    assert original.params == reconstructed.params
    print("  ✓ FilterObject OK")


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("Testes de Serialização/Deserialização - Fase 2")
    print("=" * 60)

    try:
        test_text_object()
        test_image_object()
        test_table_object()
        test_link_object()
        test_checkbox_field()
        test_radio_button_field()
        test_signature_field()
        test_line_object()
        test_rectangle_object()
        test_ellipse_object()
        test_polyline_object()
        test_bezier_curve_object()
        test_highlight_annotation()
        test_comment_annotation()
        test_marker_annotation()
        test_layer_object()
        test_filter_object()

        print("=" * 60)
        print("✓ Todos os testes passaram com sucesso!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
