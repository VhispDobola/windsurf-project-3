@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Boss Rush LAN Multiplayer Launcher
color 0B

echo.
echo  ================================================
echo             BOSS RUSH LAN MULTIPLAYER
echo  ================================================
echo.

set PYTHON_CMD=

REM Prefer local Python 3.12 install path
"%LOCALAPPDATA%\Python312\python.exe" --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD="%LOCALAPPDATA%\Python312\python.exe"
)

REM Fallback to system Python
if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
    )
)

if not defined PYTHON_CMD (
    echo  Python not found. Install Python 3.10+ and retry.
    pause
    exit /b 1
)

echo  Using: %PYTHON_CMD%
echo  Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt --user >nul 2>&1
if errorlevel 1 (
    echo  Dependency install failed. Check internet access and pip.
    pause
    exit /b 1
)

echo.
echo  Choose mode:
echo    1) Host (Player 1 on this PC)
echo    2) Client Player 2
echo    3) Client Player 3
echo    4) Client Player 4
echo.
set /p MODE_CHOICE=Enter choice (1-4): 

if "%MODE_CHOICE%"=="1" goto :host
if "%MODE_CHOICE%"=="2" goto :client2
if "%MODE_CHOICE%"=="3" goto :client3
if "%MODE_CHOICE%"=="4" goto :client4

echo  Invalid choice.
pause
exit /b 1

:host
set /p HOST_BIND=Host bind IP [0.0.0.0]: 
if "%HOST_BIND%"=="" set HOST_BIND=0.0.0.0
set /p HOST_PORT=Port [50000]: 
if "%HOST_PORT%"=="" set HOST_PORT=50000

set BOSS_RUSH_NETWORK_MODE=host
set BOSS_RUSH_HOST=%HOST_BIND%
set BOSS_RUSH_PORT=%HOST_PORT%
set BOSS_RUSH_PLAYERS=1

echo.
echo  Starting HOST on %BOSS_RUSH_HOST%:%BOSS_RUSH_PORT% with 4 players...
echo.
%PYTHON_CMD% main.py
goto :done

:client2
set SLOT=2
goto :client_common

:client3
set SLOT=3
goto :client_common

:client4
set SLOT=4
goto :client_common

:client_common
set /p SERVER_IP=Host LAN IP (example 192.168.1.20): 
if "%SERVER_IP%"=="" (
    echo  Host IP is required for client mode.
    pause
    exit /b 1
)
set /p SERVER_PORT=Port [50000]: 
if "%SERVER_PORT%"=="" set SERVER_PORT=50000

set BOSS_RUSH_NETWORK_MODE=client
set BOSS_RUSH_HOST=%SERVER_IP%
set BOSS_RUSH_PORT=%SERVER_PORT%
set BOSS_RUSH_PLAYER_SLOT=%SLOT%

echo.
echo  Starting CLIENT slot %BOSS_RUSH_PLAYER_SLOT% to %BOSS_RUSH_HOST%:%BOSS_RUSH_PORT%...
echo.
%PYTHON_CMD% main.py

:done
echo.
echo  Session ended.
pause
endlocal
