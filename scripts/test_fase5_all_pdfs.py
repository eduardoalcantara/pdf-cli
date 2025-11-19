"""
Script de teste para Fase 5 - Testa todos os PDFs do repositório

Este script executa operações de edição de texto em todos os PDFs do diretório examples/
e gera logs de auditoria completos conforme especificação da Fase 5.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.services import export_objects, edit_text
from app.pdf_repo import PDFRepository
from core.engine_manager import EngineManager, create_audit_log

# PDFs para testar
PDFS_TO_TEST = [
    "examples/boleto.pdf",
    "examples/contracheque.pdf",
    "examples/demonstrativo.pdf",
    "examples/despacho.pdf",
    "examples/orçamento.pdf"
]

# Criar diretórios de saída
outputs_dir = Path("outputs")
logs_dir = Path("logs")
outputs_dir.mkdir(exist_ok=True)
logs_dir.mkdir(exist_ok=True)

results = []

print("=" * 80)
print("TESTE FASE 5 - PRESERVAÇÃO DE FONTES")
print("=" * 80)
print()

for pdf_path in PDFS_TO_TEST:
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"⚠️  PDF não encontrado: {pdf_path}")
        continue

    print(f"\n{'='*80}")
    print(f"Processando: {pdf_path}")
    print(f"{'='*80}\n")

    pdf_name = pdf_file.stem

    try:
        # 1. Exportar objetos ANTES da edição
        before_json = outputs_dir / f"{pdf_name}_objects_before.json"
        print(f"1. Exportando objetos antes da edição...")
        before_stats = export_objects(
            pdf_path=str(pdf_file),
            output_path=str(before_json),
            types=["text"]
        )
        print(f"   ✓ Exportados {before_stats.get('total', 0)} objetos de texto")

        # 2. Identificar um texto para editar (buscar primeiro texto não vazio)
        with PDFRepository(str(pdf_file)) as repo:
            text_objects = repo.extract_text_objects()

        # Encontrar um texto adequado para teste
        test_text = None
        test_new_text = None

        for obj in text_objects:
            if obj.content and len(obj.content.strip()) > 3:
                # Usar parte do texto como search_term
                words = obj.content.strip().split()
                if len(words) > 0:
                    # Pegar primeira palavra com pelo menos 3 caracteres
                    for word in words:
                        if len(word) >= 3:
                            test_text = word
                            test_new_text = word + "_TEST"
                            break
                if test_text:
                    break

        if not test_text:
            print(f"   ⚠️  Nenhum texto adequado encontrado para teste. Pulando...")
            results.append({
                "pdf": pdf_path,
                "status": "skipped",
                "reason": "Nenhum texto adequado encontrado"
            })
            continue

        print(f"2. Texto selecionado para teste: '{test_text}' → '{test_new_text}'")

        # 3. Executar edição com PyMuPDF
        edited_pdf = outputs_dir / f"{pdf_name}_edited.pdf"
        print(f"3. Editando PDF com PyMuPDF...")

        try:
            # Configurar prefer_engine
            edit_text._prefer_engine = "pymupdf"

            result_path = edit_text(
                pdf_path=str(pdf_file),
                output_path=str(edited_pdf),
                content=test_text,
                new_content=test_new_text,
                all_occurrences=True,
                create_backup=False
            )
            print(f"   ✓ PDF editado: {result_path}")
        except Exception as e:
            print(f"   ✗ Erro ao editar: {str(e)}")
            results.append({
                "pdf": pdf_path,
                "status": "error",
                "error": str(e)
            })
            continue

        # 4. Exportar objetos DEPOIS da edição
        after_json = outputs_dir / f"{pdf_name}_objects_after.json"
        print(f"4. Exportando objetos depois da edição...")
        after_stats = export_objects(
            pdf_path=str(edited_pdf),
            output_path=str(after_json),
            types=["text"]
        )
        print(f"   ✓ Exportados {after_stats.get('total', 0)} objetos de texto")

        # 5. Analisar fontes antes/depois
        print(f"5. Analisando preservação de fontes...")

        # Carregar objetos antes
        with open(before_json, "r", encoding="utf-8") as f:
            before_data = json.load(f)

        # Carregar objetos depois
        with open(after_json, "r", encoding="utf-8") as f:
            after_data = json.load(f)

        # Comparar fontes dos objetos modificados
        font_changes = []
        before_objects = {obj["id"]: obj for obj in before_data.get("objects", {}).get("text", [])}
        after_objects = {obj["id"]: obj for obj in after_data.get("objects", {}).get("text", [])}

        for obj_id, before_obj in before_objects.items():
            if test_text in before_obj.get("content", ""):
                after_obj = after_objects.get(obj_id)
                if after_obj:
                    before_font = before_obj.get("font_name", "")
                    after_font = after_obj.get("font_name", "")

                    font_changed = before_font != after_font
                    font_changes.append({
                        "id": obj_id,
                        "content_before": before_obj.get("content", ""),
                        "content_after": after_obj.get("content", ""),
                        "font_before": before_font,
                        "font_after": after_font,
                        "font_changed": font_changed
                    })

        # 6. Verificar logs de auditoria
        audit_logs = list(logs_dir.glob(f"audit_*{pdf_name}*.json"))
        if not audit_logs:
            # Buscar logs mais recentes
            audit_logs = sorted(logs_dir.glob("audit_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:1]

        audit_data = None
        if audit_logs:
            with open(audit_logs[0], "r", encoding="utf-8") as f:
                audit_data = json.load(f)
            print(f"   ✓ Log de auditoria encontrado: {audit_logs[0].name}")

        # Resumo
        fallback_count = sum(1 for fc in font_changes if fc["font_changed"])
        preserved_count = len(font_changes) - fallback_count

        print(f"\n   Resumo:")
        print(f"   - Objetos modificados: {len(font_changes)}")
        print(f"   - Fontes preservadas: {preserved_count}")
        print(f"   - Fallbacks detectados: {fallback_count}")

        results.append({
            "pdf": pdf_path,
            "status": "success",
            "test_text": test_text,
            "test_new_text": test_new_text,
            "objects_before": before_stats.get("total", 0),
            "objects_after": after_stats.get("total", 0),
            "font_changes": font_changes,
            "fallback_count": fallback_count,
            "preserved_count": preserved_count,
            "audit_log": audit_logs[0].name if audit_logs else None
        })

    except Exception as e:
        print(f"   ✗ Erro geral: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append({
            "pdf": pdf_path,
            "status": "error",
            "error": str(e)
        })

# Salvar resultados
results_file = outputs_dir / "fase5_test_results.json"
with open(results_file, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "results": results
    }, f, ensure_ascii=False, indent=2)

print(f"\n{'='*80}")
print(f"TESTE CONCLUÍDO")
print(f"{'='*80}")
print(f"\nResultados salvos em: {results_file}")
print(f"\nResumo geral:")
for r in results:
    status_icon = "✓" if r["status"] == "success" else "✗" if r["status"] == "error" else "⚠"
    print(f"  {status_icon} {Path(r['pdf']).name}: {r['status']}")
    if r["status"] == "success":
        print(f"     Fallbacks: {r.get('fallback_count', 0)}/{r.get('preserved_count', 0) + r.get('fallback_count', 0)}")
