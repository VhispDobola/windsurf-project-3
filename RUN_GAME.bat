@echo off
title Boss Rush Game
color 0A
echo.
echo  ========================================
echo         BOSS RUSH GAME
echo  ========================================
echo.

echo  Checking dependencies...

REM Try Python 3.12 first (preferred for pygame compatibility)
"%LOCALAPPDATA%\Python312\python.exe" --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD="%LOCALAPPDATA%\Python312\python.exe"
    goto :found_python
)

REM Fallback to system python
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found_python
)

echo  Python not found. Please install Python 3.12+ from python.org
pause
exit

:found_python
echo  Checking pygame...
%PYTHON_CMD% -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo  Installing pygame...
    %PYTHON_CMD% -m pip install pygame --user >nul 2>&1
    if errorlevel 1 (
        echo  Failed to install pygame.
        pause
        exit /b 1
    )
)

echo.
echo  Starting game...
echo.
%PYTHON_CMD% main.py

echo.
echo  Thanks for playing!
pause
