@echo off
REM PDF-cli - Script batch para executar a ferramenta CLI de PDF
REM Este script facilita a execução do pdf-cli a partir de qualquer diretório
REM Uso: pdf.bat [comando] [opções]
REM Exemplo: pdf.bat extract documento.pdf -o textos.json

REM Obtém o diretório onde este script está localizado
set "SCRIPT_DIR=%~dp0"

REM Navega para o diretório do script
cd /d "%SCRIPT_DIR%"

REM Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Por favor, instale o Python 3.8 ou superior.
    pause
    exit /b 1
)

REM Verifica se o arquivo pdf_cli.py existe
if not exist "src\pdf_cli.py" (
    echo [ERRO] Arquivo src\pdf_cli.py nao encontrado.
    echo Certifique-se de que voce esta no diretorio raiz do projeto.
    pause
    exit /b 1
)

REM Executa o pdf_cli.py com todos os parâmetros passados pelo usuário
python "src\pdf_cli.py" %*

REM Captura o código de saída
set EXIT_CODE=%errorlevel%

REM Se houver erro, exibe mensagem (comente a linha pause se não quiser pausar)
if %EXIT_CODE% neq 0 (
    echo.
    echo [ERRO] Comando falhou com codigo de saida: %EXIT_CODE%
)

REM Retorna o código de saída para quem chamou o script
exit /b %EXIT_CODE%
