# TCP Socket MCP Server

A Model Context Protocol (MCP) server that provides raw TCP socket access for AI models to interact with network services.

## Installation

```bash
# Add to Claude Desktop configuration
./add_to_claude.sh

# Or manually run
python run.py
```

## Quick Start for AI Models

### Basic Workflow

```python
# 1. Connect to a service
tcp_connect("example.com", 80) → returns connection_id

# 2. Send data (use hex for precise control)
tcp_send(connection_id, "474554202F", encoding="hex")  # GET /

# 3. Read response
tcp_read_buffer(connection_id) → returns received data

# 4. Close connection
tcp_disconnect(connection_id)
```

## Available Tools

### tcp_connect
Opens a TCP connection to any host:port
- Returns a connection_id for subsequent operations
- Supports custom connection_id for pre-registered triggers

### tcp_send  
Sends data over an established connection
- **Encoding options**: utf-8, hex (recommended), base64
- **Hex format**: Plain pairs like "48656C6C6F" for "Hello"
- **Terminator**: Optional hex suffix like "0D0A" for CRLF

### tcp_read_buffer
Reads received data from connection buffer
- Data may not be immediately available after sending
- Try multiple reads with small delays
- Supports index/count for partial reads

### tcp_set_trigger
Sets automatic responses for pattern matches
- **Pre-registration**: Can set triggers before connecting
- Supports regex patterns with capture groups ($1, $2)
- Response fires automatically when pattern matches

### tcp_connect_and_send
Combines connect + send for time-sensitive protocols
- Useful for immediate handshakes
- Returns connection_id for further operations

### Helper Tools
- **tcp_disconnect**: Close connection and free resources
- **tcp_list_connections**: List all active connections
- **tcp_connection_info**: Get detailed connection info
- **tcp_buffer_info**: Check buffer statistics
- **tcp_clear_buffer**: Clear received data
- **tcp_remove_trigger**: Remove auto-response trigger

## Important Usage Notes

### For Protocols with Line Endings (HTTP, SMTP, IRC)
**Use hex encoding to avoid JSON escape issues:**
```python
# Instead of struggling with \r\n in JSON:
tcp_send(conn_id, "GET / HTTP/1.1\r\n...")  # Can be problematic

# Use hex encoding:
tcp_send(conn_id, "474554202F20485454502F312E310D0A", encoding="hex")
```

### Common Hex Values
- `0D0A` = CRLF (\r\n) - Used by HTTP, SMTP, IRC
- `0A` = LF (\n) - Unix line ending  
- `00` = Null terminator - Binary protocols
- `20` = Space
- `0D0A0D0A` = Double CRLF - HTTP header end

### Pre-Registration for Immediate Handshakes
```python
# 1. Set trigger before connecting
tcp_set_trigger("my-conn", "ping-handler", "^PING", "PONG")

# 2. Connect - trigger auto-activates
tcp_connect("server.com", 6667, connection_id="my-conn")
```

## Example: HTTP Request

```python
# 1. Connect
conn_id = tcp_connect("httpbin.org", 80)

# 2. Send HTTP request (hex encoded for precise control)
request_hex = "474554202F676574204854..." # GET /get HTTP/1.1\r\nHost: httpbin.org\r\n\r\n
tcp_send(conn_id, request_hex, encoding="hex")

# 3. Read response (may need to wait/retry)
await sleep(1)
response = tcp_read_buffer(conn_id)

# 4. Clean up
tcp_disconnect(conn_id)
```

## License

MIT