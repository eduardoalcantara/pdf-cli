"""
Sistema de logging de operações para PDF-cli.

Este módulo implementa o sistema de logs detalhados em formato JSON
conforme especificação da Fase 3. Todos os logs incluem IDs únicos,
tipos de operação, parâmetros, resultados, timestamps e notas.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid


class OperationLogger:
    """
    Logger para operações do PDF-cli.

    Gera logs em formato JSON detalhados para cada operação realizada,
    incluindo IDs únicos, timestamps, parâmetros e resultados.
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        Inicializa o logger.

        Args:
            log_dir: Diretório para salvar logs. Se None, usa ./logs.
        """
        if log_dir is None:
            log_dir = "./logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def create_operation_log(
        self,
        operation_type: str,
        operation_id: Optional[str] = None,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        status: str = "success",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um log de operação completo.

        Args:
            operation_type: Tipo da operação (ex: "export-objects", "edit-text").
            operation_id: ID único da operação (gerado se None).
            input_file: Arquivo de entrada.
            output_file: Arquivo de saída.
            parameters: Parâmetros utilizados na operação.
            result: Resultado da operação (contadores, IDs criados, etc.).
            notes: Notas adicionais sobre a operação.
            status: Status da operação ("success" ou "error").
            error: Mensagem de erro se status for "error".

        Returns:
            dict: Log completo da operação.
        """
        if operation_id is None:
            operation_id = str(uuid.uuid4())

        log = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": status,
            "input_file": input_file,
            "output_file": output_file,
            "parameters": parameters or {},
            "result": result or {},
        }

        if notes:
            log["notes"] = notes

        if error:
            log["error"] = error

        return log

    def save_log(self, log: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Salva um log em arquivo JSON.

        Args:
            log: Dicionário do log a ser salvo.
            filename: Nome do arquivo. Se None, usa timestamp + operation_type.

        Returns:
            str: Caminho do arquivo de log criado.
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            operation_type = log.get("operation_type", "unknown")
            filename = f"{timestamp}_{operation_type}_{log.get('operation_id', '')[:8]}.json"

        log_path = self.log_dir / filename

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

        return str(log_path)

    def log_operation(
        self,
        operation_type: str,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        status: str = "success",
        error: Optional[str] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Cria e salva um log de operação (método conveniente).

        Args:
            operation_type: Tipo da operação.
            input_file: Arquivo de entrada.
            output_file: Arquivo de saída.
            parameters: Parâmetros utilizados.
            result: Resultado da operação.
            notes: Notas adicionais.
            status: Status ("success" ou "error").
            error: Mensagem de erro.
            save: Se True, salva o log em arquivo.

        Returns:
            dict: Log criado.
        """
        log = self.create_operation_log(
            operation_type=operation_type,
            input_file=input_file,
            output_file=output_file,
            parameters=parameters,
            result=result,
            notes=notes,
            status=status,
            error=error
        )

        if save:
            log_path = self.save_log(log)
            log["log_file"] = log_path

        return log


# Instância global do logger
_default_logger: Optional[OperationLogger] = None


def get_logger(log_dir: Optional[str] = None) -> OperationLogger:
    """
    Retorna instância do logger (singleton).

    Args:
        log_dir: Diretório de logs (usado apenas na primeira chamada).

    Returns:
        OperationLogger: Instância do logger.
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = OperationLogger(log_dir)
    return _default_logger
