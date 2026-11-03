@echo off
rem Liga o sistema TNADV as centrais HTML do kit (ver docs\CENTRAIS.md).
rem Rode de novo sempre que o acervo mudar: so os dados sao atualizados.
rem Opcoes extras passam direto ao conector, por exemplo:
rem   CONECTAR_CENTRAIS_TNADV.bat --kit "C:\caminho\da\pasta\do\kit"
rem   CONECTAR_CENTRAIS_TNADV.bat --desconectar
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Python nao encontrado. Instale pelo site python.org, marcando
  echo a opcao "Add python.exe to PATH", e rode este arquivo de novo.
  pause
  exit /b 1
)
%PY% tools\conectar_centrais.py --abrir %*
echo.
pause
