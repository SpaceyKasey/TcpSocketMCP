# TCP Socket MCP Server - Model Guide

## Quick Start for AI Models

This server gives you direct TCP socket access to communicate with any network service. Think of it as your gateway to the internet's underlying protocols.

### What You Can Do

1. **Connect to any TCP service** - Web servers, databases, chat servers, IoT devices
2. **Send any data** - Text, binary, mixed formats with proper encoding
3. **Receive and buffer data** - Store responses for analysis
4. **Automate interactions** - Set triggers for automatic responses
5. **Handle multiple connections** - Manage many services simultaneously

### Basic Workflow

```
1. Connect → 2. Send Data → 3. Read Response → 4. Disconnect
```

### Essential Commands

#### Connect to a Service
```json
tcp_connect: {
  "host": "example.com",
  "port": 80
}
// Returns: connection_id to use in other commands
```

#### Send Data
```json
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "Hello World",
  "terminator": "\\x0d\\x0a"  // Optional CRLF
}
```

#### Read Response
```json
tcp_read_buffer: {
  "connection_id": "YOUR_ID"
}
```

#### Close Connection
```json
tcp_disconnect: {
  "connection_id": "YOUR_ID"
}
```

## Common Protocol Patterns

### HTTP Request Pattern
```json
// 1. Connect
tcp_connect: {"host": "api.example.com", "port": 80}

// 2. Send request with CRLF terminators
tcp_send: {"connection_id": "ID", "data": "GET /data HTTP/1.1", "terminator": "\\x0d\\x0a"}
tcp_send: {"connection_id": "ID", "data": "Host: api.example.com", "terminator": "\\x0d\\x0a"}
tcp_send: {"connection_id": "ID", "data": "", "terminator": "\\x0d\\x0a"}

// 3. Read response
tcp_read_buffer: {"connection_id": "ID"}
```

### Binary Protocol Pattern
```json
// 1. Connect
tcp_connect: {"host": "device.local", "port": 9000}

// 2. Send binary packet
tcp_send: {
  "connection_id": "ID",
  "data": "\\x01\\x00\\x00\\x10DATA",
  "encoding": "hex",
  "terminator": "\\xff\\xfe"
}

// 3. Read binary response
tcp_read_buffer: {"connection_id": "ID", "format": "hex"}
```

### Chat/Command Protocol Pattern
```json
// 1. Connect
tcp_connect: {"host": "chat.server.com", "port": 6667}

// 2. Set up auto-response for pings
tcp_set_trigger: {
  "connection_id": "ID",
  "trigger_id": "ping",
  "pattern": "PING :(.*)",
  "response": "PONG :$1",
  "response_terminator": "\\x0d\\x0a"
}

// 3. Send commands
tcp_send: {"connection_id": "ID", "data": "JOIN #channel", "terminator": "\\x0d\\x0a"}
```

## Data Encoding Guide

### Text Data (UTF-8)
Default encoding for normal text:
```json
{"data": "Hello World", "encoding": "utf-8"}
```

### Binary Data (Hex)
For binary protocols, use hex encoding:
```json
// Escaped hex format
{"data": "\\x01\\x02\\x03", "encoding": "hex"}

// Plain hex string
{"data": "010203", "encoding": "hex"}

// Mixed text and hex
{"data": "HELLO\\x00WORLD", "encoding": "hex"}
```

### Base64 Binary
Alternative binary encoding:
```json
{"data": "SGVsbG8gV29ybGQ=", "encoding": "base64"}
```

## Terminators Reference

Add these to ensure proper line endings:

| Protocol | Terminator | Usage |
|----------|------------|-------|
| HTTP/Telnet | `\\x0d\\x0a` | Most internet protocols |
| Unix/Linux | `\\x0a` | Unix commands |
| Null-terminated | `\\x00` | C strings, binary protocols |
| Custom | Any hex | Protocol-specific |

## Trigger System

Automate responses for common patterns:

### Simple Trigger
```json
tcp_set_trigger: {
  "connection_id": "ID",
  "trigger_id": "welcome",
  "pattern": "HELLO",
  "response": "Hi there!",
  "response_terminator": "\\x0d\\x0a"
}
```

### Regex Trigger with Capture
```json
tcp_set_trigger: {
  "connection_id": "ID",
  "trigger_id": "echo",
  "pattern": "ECHO: (.*)",
  "response": "You said: $1",
  "response_terminator": "\\x0d\\x0a"
}
```

### Binary Trigger
```json
tcp_set_trigger: {
  "connection_id": "ID",
  "trigger_id": "ack",
  "pattern": "\\x01\\x00",
  "response": "\\x06",
  "response_encoding": "hex"
}
```

## Multi-Connection Management

Handle multiple services simultaneously:

```json
// Connect to multiple services
tcp_connect: {"host": "service1.com", "port": 80, "connection_id": "web"}
tcp_connect: {"host": "service2.com", "port": 22, "connection_id": "ssh"}
tcp_connect: {"host": "localhost", "port": 3306, "connection_id": "db"}

// Send to different connections
tcp_send: {"connection_id": "web", "data": "GET /"}
tcp_send: {"connection_id": "db", "data": "SELECT 1"}

// List all connections
tcp_list_connections: {}
```

## Best Practices for Models

### 1. Always Store Connection IDs
```json
// Good: Store the ID
response = tcp_connect(...)
connection_id = response["connection_id"]

// Use it in subsequent calls
tcp_send({"connection_id": connection_id, ...})
```

### 2. Use Appropriate Encoding
- Text protocols → UTF-8
- Binary protocols → Hex or Base64
- Mixed data → Hex with escaped sequences

### 3. Add Terminators for Line Protocols
Most text protocols expect CRLF (`\\x0d\\x0a`):
```json
{"data": "COMMAND", "terminator": "\\x0d\\x0a"}
```

### 4. Read Buffer After Sending
Always check for responses:
```json
tcp_send: {...}
tcp_read_buffer: {"connection_id": "ID"}
```

### 5. Clean Up Connections
Always disconnect when done:
```json
tcp_disconnect: {"connection_id": "ID"}
```

### 6. Use Triggers for Repetitive Responses
Instead of manually responding to each PING:
```json
tcp_set_trigger: {
  "pattern": "PING",
  "response": "PONG"
}
```

## Common Protocols Quick Reference

### Web (HTTP/HTTPS)
- Port: 80 (HTTP), 443 (HTTPS)
- Terminator: `\\x0d\\x0a`
- Example: `GET / HTTP/1.1\\r\\nHost: example.com\\r\\n\\r\\n`

### Email (SMTP)
- Port: 25, 587, 465
- Terminator: `\\x0d\\x0a`
- Example: `HELO client\\r\\n`

### Chat (IRC)
- Port: 6667, 6697 (SSL)
- Terminator: `\\x0d\\x0a`
- Example: `NICK bot\\r\\n`

### Database (MySQL)
- Port: 3306
- Binary protocol with varied terminators
- Use hex encoding

### SSH/Telnet
- Port: 22 (SSH), 23 (Telnet)
- Terminator: `\\x0d\\x0a`
- Complex protocols requiring handshakes

### Custom/IoT
- Varies by device
- Often binary with custom terminators
- Check device documentation

## Debugging Tips

### 1. Check Connection Status
```json
tcp_connection_info: {"connection_id": "ID"}
```

### 2. View Buffer in Hex
For binary protocols:
```json
tcp_read_buffer: {"connection_id": "ID", "format": "hex"}
```

### 3. Monitor Buffer Growth
```json
tcp_buffer_info: {"connection_id": "ID"}
```

### 4. Clear Old Data
```json
tcp_clear_buffer: {"connection_id": "ID"}
```

### 5. List All Connections
```json
tcp_list_connections: {}
```

## Error Handling

Common errors and solutions:

### Connection Refused
- Check host and port are correct
- Verify service is running
- Check firewall rules

### No Response
- Add proper terminator
- Check encoding is correct
- Verify protocol requirements

### Binary Data Issues
- Use hex or base64 encoding
- Check byte order (endianness)
- Verify terminator format

### Trigger Not Working
- Verify regex pattern
- Check trigger_id is unique
- Test pattern separately

## Advanced Usage

### State Machine with Triggers
```json
// State 1: Waiting
tcp_set_trigger: {
  "trigger_id": "state1",
  "pattern": "START",
  "response": "READY"
}

// State 2: Ready
tcp_set_trigger: {
  "trigger_id": "state2",
  "pattern": "READY",
  "response": "PROCESSING"
}

// State 3: Processing
tcp_set_trigger: {
  "trigger_id": "state3",
  "pattern": "DATA:(.*)",
  "response": "ACK"
}
```

### Performance Testing
```json
// Send test data
for i in range(100):
  tcp_send: {"connection_id": "ID", "data": f"TEST_{i}"}

// Check statistics
tcp_buffer_info: {"connection_id": "ID"}
```

### Protocol Analysis
```json
// Capture everything in hex
tcp_read_buffer: {"connection_id": "ID", "format": "hex"}

// Analyze patterns
// Look for headers, terminators, data structures
```

## Remember

- This server handles **raw TCP** - you implement the protocol logic
- **Buffers store all received data** - read anytime
- **Triggers automate responses** - reduce manual work
- **Multiple connections supported** - manage many services
- **Binary safe** - handles any byte sequence
- **Protocol agnostic** - works with any TCP protocol

Use this server whenever you need to:
- Communicate with network services
- Test or debug protocols
- Automate network interactions
- Handle binary protocols
- Integrate with legacy systems
- Build protocol handlers