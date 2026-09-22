@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencies
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.11 for Windows from python.org with the Python launcher enabled.
  echo Then double-click this file again.
  pause
  exit /b 1
)
py -3.11 -m venv ".venv"
if errorlevel 1 goto failed
:dependencies
if not exist ".venv\requirements-installed.txt" goto install
fc /b requirements.txt ".venv\requirements-installed.txt" >nul 2>&1
if errorlevel 1 goto install
".venv\Scripts\python.exe" -c "from importlib.metadata import version; [version(p) for p in ('PySide6', 'mss', 'numpy', 'ultralytics', 'torch')]" >nul 2>&1
if not errorlevel 1 goto launch
:install
echo First setup or changed requirements: installing dependencies. This can take a while.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
copy /y requirements.txt ".venv\requirements-installed.txt" >nul
if errorlevel 1 goto failed
:launch
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup or execution failed. Review the message above before retrying.
pause
exit /b 1
