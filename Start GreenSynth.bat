@echo off
setlocal EnableDelayedExpansion
title GreenSynth Launcher

:: ============================================================
::  GreenSynth Analytics Platform — One-Click Windows Launcher
:: ============================================================

echo ============================================================
echo   GREEN SYNTH ANALYTICS — DEVELOPMENT LAUNCHER
echo ============================================================
echo.

:: [1/7] Determine Root Directory
pushd "%~dp0"
set "ROOT_DIR=%CD%"
popd

set "BACKEND_DIR=%ROOT_DIR%\backend"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"

echo [1/7] Resolving project directories...
echo       Project Root : %ROOT_DIR%
echo       Backend Dir  : %BACKEND_DIR%
echo       Frontend Dir : %FRONTEND_DIR%
echo.

:: [2/7] Validate Directory Structure
if not exist "%BACKEND_DIR%" goto :err_no_backend
if not exist "%FRONTEND_DIR%" goto :err_no_frontend
if not exist "%BACKEND_DIR%\app\main.py" goto :err_no_main
if not exist "%FRONTEND_DIR%\package.json" goto :err_no_pkg

:: [3/7] Check Node.js and npm
echo [2/7] Checking Node.js and npm environment...
where node >nul 2>nul
if %errorlevel% neq 0 goto :err_no_node

where npm >nul 2>nul
if %errorlevel% neq 0 goto :err_no_npm

for /f "tokens=*" %%v in ('node -v 2^>nul') do set "NODE_VER=%%v"
for /f "tokens=*" %%v in ('npm -v 2^>nul') do set "NPM_VER=%%v"
echo       Node.js : !NODE_VER! [OK]
echo       npm     : !NPM_VER! [OK]
echo.

:: [4/7] Detect Python Environment
echo [3/7] Detecting Python environment...
set "PYTHON_EXE="

:: 1. Check backend\.venv
if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
    "%BACKEND_DIR%\.venv\Scripts\python.exe" -c "import fastapi, uvicorn" >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"
        echo       Found Python in backend\.venv
    )
)

:: 2. Check root .venv
if "!PYTHON_EXE!"=="" (
    if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
        "%ROOT_DIR%\.venv\Scripts\python.exe" -c "import fastapi, uvicorn" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
            echo       Found Python in root .venv
        )
    )
)

:: 3. Check system Python
if "!PYTHON_EXE!"=="" (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        python -c "import fastapi, uvicorn" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=python"
            echo       Found system Python with required packages
        )
    )
)

:: 4. Fallback if python exists in PATH
if "!PYTHON_EXE!"=="" (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo       Using system Python
    )
)

if "!PYTHON_EXE!"=="" goto :err_no_python

for /f "tokens=*" %%v in ('"%PYTHON_EXE%" --version 2^>nul') do set "PY_VER=%%v"
echo       Python  : !PY_VER! [OK]
echo.

:: [5/7] Check Environment & Frontend Dependencies
echo [4/7] Checking configuration and dependencies...

:: Ensure .env exists
if not exist "%ROOT_DIR%\.env" (
    if exist "%ROOT_DIR%\.env.example" (
        echo       Creating .env from .env.example for local development...
        copy "%ROOT_DIR%\.env.example" "%ROOT_DIR%\.env" >nul
    )
)

:: Check frontend node_modules
if not exist "%FRONTEND_DIR%\node_modules" (
    echo       Frontend dependencies not found. Running npm install...
    pushd "%FRONTEND_DIR%"
    call npm install
    if !errorlevel! neq 0 (
        popd
        goto :err_npm_install
    )
    popd
) else (
    echo       Frontend dependencies : OK [node_modules present]
)
echo.

:: [6/7] Start Backend Server
echo [5/7] Starting GreenSynth Backend [FastAPI on port 8000]...

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
if %errorlevel% equ 0 (
    echo       Backend port 8000 is already active. Checking health endpoint...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3; if ($r.status -eq 'healthy') { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>nul
    if !errorlevel! equ 0 (
        echo       GreenSynth Backend is already running and healthy.
    ) else (
        echo       [NOTE] Port 8000 is active. Proceeding with existing process.
    )
) else (
    start "GreenSynth Backend" cmd /k "title GreenSynth Backend && cd /d ""%BACKEND_DIR%"" && echo ============================================================ && echo   GREENSYNTH BACKEND [FastAPI on port 8000] && echo ============================================================ && ""%PYTHON_EXE%"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    
    echo       Waiting for backend to initialize...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "for ($i=0; $i -lt 20; $i++) { Start-Sleep -Seconds 1; try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2; if ($r.status -eq 'healthy') { exit 0 } } catch {} }; exit 1" >nul 2>nul
    if !errorlevel! equ 0 (
        echo       Backend started successfully [Healthy].
    ) else (
        echo       Backend start initiated.
    )
)
echo.

:: [7/7] Start Frontend Server & Open Browser
echo [6/7] Starting GreenSynth Frontend [Vite on port 5173]...

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>nul
if %errorlevel% equ 0 (
    echo       GreenSynth Frontend is already running on port 5173.
) else (
    start "GreenSynth Frontend" cmd /k "title GreenSynth Frontend && cd /d ""%FRONTEND_DIR%"" && echo ============================================================ && echo   GREENSYNTH FRONTEND [Vite + React on port 5173] && echo ============================================================ && npm run dev -- --host 127.0.0.1 --port 5173"
    
    echo       Waiting for frontend to initialize...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "for ($i=0; $i -lt 15; $i++) { Start-Sleep -Seconds 1; if (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue) { exit 0 } }; exit 0" >nul 2>nul
)
echo.

echo [7/7] Opening GreenSynth in default web browser...
start "" "http://localhost:5173"

echo.
echo ============================================================
echo   GREENSYNTH PLATFORM SUCCESSFULLY LAUNCHED!
echo ============================================================
echo.
echo   * Frontend UI    : http://localhost:5173
echo   * Backend API    : http://localhost:8000
echo   * API Docs       : http://localhost:8000/docs
echo   * Health Check   : http://localhost:8000/health
echo.
echo   To stop all GreenSynth services, double-click:
echo   Stop GreenSynth.bat
echo.
echo ============================================================
echo.
echo Press any key to close this launcher window (servers stay running in background)...
pause >nul
exit /b 0

:: Error Handlers
:err_no_backend
echo [ERROR] GreenSynth backend directory was not found.
echo         Expected location: %BACKEND_DIR%
echo.
pause
exit /b 1

:err_no_frontend
echo [ERROR] GreenSynth frontend directory was not found.
echo         Expected location: %FRONTEND_DIR%
echo.
pause
exit /b 1

:err_no_main
echo [ERROR] Backend entry point app\main.py was not found in:
echo         %BACKEND_DIR%
echo.
pause
exit /b 1

:err_no_pkg
echo [ERROR] Frontend package.json was not found in:
echo         %FRONTEND_DIR%
echo.
pause
exit /b 1

:err_no_node
echo [ERROR] Node.js is not installed or is not available in PATH.
echo         Please install Node.js 18+ from https://nodejs.org/
echo.
pause
exit /b 1

:err_no_npm
echo [ERROR] npm is not installed or is not available in PATH.
echo         Please install Node.js / npm from https://nodejs.org/
echo.
pause
exit /b 1

:err_no_python
echo [ERROR] Python is not installed or was not found in PATH or virtual environments.
echo         Please install Python 3.11+ from https://www.python.org/
echo.
pause
exit /b 1

:err_npm_install
echo [ERROR] npm install encountered an error in frontend directory.
echo.
pause
exit /b 1
