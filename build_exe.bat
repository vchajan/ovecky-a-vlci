@echo off
setlocal
cd /d "%~dp0"

echo Building Sheep Defender...
echo.

where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python was not found. Install Python 3.12 or newer and try again.
        goto :error
    )
    set "PYTHON_CMD=python"
) else (
    set "PYTHON_CMD=py"
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installing runtime requirements...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Installing build requirements...
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo Generating spritesheets...
python tools\generate_spritesheets.py
if errorlevel 1 goto :error

echo Generating sounds...
python tools\generate_sounds.py
if errorlevel 1 goto :error

echo Cleaning previous build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec.bak" del /q "*.spec.bak"

echo Running checks...
python -m compileall .
if errorlevel 1 goto :error

python -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo Building one-file windowed executable...
python -m PyInstaller --noconfirm --clean SheepDefender.spec
if errorlevel 1 goto :error

if not exist "dist\SheepDefender.exe" goto :error

echo.
echo BUILD SUCCESSFUL
echo File: %CD%\dist\SheepDefender.exe
echo Double-click SheepDefender.exe to start the game.
pause
exit /b 0

:error
echo.
echo BUILD FAILED
pause
exit /b 1
