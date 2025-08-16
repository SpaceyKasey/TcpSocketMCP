#!/bin/bash
# Script to run TCP Socket MCP Server with MCP Inspector

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting TCP Socket MCP Server with MCP Inspector..."
echo "Directory: $DIR"
echo ""

# Check if mcp-inspector is installed
if ! command -v mcp-inspector &> /dev/null; then
    echo "MCP Inspector not found. Installing..."
    npm install -g @modelcontextprotocol/inspector
fi

# Run with the run.py script
echo "Running: mcp-inspector python $DIR/run.py"
mcp-inspector python "$DIR/run.py"