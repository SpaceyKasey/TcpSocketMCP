#!/bin/bash

# Add TCP Socket MCP server to Claude Desktop

echo "Adding TCP Socket MCP server to Claude Desktop configuration..."

# Get the current directory
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"

# The config file location for Claude Desktop on macOS
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Create the config directory if it doesn't exist
mkdir -p "$(dirname "$CONFIG_FILE")"

# Check if config file exists, if not create it with basic structure
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating new Claude Desktop config file..."
    cat > "$CONFIG_FILE" << 'EOF'
{
  "mcpServers": {}
}
EOF
fi

# Create a Python script to update the JSON properly
cat > /tmp/update_claude_config.py << EOF
import json
import sys

config_file = "$CONFIG_FILE"
current_dir = "$CURRENT_DIR"

# Read existing config
with open(config_file, 'r') as f:
    config = json.load(f)

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add or update the TCP Socket MCP server
config['mcpServers']['tcp-socket'] = {
    "command": "python",
    "args": [f"{current_dir}/run.py"],
    "env": {}
}

# Write back the config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("Successfully added TCP Socket MCP server to Claude Desktop")
print(f"Server path: {current_dir}/run.py")
EOF

# Run the Python script
python3 /tmp/update_claude_config.py

# Clean up
rm /tmp/update_claude_config.py

echo ""
echo "Configuration complete!"
echo ""
echo "Next steps:"
echo "1. Quit Claude Desktop completely (Cmd+Q)"
echo "2. Restart Claude Desktop"
echo "3. Look for 'tcp-socket' in the MCP servers list (bottom of the screen)"
echo "4. The server should show as connected with 11 tools available"
echo ""
echo "To test the server:"
echo "- Try: 'Connect to example.com on port 80 and send an HTTP request'"
echo "- Or: 'List all TCP tools available'"