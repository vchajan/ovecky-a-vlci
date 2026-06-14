@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\SheepDefender.exe" (
    echo dist\SheepDefender.exe was not found.
    echo Run build_exe.bat first.
    pause
    exit /b 1
)

start "" "dist\SheepDefender.exe"
