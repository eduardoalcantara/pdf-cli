"""Script para executar testes em todos os PDFs do repositório."""
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

def run_test(pdf_name, search_term, new_content):
    """Executa teste de edição de texto em um PDF."""
    print(f"\n{'='*70}")
    print(f"Testando: {pdf_name}")
    print(f"Buscar: '{search_term}' → Substituir por: '{new_content}'")
    print(f"{'='*70}\n")

    input_pdf = f"examples/{pdf_name}"
    output_pdf = f"outputs/{pdf_name.replace('.pdf', '_test.pdf')}"

    # Executar com PyMuPDF
    cmd_pymupdf = [
        sys.executable, "src/pdf_cli.py", "edit-text",
        input_pdf, output_pdf,
        "--content", search_term,
        "--new-content", new_content,
        "--all-occurrences",
        "--prefer-engine", "pymupdf",
        "--force"
    ]

    print(">>> Executando com PyMuPDF...")
    result_pymupdf = subprocess.run(cmd_pymupdf, capture_output=True, text=True, encoding='utf-8')
    print(result_pymupdf.stdout)
    if result_pymupdf.stderr:
        print(f"ERRO: {result_pymupdf.stderr}")

    return result_pymupdf.returncode == 0, output_pdf

if __name__ == "__main__":
    pdfs = [
        ("boleto.pdf", "ALCANTARA", "ALCÂNTARA"),
        ("contracheque.pdf", "R$", "R$"),  # Substituição simples para teste
        ("demonstrativo.pdf", "Total", "Total"),  # Teste básico
        ("despacho.pdf", "DESPACHO", "DESPACHO"),  # Teste básico
        ("orçamento.pdf", "Orçamento", "Orçamento"),  # Teste básico
    ]

    results = []
    for pdf_name, search_term, new_content in pdfs:
        if Path(f"examples/{pdf_name}").exists():
            success, output = run_test(pdf_name, search_term, new_content)
            results.append({
                "pdf": pdf_name,
                "search_term": search_term,
                "new_content": new_content,
                "success": success,
                "output": output
            })
        else:
            print(f"\n⚠️  PDF não encontrado: examples/{pdf_name}")

    # Salvar resultados
    results_file = f"logs/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path("logs").mkdir(exist_ok=True)
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Resumo dos Testes")
    print(f"{'='*70}")
    for r in results:
        status = "✓" if r['success'] else "✗"
        print(f"{status} {r['pdf']}: {r['search_term']} → {r['new_content']}")
    print(f"\nResultados salvos em: {results_file}")
