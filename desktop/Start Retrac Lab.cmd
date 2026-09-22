@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem ============================================================
rem  Retrac Lab starter
rem  - Keeps the venv short enough for Windows MAX_PATH (260)
rem    because PySide6 ships very deep QML file paths.
rem ============================================================

set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"

rem --- Measure project path length ---------------------------------
set "LEN=0"
set "TMPSTR=%PROJ%"
:countloop
if defined TMPSTR (
  set "TMPSTR=!TMPSTR:~1!"
  set /a LEN+=1
  goto countloop
)

rem --- Pick venv location ------------------------------------------
rem Desktop\.venv is preferred; fall back to %LOCALAPPDATA% when the
rem project itself already sits on a long path.
set "VENV=%PROJ%\.venv"
set "VENV_MODE=project"
if %LEN% GTR 70 (
  set "VENV=%LOCALAPPDATA%\RetracLab\venv"
  set "VENV_MODE=localappdata"
  echo.
  echo [i] Project path is %LEN% characters long.
  echo [i] PySide6 needs deep paths, so the environment will live in:
  echo     !VENV!
  echo.
)

set "PYTHON=!VENV!\Scripts\python.exe"
set "STAMP=!VENV!\requirements-installed.txt"

rem --- Python 3.11 launcher ---------------------------------------
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.11 for Windows from python.org with the Python launcher enabled.
  echo Then double-click this file again.
  pause
  exit /b 1
)

rem --- Create venv if needed --------------------------------------
if exist "!PYTHON!" goto dependencies
echo Creating virtual environment in !VENV! ...
py -3.11 -m venv "!VENV!"
if errorlevel 1 goto failed

:dependencies
rem --- Install / refresh dependencies when requirements change ----
set "NEED_INSTALL="
if not exist "!STAMP!" set "NEED_INSTALL=1"
if defined NEED_INSTALL goto install
fc /b requirements.txt "!STAMP!" >nul 2>&1
if errorlevel 1 goto install
"!PYTHON!" -c "from importlib.metadata import version; [version(p) for p in ('PySide6', 'mss', 'numpy', 'ultralytics', 'torch')]" >nul 2>&1
if not errorlevel 1 goto launch

:install
echo First setup or changed requirements: installing dependencies. This can take a while.
echo If pip reports "No such file or directory" for a very long path, either:
echo   1^) Move this project to a short folder, e.g. C:\retrac
echo   2^) Enable Win32 long paths (Windows 11: Settings ^> System ^> For developers
echo      ^> Long paths; or set LongPathsEnabled=1 under
echo      HKLM\SYSTEM\CurrentControlSet\Control\FileSystem as admin)
echo.
"!PYTHON!" -m pip install --upgrade pip
if errorlevel 1 goto failed
"!PYTHON!" -m pip install -r requirements.txt
if errorlevel 1 goto failed
copy /y requirements.txt "!STAMP!" >nul
if errorlevel 1 goto failed

:launch
"!PYTHON!" main.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Setup or execution failed. Review the message above before retrying.
echo Tip: delete a broken venv folder, move the project to C:\retrac, run again.
pause
exit /b 1
