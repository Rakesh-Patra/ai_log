@echo off
setlocal
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist "venv_win\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv_win' not found in %cd%
    echo Please create it first or update this script.
    exit /b 1
)

:: Run the MCP server with UTF-8 encoding enforced
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
venv_win\Scripts\python.exe mcp_server.py %*
