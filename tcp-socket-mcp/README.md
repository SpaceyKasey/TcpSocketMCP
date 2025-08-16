# TCP Socket MCP Server

A Model Context Protocol (MCP) server that provides raw TCP socket access with buffer management and trigger capabilities.

## Features

- **Multiple TCP Connections**: Open and manage multiple simultaneous TCP connections
- **Raw Data Transmission**: Send and receive raw binary or text data
- **Buffer Management**: Store received data in buffers with indexed access
- **Trigger System**: Set up automatic responses when specific patterns are received
- **Full Connection Control**: Connect, disconnect, and monitor connection status
- **MCP Inspector Compatible**: Fully debuggable with MCP Inspector

## Installation

```bash
# Clone the repository
git clone <repository_url>
cd tcp-socket-mcp

# Option 1: Use directly without installation (RECOMMENDED)
# Just use the run.py script - no installation needed!

# Option 2: Install in development mode (optional)
pip install -e .
```

## Usage

### Running the Server - 3 Methods

#### Method 1: Direct Script (RECOMMENDED)
```bash
# Navigate to the project directory
cd tcp-socket-mcp

# Run with MCP Inspector
mcp-inspector python run.py
```

#### Method 2: Shell Script
```bash
# Navigate to the project directory
cd tcp-socket-mcp

# Run the provided shell script
./run_with_inspector.sh
```

#### Method 3: After Installation
```bash
# Only if you installed with pip install -e .
mcp-inspector tcp-socket-mcp
```

### Using with MCP Inspector

1. Install MCP Inspector if you haven't already:
```bash
npm install -g @modelcontextprotocol/inspector
```

2. Run MCP Inspector with the TCP Socket server:
```bash
# From the tcp-socket-mcp directory
mcp-inspector python run.py
```

3. The inspector will open in your browser, allowing you to interact with all the TCP socket tools.

### Available Tools

#### `tcp_connect`
Open a new TCP connection to a specified host and port.

**Parameters:**
- `host` (string, required): Target host address
- `port` (integer, required): Target port number
- `connection_id` (string, optional): Custom connection ID (auto-generated if not provided)

**Example:**
```json
{
  "host": "example.com",
  "port": 80,
  "connection_id": "web-conn-1"
}
```

#### `tcp_disconnect`
Close an existing TCP connection.

**Parameters:**
- `connection_id` (string, required): Connection ID to close

#### `tcp_send`
Send raw data over a TCP connection.

**Parameters:**
- `connection_id` (string, required): Connection ID
- `data` (string, required): Data to send (supports hex escapes with \xNN format)
- `encoding` (string, optional): "utf-8", "base64", or "hex" (default: "utf-8")
- `terminator` (string, optional): Hex-formatted terminator bytes to append (e.g., "\x0d\x0a" for CRLF)

**Examples:**
```json
// UTF-8 text
{
  "connection_id": "web-conn-1",
  "data": "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n",
  "encoding": "utf-8"
}

// Binary data with hex encoding
{
  "connection_id": "binary-conn",
  "data": "\\x00\\x01\\x02\\x03\\xff\\xfe",
  "encoding": "hex"
}

// Mixed UTF-8 and hex escapes
{
  "connection_id": "mixed-conn",
  "data": "Hello\\x00World\\x0d\\x0a",
  "encoding": "hex"
}

// With terminator for consistent line endings
{
  "connection_id": "proto-conn",
  "data": "COMMAND",
  "terminator": "\\x0d\\x0a"
}
```

#### `tcp_read_buffer`
Read data from a connection's buffer.

**Parameters:**
- `connection_id` (string, required): Connection ID
- `index` (integer, optional): Starting index in buffer
- `count` (integer, optional): Number of chunks to read
- `format` (string, optional): "utf-8", "hex", or "base64" (default: "utf-8")

**Example:**
```json
{
  "connection_id": "web-conn-1",
  "index": 0,
  "count": 10,
  "format": "utf-8"
}
```

#### `tcp_clear_buffer`
Clear all data from a connection's buffer.

**Parameters:**
- `connection_id` (string, required): Connection ID

#### `tcp_buffer_info`
Get information about a connection's buffer.

**Parameters:**
- `connection_id` (string, required): Connection ID

**Returns:**
- Number of chunks in buffer
- Total bytes in buffer
- Bytes sent/received statistics
- Connection status

#### `tcp_set_trigger`
Set up an automatic response when a pattern is received.

**Parameters:**
- `connection_id` (string, required): Connection ID
- `trigger_id` (string, required): Unique trigger identifier
- `pattern` (string, required): Regex pattern to match
- `response` (string, required): Response data to send when pattern matches
- `response_encoding` (string, optional): "utf-8", "base64", or "hex" (default: "utf-8")
- `response_terminator` (string, optional): Hex-formatted terminator bytes to append to response

**Examples:**
```json
// Text response
{
  "connection_id": "chat-conn",
  "trigger_id": "ping-pong",
  "pattern": "PING",
  "response": "PONG\r\n",
  "response_encoding": "utf-8"
}

// Binary response with hex encoding
{
  "connection_id": "binary-conn",
  "trigger_id": "ack",
  "pattern": "\\x01\\x00",
  "response": "\\x06\\x00\\x00\\x01",
  "response_encoding": "hex"
}
```

#### `tcp_remove_trigger`
Remove a trigger from a connection.

**Parameters:**
- `connection_id` (string, required): Connection ID
- `trigger_id` (string, required): Trigger ID to remove

#### `tcp_list_connections`
List all active TCP connections.

**Returns:**
- Total number of connections
- Details for each connection (ID, host, port, status, statistics)

#### `tcp_connection_info`
Get detailed information about a specific connection.

**Parameters:**
- `connection_id` (string, required): Connection ID

**Returns:**
- Connection details (host, port, status)
- Buffer statistics
- Active triggers
- Creation timestamp

## Example Use Cases

### 1. HTTP Request
```python
# Connect to web server
tcp_connect(host="example.com", port=80, connection_id="http-1")

# Send HTTP request
tcp_send(
    connection_id="http-1",
    data="GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
)

# Read response
tcp_read_buffer(connection_id="http-1", format="utf-8")

# Disconnect
tcp_disconnect(connection_id="http-1")
```

### 2. Chat Protocol with Auto-Response
```python
# Connect to chat server
tcp_connect(host="chat.example.com", port=6667, connection_id="chat")

# Set up auto-response for ping
tcp_set_trigger(
    connection_id="chat",
    trigger_id="ping-handler",
    pattern="PING :(.+)",
    response="PONG :$1\r\n"
)

# Send initial message
tcp_send(connection_id="chat", data="NICK bot\r\n")

# Read messages
tcp_read_buffer(connection_id="chat")
```

### 3. Binary Protocol
```python
# Connect to binary service
tcp_connect(host="binary.example.com", port=9000)

# Send binary data (base64 encoded)
tcp_send(
    connection_id="<auto-generated-id>",
    data="SGVsbG8gV29ybGQ=",
    encoding="base64"
)

# Read binary response
tcp_read_buffer(
    connection_id="<auto-generated-id>",
    format="base64"
)
```

## Architecture

The server consists of three main components:

1. **TCPConnection Class** (`connection.py`):
   - Manages individual TCP connections
   - Handles asynchronous read/write operations
   - Maintains buffer for received data
   - Implements trigger pattern matching

2. **TCPSocketServer Class** (`server.py`):
   - Implements MCP server interface
   - Manages multiple connections
   - Provides tool implementations
   - Handles data encoding/decoding

3. **Buffer Management**:
   - Data stored as list of byte chunks
   - Indexed access for partial reads
   - Automatic data accumulation from socket
   - Thread-safe operations

## Security Considerations

- **No Built-in Encryption**: This server provides raw TCP access. For secure connections, the protocol layer (e.g., TLS) must be implemented separately.
- **Pattern Matching**: Trigger patterns use regex, be careful with complex patterns that could cause performance issues.
- **Resource Management**: Each connection maintains its own buffer. Monitor memory usage with many connections or large data transfers.

## Development

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please visit the GitHub repository.