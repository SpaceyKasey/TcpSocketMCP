# TCP Socket MCP Server

A Model Context Protocol (MCP) server that provides raw TCP socket access, enabling AI models to interact directly with network services using raw TCP Sockets.
Supports multiple concurrent connections, buffering of response data and triggering automatic responses.

## Motivation and Context
Many network services and IoT devices communicate via raw TCP protocols that aren't covered by existing HTTP-based MCP servers. TcpSocketMCP enables:

- Direct interaction with embedded devices and IoT systems
- Network protocol debugging and testing
- Legacy system integration without HTTP wrappers
- Protocol reverse engineering and analysis
- Automated responses via trigger patterns (useful for IRC, telnet, custom protocols)

This addresses the need for low-level network access that several community members have expressed, particularly for industrial automation, IoT development, and network security testing scenarios.

## Demo

![Demo 1](https://raw.githubusercontent.com/SpaceyKasey/TcpSocketMCP/main/assets/Demo1.gif)
*Interrogating a device to figure out what it is*

![Demo 2](https://raw.githubusercontent.com/SpaceyKasey/TcpSocketMCP/main/assets/Demo2.gif)
*Sending data to the device*

![Output Example](https://raw.githubusercontent.com/SpaceyKasey/TcpSocketMCP/main/assets/output.jpg)
*Sample output from TCP interactions*

## Installation & Setup

### Install from PyPI

```bash
# Install with pip
pip install TcpSocketMCP

# Install with uv (recommended)
uv add TcpSocketMCP

# Add to Claude Code (recommended)
claude mcp add rawtcp -- uvx TcpSocketMCP
```

### For Claude Desktop

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Option 1: Using installed package (recommended)
```json
{
  "mcpServers": {
    "tcp-socket": {
      "command": "TcpSocketMCP",
      "env": {}
    }
  }
}
```

#### Option 2: From source
```json
{
  "mcpServers": {
    "tcp-socket": {
      "command": "python",
      "args": ["/path/to/tcp-socket-mcp/run.py"],
      "env": {}
    }
  }
}
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/kaseyk/tcp-socket-mcp.git
cd tcp-socket-mcp

# Install with uv (recommended)
uv pip install -e .

# Or install with pip
pip install -e .

# Run the server directly
python run.py

# Or use the command
TcpSocketMCP
```

## Available Tools

Once configured via MCP, the following tools become available to the AI model:

### Core Connection Tools

#### tcp_connect
Opens a TCP connection to any host:port
- Returns a `connection_id` for subsequent operations
- Supports custom connection_id for pre-registered triggers
- Example: `tcp_connect("example.com", 80)`

#### tcp_send  
Sends data over an established connection
- **Encoding options**: `utf-8`, `hex` (recommended for binary), `base64`
- **Hex format**: Plain pairs like `"48656C6C6F"` for "Hello"
- **Terminator**: Optional hex suffix like `"0D0A"` for CRLF

#### tcp_read_buffer
Reads received data from connection buffer
- Data may not be immediately available after sending
- Buffer stores all received data until cleared
- Supports `index`/`count` for partial reads
- Format options: `utf-8`, `hex`, `base64`

#### tcp_disconnect
Closes connection and frees resources
- Always close connections when done
- All triggers automatically removed

### Advanced Features

#### tcp_set_trigger
Sets automatic responses for pattern matches
- **Pre-registration**: Set triggers before connecting for immediate activation
- Supports regex patterns with capture groups (`$1`, `$2`)
- Response fires automatically when pattern matches
- Perfect for protocol handshakes (IRC PING/PONG, etc.)

#### tcp_connect_and_send
Combines connect + send in one atomic operation
- Essential for time-sensitive protocols
- Useful for immediate handshakes or banner grabbing
- Returns connection_id for further operations

### Utility Tools

- **tcp_list_connections**: View all active connections with statistics
- **tcp_connection_info**: Get detailed info about specific connection
- **tcp_buffer_info**: Check buffer statistics without reading data
- **tcp_clear_buffer**: Clear received data from buffer
- **tcp_remove_trigger**: Remove specific auto-response trigger

## Usage Examples

### Basic TCP Communication

```python
# Connect to a service
conn_id = tcp_connect("example.com", 80)

# Send data (hex encoding recommended for protocols)
tcp_send(conn_id, "474554202F20485454502F312E310D0A", encoding="hex")  # GET / HTTP/1.1\r\n

# Read response (may need to wait for data)
response = tcp_read_buffer(conn_id)

# Clean up
tcp_disconnect(conn_id)
```

### Automated Protocol Handling

```python
# Pre-register trigger for IRC PING/PONG
tcp_set_trigger("irc-conn", "ping-handler", "^PING :(.+)", "PONG :$1\r\n")

# Connect with pre-registered triggers
tcp_connect("irc.server.com", 6667, connection_id="irc-conn")
# PING responses now happen automatically!
```

### Working with Binary Protocols

```python
# Use hex encoding for precise byte control
tcp_send(conn_id, "0001000400000001", encoding="hex")  # Binary protocol header

# Read response in hex for analysis
response = tcp_read_buffer(conn_id, format="hex")
```

## Important Notes

### Hex Encoding for Line Endings

Many text protocols (HTTP, SMTP, IRC) require specific line endings. Use hex encoding to avoid JSON escaping issues:

```python
# Common hex sequences:
# 0D0A     = \r\n (CRLF) - HTTP, SMTP, IRC
# 0A       = \n (LF) - Unix line ending
# 0D0A0D0A = \r\n\r\n - HTTP header terminator
# 00       = Null byte - Binary protocols
```

### Timing Considerations

- Network responses aren't instant - use `tcp_buffer_info` to check for data
- Consider implementing retry logic with small delays
- Buffer accumulates all received data - clear when needed

## License

MIT
