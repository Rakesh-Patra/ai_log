@echo off
setlocal
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist "venv_win\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv_win' not found in %cd%
    echo Please create it first or update this script.
    exit /b 1
)

:: Run the MCP server
venv_win\Scripts\python.exe mcp_server.py %*
