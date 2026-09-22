@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "LOG=%~dp0start-log.txt"
> "%LOG%" echo === Retrac Lab start ===
>>"%LOG%" echo Time: %DATE% %TIME%
>>"%LOG%" echo CWD:  %CD%

if not exist "%~dp0main.py" (
    echo.
    echo [FATAL] main.py nicht gefunden in:
    echo         %~dp0
    echo.
    echo Du startest vermutlich DIREKT AUS DER ZIP.
    echo 1^) ZIP komplett entpacken, z.B. nach C:\retrac
    echo 2^) Dann desktop\Start Retrac Lab.cmd starten
    echo.
    echo Log: %LOG%
    pause
    exit /b 1
)

if not exist "%~dp0requirements.txt" (
    echo [FATAL] requirements.txt fehlt - unvollstaendiger Ordner.
    pause
    exit /b 1
)

rem --- Kurzer Pfad erzwingen, wenn zu lang (PySide6 braucht MAX_PATH) ---
set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"
set "LEN=0"
set "TMPSTR=%PROJ%"
:countloop
if defined TMPSTR (
    set "TMPSTR=!TMPSTR:~1!"
    set /a LEN+=1
    goto countloop
)
>>"%LOG%" echo Path length: %LEN%

set "VENV=%PROJ%\.venv"
if %LEN% GTR 70 (
    set "VENV=%LOCALAPPDATA%\RetracLab\venv"
    echo.
    echo [i] Projekt-Pfad ist %LEN% Zeichen lang.
    echo [i] Umgebung wird in KURZ pfad installiert:
    echo     !VENV!
    echo.
    >>"%LOG%" echo Using LOCALAPPDATA venv: !VENV!
)

set "PYTHON=!VENV!\Scripts\python.exe"
set "STAMP=!VENV!\requirements-installed.txt"

rem --- Python 3.11 pruefen ---
py -3.11 --version >>"%LOG%" 2>&1
if errorlevel 1 (
    echo.
    echo [FATAL] Python 3.11 nicht gefunden (py -3.11 fehlt).
    echo Installiere Python 3.11 von python.org mit "py launcher".
    echo.
    echo Log: %LOG%
    pause
    exit /b 1
)

rem --- Venv anlegen ---
if exist "!PYTHON!" goto dependencies
echo Lege virtuelle Umgebung an: !VENV!
>>"%LOG%" echo Creating venv: !VENV!
py -3.11 -m venv "!VENV!" >>"%LOG%" 2>&1
if errorlevel 1 (
    echo.
    echo [FATAL] venv erstellen fehlgeschlagen - Log ansehen:
    echo   %LOG%
    echo Tipp: Projekt nach C:\retrac verschieben.
    pause
    exit /b 1
)

:dependencies
set "NEED_INSTALL="
if not exist "!STAMP!" set "NEED_INSTALL=1"
if defined NEED_INSTALL goto install
fc /b requirements.txt "!STAMP!" >nul 2>&1
if errorlevel 1 goto install
"!PYTHON!" -c "from importlib.metadata import version; [version(p) for p in ('PySide6','mss','numpy','ultralytics','torch')]" >>"%LOG%" 2>&1
if not errorlevel 1 goto launch

:install
echo.
echo Installiere Abhaengigkeiten (beim ersten Start dauert das mehrere Minuten)...
echo.
>>"%LOG%" echo pip install -r requirements.txt
"!PYTHON!" -m pip install --upgrade pip
if errorlevel 1 (
    echo [FATAL] pip upgrade fehlgeschlagen - Log: %LOG%
    pause
    exit /b 1
)
"!PYTHON!" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [FATAL] pip install fehlgeschlagen - Log ansehen:
    echo   %LOG%
    echo.
    echo Oefter: Pfad zu lang / Long Paths / Internet.
    echo Projekt am besten nach C:\retrac legen.
    pause
    exit /b 1
)
copy /y requirements.txt "!STAMP!" >nul
if errorlevel 1 (
    echo [FATAL] Stamp konnte nicht geschrieben werden: !STAMP!
    pause
    exit /b 1
)

:launch
echo Starte RETRAC...
>>"%LOG%" echo Launch: "!PYTHON!" main.py
"!PYTHON!" main.py
set "RC=%ERRORLEVEL%"
>>"%LOG%" echo Exit code: %RC%
if not "%RC%"=="0" (
    echo.
    echo [FATAL] Programm beendet mit Code %RC% - Log:
    echo   %LOG%
    echo.
    pause
    exit /b 1
)
exit /b 0
