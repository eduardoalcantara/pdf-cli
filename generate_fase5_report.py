"""Script para gerar relatório completo da Fase 5."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def generate_report():
    """Gera relatório completo de auditoria da Fase 5."""

    # Coletar todos os logs
    log_files = sorted(Path("logs").glob("audit_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    report = {
        "data_relatorio": datetime.now().isoformat(),
        "versao": "0.5.0 (Fase 5)",
        "total_testes": len(log_files),
        "testes": []
    }

    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            log = json.load(f)

        test_info = {
            "arquivo_pdf": Path(log['input_file']).name,
            "caminho_completo": log['input_file'],
            "arquivo_saida": Path(log['output_file']).name,
            "timestamp": log.get('timestamp', ''),
            "operation_id": log.get('operation_id', ''),
            "engine_final": log.get('final_engine_used', ''),
            "fallback_detectado": log.get('any_font_fallback', False),
            "preservacao_fonte": log.get('font_preservation_success', False),
            "tentativas_engine": len(log.get('engine_attempts', [])),
            "detalhes_tentativas": []
        }

        for attempt in log.get('engine_attempts', []):
            test_info["detalhes_tentativas"].append({
                "engine": attempt.get('engine', ''),
                "sucesso": attempt.get('success', False),
                "fallback_detectado": attempt.get('any_font_fallback', False),
                "tempo_execucao_ms": attempt.get('execution_time_ms', 0),
                "erro": attempt.get('error', None),
                "comparacoes_fonte": len(attempt.get('font_comparisons', []))
            })

        report["testes"].append(test_info)

    # Salvar relatório
    report_file = Path("results") / f"FASE-5-RELATORIO-FONTS-REAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Gerar também em formato Markdown
    md_file = Path("results") / f"FASE-5-RELATORIO-FONTS-REAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# Relatório de Auditoria - Fase 5: Preservação de Fontes\n\n")
        f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Versão:** 0.5.0 (Fase 5)\n")
        f.write(f"**Total de Testes:** {len(log_files)}\n\n")
        f.write("---\n\n")

        f.write("## Resumo Executivo\n\n")
        total_com_fallback = sum(1 for t in report["testes"] if t["fallback_detectado"])
        total_preservados = sum(1 for t in report["testes"] if t["preservacao_fonte"])
        f.write(f"- **Testes realizados:** {len(log_files)}\n")
        f.write(f"- **Fallback detectado:** {total_com_fallback}\n")
        f.write(f"- **Fontes preservadas:** {total_preservados}\n")
        f.write(f"- **Taxa de preservação:** {(total_preservados/len(log_files)*100):.1f}%\n\n")

        f.write("---\n\n")
        f.write("## Detalhes dos Testes\n\n")

        for i, test in enumerate(report["testes"], 1):
            f.write(f"### Teste {i}: {test['arquivo_pdf']}\n\n")
            f.write(f"- **Arquivo de entrada:** `{test['caminho_completo']}`\n")
            f.write(f"- **Arquivo de saída:** `{test['arquivo_saida']}`\n")
            f.write(f"- **Engine final:** `{test['engine_final']}`\n")
            f.write(f"- **Fallback detectado:** {'⚠️ Sim' if test['fallback_detectado'] else '✓ Não'}\n")
            f.write(f"- **Preservação de fonte:** {'✓ Sim' if test['preservacao_fonte'] else '⚠️ Não'}\n")
            f.write(f"- **Tentativas de engine:** {test['tentativas_engine']}\n\n")

            f.write("**Tentativas:**\n\n")
            for j, attempt in enumerate(test["detalhes_tentativas"], 1):
                f.write(f"{j}. **{attempt['engine']}**\n")
                f.write(f"   - Sucesso: {'✓' if attempt['sucesso'] else '✗'}\n")
                f.write(f"   - Fallback: {'⚠️ Sim' if attempt['fallback_detectado'] else '✓ Não'}\n")
                f.write(f"   - Tempo: {attempt['tempo_execucao_ms']:.2f}ms\n")
                if attempt['erro']:
                    f.write(f"   - Erro: {attempt['erro'][:100]}...\n")
                f.write(f"   - Comparações de fonte: {attempt['comparacoes_fonte']}\n\n")
            f.write("---\n\n")

        f.write("## Conclusões\n\n")
        f.write("### Problemas Identificados\n\n")
        if total_com_fallback > 0:
            f.write(f"- ⚠️ **{total_com_fallback} teste(s) detectaram fallback de fonte**\n")
            f.write("  - Fontes originais foram substituídas por fontes padrão (Helvetica)\n")
            f.write("  - O fallback automático para pypdf deveria ter sido acionado\n\n")

        f.write("### Próximos Passos\n\n")
        f.write("1. Investigar por que o fallback automático não está sendo acionado\n")
        f.write("2. Verificar se a detecção de fallback está comparando corretamente os objetos\n")
        f.write("3. Testar a implementação do pypdf com preservação de especificações de fonte (/F1, /F2, etc.)\n")
        f.write("4. Validar que o pypdf realmente preserva as fontes quando usado corretamente\n\n")

    print(f"✓ Relatório JSON salvo em: {report_file}")
    print(f"✓ Relatório Markdown salvo em: {md_file}")

    return report_file, md_file

if __name__ == "__main__":
    generate_report()
