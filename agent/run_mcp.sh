#!/bin/bash
# run_mcp.sh - Starts the Kubernetes AI Agent MCP Server (Linux/Mac)

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if a virtual environment exists
# Check for both "venv" (Linux/Mac default) and "venv_win" (in case of WSL)
if [ -d "venv" ]; then
    VENV_PYTHON="./venv/bin/python"
elif [ -d "venv_win" ]; then
    VENV_PYTHON="./venv_win/Scripts/python"
else
    echo "ERROR: Virtual environment not found in $DIR"
    exit 1
fi

# Run the MCP server
$VENV_PYTHON mcp_server.py "$@"
