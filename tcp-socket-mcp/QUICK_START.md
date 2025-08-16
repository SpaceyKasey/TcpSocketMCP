# Quick Start Guide - TCP Socket MCP Server

## Installation & Running Options

You have **3 different ways** to run the TCP Socket MCP server:

### Option 1: Direct Python Script (Recommended for Testing)
```bash
# Navigate to the project directory
cd /Volumes/ExtraSpace\ External/Dev/TcpSocketMCP/tcp-socket-mcp

# Run with MCP Inspector
mcp-inspector python run.py
```

### Option 2: Using the Shell Script
```bash
# Navigate to the project directory
cd /Volumes/ExtraSpace\ External/Dev/TcpSocketMCP/tcp-socket-mcp

# Run the shell script
./run_with_inspector.sh
```

### Option 3: Install Package (For Development)
```bash
# Navigate to the project directory
cd /Volumes/ExtraSpace\ External/Dev/TcpSocketMCP/tcp-socket-mcp

# Install in development mode
pip install -e .

# Then run with MCP Inspector
mcp-inspector tcp-socket-mcp
```

## Testing the Server

### 1. Start the Echo Test Server (Optional)
In a separate terminal:
```bash
cd /Volumes/ExtraSpace\ External/Dev/TcpSocketMCP/tcp-socket-mcp
python example_usage.py echo
```
This starts an echo server on localhost:9999 for testing.

### 2. Run the MCP Server
Choose one of the options above to start the server with MCP Inspector.

### 3. Test with MCP Inspector
Once MCP Inspector opens in your browser:
1. You'll see all 10 TCP tools listed
2. Try connecting to the echo server:
   - Tool: `tcp_connect`
   - Parameters: `{"host": "localhost", "port": 9999}`
3. Send some data:
   - Tool: `tcp_send`
   - Parameters: `{"connection_id": "<your-connection-id>", "data": "Hello World!"}`
4. Read the response:
   - Tool: `tcp_read_buffer`
   - Parameters: `{"connection_id": "<your-connection-id>"}`

## Troubleshooting

### ModuleNotFoundError
If you get "ModuleNotFoundError: No module named 'tcp_socket_mcp'":
- Use `python run.py` instead of `python -m tcp_socket_mcp.server`
- Or install the package with `pip install -e .`

### Permission Denied
If you get permission denied for the scripts:
```bash
chmod +x run.py run_with_inspector.sh
```

### MCP Inspector Not Found
If MCP Inspector isn't installed:
```bash
npm install -g @modelcontextprotocol/inspector
```

## File Structure
```
tcp-socket-mcp/
├── run.py                 # Direct runner (USE THIS!)
├── run_with_inspector.sh  # Shell script runner
├── src/tcp_socket_mcp/    # Source code
├── example_usage.py       # Test echo server
└── test_server.py         # Basic tests
```