# ESPECIFICACOES-FASE-8-DIST-BUILD-EXECUTAVEIS.md

## Projeto: PDF-cli — Fase 8: Distribuição Portátil e Scripts de Build Cross-platform

**Objetivo Geral:**
Organizar a pasta `./dist` para distribuição dos executáveis stand-alone do PDF-cli em Windows e Linux, além de prover scripts automatizados para compilação utilizando PyInstaller (`--onefile`) para Windows e AppImage (via PyInstaller como pré-etapa) para Linux.

---

## ESTRUTURA DE PASTAS DE DISTRIBUIÇÃO

- `./dist`
  - `/windows` → Executável compilado para Windows (pdf-cli.exe)
  - `/linux` → AppImage compilado para Linux (pdf-cli-x86_64.AppImage)
  - README.txt → Explicação resumida sobre o funcionamento e execução dos binários

---

## SCRIPT DE BUILD PARA WINDOWS (`build_win.bat`)

```
@echo off
REM Script para compilar PDF-cli em executável Windows usando PyInstaller (--onefile)

REM Ative o ambiente virtual, se necessário, e instale dependências:
REM python -m venv .venv
REM .venv\Scripts\activate

REM Instale o PyInstaller:
pip install pyinstaller

REM Compile o executável:
pyinstaller --onefile --name pdf-cli main.py

REM (Opcional) Copie ícone personalizado:
REM --icon=icon.ico

REM Mova o executável para a pasta dist\windows:
move dist\pdf-cli.exe ..\dist\windows\pdf-cli.exe

echo PDF-cli Windows compilado com sucesso!
pause
```

---

## SCRIPT DE BUILD PARA LINUX (`build_linux.sh`)

```
#!/bin/bash

# ========= AVISO OBRIGATÓRIO ==========
# Este script DEVE ser executado DENTRO do WSL (Windows Subsystem for Linux)!
# Caminho do repositório: /mnt/d/proj/pdf-cli
# Resultado final será: /mnt/d/proj/pdf-cli/dist/linux/pdf-cli
# =======================================

set -e

# Verifique se está rodando no WSL
if ! grep -qEi "(microsoft|wsl)" /proc/version &> /dev/null ; then
  echo "Erro: Este script DEVE ser rodado DENTRO do WSL (Windows Subsystem for Linux)!"
  exit 1
fi

# Caminho obrigatório do repositório
REPO_PATH="/mnt/d/proj/pdf-cli"
cd "$REPO_PATH"

# Instale dependências mínimas do sistema
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git wget

# Atualize pip e instale PyInstaller se necessário
pip3 install --upgrade pip
pip3 install pyinstaller

# Limpe builds antigos, se existirem
rm -rf build dist AppDir || true

# Compile o executável standalone com PyInstaller
pyinstaller --onefile --name pdf-cli main.py

# Baixe o AppImage Tool
wget -O appimagetool-x86_64.AppImage https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Estruture a pasta AppDir para o binário
mkdir -p AppDir/usr/bin
cp dist/pdf-cli AppDir/usr/bin/

# Crie o arquivo .desktop
cat > AppDir/pdf-cli.desktop <<EOL
[Desktop Entry]
Type=Application
Name=PDF-cli
Exec=pdf-cli
Icon=pdf-cli
Categories=Utility;
EOL

# (Opcional) Adicione ícone PNG
# cp icon.png AppDir/

# Certifique-se que a pasta destino exista
mkdir -p dist/linux

# Gere AppImage e imediatamente renomeie para pdf-cli
./appimagetool-x86_64.AppImage AppDir dist/linux/pdf-cli-tmp.AppImage
mv dist/linux/pdf-cli-tmp.AppImage dist/linux/pdf-cli
chmod +x dist/linux/pdf-cli

echo "PDF-cli Linux executável criado: /mnt/d/proj/pdf-cli/dist/linux/pdf-cli"
echo "Para rodar: cd /mnt/d/proj/pdf-cli/dist/linux && chmod +x pdf-cli && ./pdf-cli --help"
```

---

## INSTRUÇÕES ADICIONAIS PARA O DESENVOLVEDOR

- **Certifique-se que o main.py seja o entrypoint do CLI.**
- Antes de distribuir, teste todos comandos em um ambiente limpo (máquina virtual ou fresh install).
- Inclua instruções de uso resumidas em README.txt dentro de cada pasta.
- Sempre inclua release notes com versões, dependências, data de build e hash dos binários para auditoria.

---

**Checklist de Entrega**
- Pasta `dist/windows/` com pdf-cli.exe testado e funcional.
- Pasta `dist/linux/` com pdf-cli-x86_64.AppImage testado e funcional.
- Scripts `build_win.bat` e `build_linux.sh` documentados, prontos para uso e versionados.
- README.txt resumido na raiz da pasta `dist/` explicando como rodar o binário.
- Logs de teste funcional anexados para auditoria final.

---

**Siga estas instruções sem atalhos, garantindo máxima portabilidade, facilidade e transparência na entrega!**
