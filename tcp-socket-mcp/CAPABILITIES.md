# TCP Socket MCP Server - Complete Capabilities Documentation

## Purpose and Overview

The TCP Socket MCP Server provides AI models with direct access to raw TCP socket operations, enabling communication with any TCP-based service or protocol. This server acts as a bridge between AI models and network services, allowing for:

- **Protocol Testing**: Interact with and test various network protocols
- **Service Integration**: Connect to databases, web servers, IoT devices, and custom services
- **Network Debugging**: Analyze and debug network communication
- **Automation**: Create automated responses and protocol handlers
- **Binary Communication**: Handle both text and binary protocols

## Core Concepts

### TCP Connections
TCP (Transmission Control Protocol) provides reliable, ordered, and error-checked delivery of data between applications. This server allows you to:
- Open connections to any TCP service
- Send and receive data
- Manage multiple simultaneous connections
- Handle both text and binary protocols

### Buffer Management
All received data is stored in a buffer for each connection, allowing you to:
- Read data at any time
- Access specific portions of received data
- Clear buffers when needed
- Track data statistics

### Trigger System
Automated response system that monitors incoming data and responds automatically when patterns are detected, useful for:
- Protocol handshakes
- Keep-alive messages
- Authentication sequences
- State machines

## Complete Tool Reference

### 1. tcp_connect - Establish a TCP Connection

**Purpose**: Opens a new TCP connection to a specified host and port.

**When to use**:
- Starting communication with any TCP service
- Connecting to web servers, databases, chat servers, etc.
- Establishing multiple connections to different services

**Parameters**:
```json
{
  "host": "string - IP address or hostname (required)",
  "port": "number - Port number 1-65535 (required)",
  "connection_id": "string - Custom ID for the connection (optional, auto-generated if not provided)"
}
```

**Examples**:

```json
// Connect to a web server
{
  "host": "example.com",
  "port": 80
}

// Connect to a local service with custom ID
{
  "host": "localhost",
  "port": 3306,
  "connection_id": "mysql-connection"
}

// Connect to an SMTP server
{
  "host": "smtp.gmail.com",
  "port": 587,
  "connection_id": "email-server"
}
```

**Response**:
```json
{
  "success": true,
  "connection_id": "abc123-def456",
  "host": "example.com",
  "port": 80,
  "status": "connected"
}
```

### 2. tcp_send - Send Data Over TCP

**Purpose**: Sends data through an established TCP connection with support for text, binary, and hex-encoded data.

**When to use**:
- Sending commands to a server
- Transmitting binary data
- Sending protocol-specific messages
- Communicating with IoT devices

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)",
  "data": "string - Data to send (required)",
  "encoding": "string - 'utf-8', 'base64', or 'hex' (optional, default: 'utf-8')",
  "terminator": "string - Hex bytes to append, like '\\x0d\\x0a' (optional)"
}
```

**Examples**:

```json
// Send HTTP request with CRLF terminator
{
  "connection_id": "web-conn",
  "data": "GET / HTTP/1.1",
  "terminator": "\\x0d\\x0a"
}

// Send binary data using hex encoding
{
  "connection_id": "binary-conn",
  "data": "\\x01\\x00\\x00\\x10\\xff\\xfe",
  "encoding": "hex"
}

// Send mixed text and binary with terminator
{
  "connection_id": "protocol-conn",
  "data": "HELLO\\x00WORLD",
  "encoding": "hex",
  "terminator": "\\x03"
}

// Send base64-encoded binary data
{
  "connection_id": "data-conn",
  "data": "SGVsbG8gV29ybGQ=",
  "encoding": "base64"
}

// Send a database query
{
  "connection_id": "db-conn",
  "data": "SELECT * FROM users",
  "terminator": "\\x00"
}
```

**Encoding Options**:
- **utf-8**: Standard text encoding (default)
- **base64**: For binary data encoded as base64 string
- **hex**: Supports multiple formats:
  - Escaped: `\x48\x65\x6c\x6c\x6f`
  - Plain: `48656c6c6f`
  - Mixed: `Hello\x00World`

**Common Terminators**:
- `\x0d\x0a` - CRLF (Windows/HTTP/Telnet)
- `\x0a` - LF (Unix/Linux)
- `\x00` - Null (C strings/Binary protocols)
- `\x03` - ETX (End of Text)
- `\x04` - EOT (End of Transmission)

### 3. tcp_read_buffer - Read Received Data

**Purpose**: Reads data from a connection's receive buffer with flexible formatting options.

**When to use**:
- Reading server responses
- Checking for new data
- Debugging protocol communication
- Analyzing binary data

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)",
  "index": "number - Starting position in buffer (optional)",
  "count": "number - Number of chunks to read (optional)",
  "format": "string - 'utf-8', 'hex', or 'base64' (optional, default: 'utf-8')"
}
```

**Examples**:

```json
// Read all data as text
{
  "connection_id": "web-conn"
}

// Read binary data as hex
{
  "connection_id": "binary-conn",
  "format": "hex"
}

// Read specific portion of buffer
{
  "connection_id": "data-conn",
  "index": 0,
  "count": 5,
  "format": "utf-8"
}

// Read data as base64
{
  "connection_id": "file-conn",
  "format": "base64"
}
```

**Response**:
```json
{
  "connection_id": "web-conn",
  "chunks": 3,
  "data": ["HTTP/1.1 200 OK", "Content-Type: text/html", "..."],
  "format": "utf-8"
}
```

### 4. tcp_set_trigger - Create Auto-Response Trigger

**Purpose**: Sets up automatic responses when specific patterns are detected in received data.

**When to use**:
- Protocol handshakes
- Authentication sequences
- Keep-alive responses
- Chat bots
- State machine implementations

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)",
  "trigger_id": "string - Unique ID for this trigger (required)",
  "pattern": "string - Regex pattern to match (required)",
  "response": "string - Data to send when pattern matches (required)",
  "response_encoding": "string - 'utf-8', 'base64', or 'hex' (optional)",
  "response_terminator": "string - Hex bytes to append to response (optional)"
}
```

**Examples**:

```json
// Simple ping-pong response
{
  "connection_id": "game-conn",
  "trigger_id": "ping-handler",
  "pattern": "PING",
  "response": "PONG",
  "response_terminator": "\\x0d\\x0a"
}

// Authentication handler
{
  "connection_id": "auth-conn",
  "trigger_id": "login-handler",
  "pattern": "Username:",
  "response": "admin",
  "response_terminator": "\\x0d\\x0a"
}

// Binary protocol ACK
{
  "connection_id": "binary-conn",
  "trigger_id": "ack-handler",
  "pattern": "\\x01\\x00",
  "response": "\\x06\\x00\\x00\\x01",
  "response_encoding": "hex"
}

// Complex pattern with capture groups
{
  "connection_id": "chat-conn",
  "trigger_id": "greeting",
  "pattern": "HELLO (\\w+)",
  "response": "Welcome to the server!",
  "response_terminator": "\\x0d\\x0a"
}

// HTTP-like response
{
  "connection_id": "web-conn",
  "trigger_id": "http-response",
  "pattern": "GET /status",
  "response": "HTTP/1.1 200 OK\\x0d\\x0aContent-Length: 2\\x0d\\x0a\\x0d\\x0aOK",
  "response_encoding": "hex"
}
```

### 5. tcp_remove_trigger - Remove Auto-Response Trigger

**Purpose**: Removes a previously set trigger from a connection.

**When to use**:
- Disabling auto-responses
- Changing protocol states
- Cleanup operations

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)",
  "trigger_id": "string - ID of trigger to remove (required)"
}
```

**Example**:
```json
{
  "connection_id": "chat-conn",
  "trigger_id": "greeting"
}
```

### 6. tcp_clear_buffer - Clear Receive Buffer

**Purpose**: Clears all data from a connection's receive buffer.

**When to use**:
- Starting fresh communication
- Clearing old data
- Memory management
- Between different protocol phases

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)"
}
```

**Example**:
```json
{
  "connection_id": "data-conn"
}
```

### 7. tcp_buffer_info - Get Buffer Statistics

**Purpose**: Returns detailed information about a connection's buffer.

**When to use**:
- Monitoring data flow
- Debugging issues
- Checking buffer status
- Performance analysis

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)"
}
```

**Response**:
```json
{
  "connection_id": "data-conn",
  "chunks": 15,
  "total_size": 4096,
  "bytes_received": 4096,
  "bytes_sent": 256,
  "last_received": "2024-01-01T12:00:00Z"
}
```

### 8. tcp_list_connections - List All Connections

**Purpose**: Returns information about all active TCP connections.

**When to use**:
- Managing multiple connections
- Getting overview of active sessions
- Debugging connection issues
- Resource monitoring

**Parameters**: None

**Response**:
```json
{
  "total_connections": 3,
  "connections": [
    {
      "connection_id": "web-conn",
      "host": "example.com",
      "port": 80,
      "connected": true,
      "bytes_sent": 256,
      "bytes_received": 4096,
      "buffer_chunks": 10,
      "triggers": 2
    }
  ]
}
```

### 9. tcp_connection_info - Get Detailed Connection Info

**Purpose**: Returns comprehensive information about a specific connection.

**When to use**:
- Debugging specific connections
- Getting trigger information
- Checking connection health
- Detailed monitoring

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)"
}
```

**Response**:
```json
{
  "connection_id": "chat-conn",
  "host": "chat.example.com",
  "port": 6667,
  "connected": true,
  "created_at": "2024-01-01T12:00:00Z",
  "buffer": {
    "chunks": 25,
    "total_size": 2048,
    "bytes_received": 2048,
    "bytes_sent": 512
  },
  "triggers": [
    {
      "trigger_id": "ping-handler",
      "pattern": "PING",
      "response_length": 5
    }
  ]
}
```

### 10. tcp_disconnect - Close Connection

**Purpose**: Closes an active TCP connection and cleans up resources.

**When to use**:
- Ending communication
- Cleaning up resources
- Switching services
- Error recovery

**Parameters**:
```json
{
  "connection_id": "string - ID of the connection (required)"
}
```

**Example**:
```json
{
  "connection_id": "web-conn"
}
```

## Common Protocol Examples

### HTTP Communication

```json
// 1. Connect to web server
tcp_connect: {"host": "example.com", "port": 80}

// 2. Send HTTP request
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "GET / HTTP/1.1",
  "terminator": "\\x0d\\x0a"
}
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "Host: example.com",
  "terminator": "\\x0d\\x0a"
}
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "",
  "terminator": "\\x0d\\x0a"
}

// 3. Read response
tcp_read_buffer: {"connection_id": "YOUR_ID"}
```

### SMTP Email Protocol

```json
// 1. Connect to SMTP server
tcp_connect: {"host": "smtp.example.com", "port": 25}

// 2. Set up auto-responses for handshake
tcp_set_trigger: {
  "connection_id": "YOUR_ID",
  "trigger_id": "greeting",
  "pattern": "220",
  "response": "HELO client.example.com",
  "response_terminator": "\\x0d\\x0a"
}

// 3. Send email commands
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "MAIL FROM:<sender@example.com>",
  "terminator": "\\x0d\\x0a"
}
```

### Binary Protocol Communication

```json
// 1. Connect to binary service
tcp_connect: {"host": "device.local", "port": 9000}

// 2. Send binary packet header
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "\\x02\\x00\\x00\\x1a",  // STX + length
  "encoding": "hex"
}

// 3. Send binary payload
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "0102030405060708",
  "encoding": "hex",
  "terminator": "\\x03"  // ETX
}

// 4. Read binary response
tcp_read_buffer: {
  "connection_id": "YOUR_ID",
  "format": "hex"
}
```

### Chat/IRC Protocol

```json
// 1. Connect to IRC server
tcp_connect: {"host": "irc.example.com", "port": 6667}

// 2. Set up triggers for server pings
tcp_set_trigger: {
  "connection_id": "YOUR_ID",
  "trigger_id": "ping",
  "pattern": "PING :(.*)",
  "response": "PONG :$1",
  "response_terminator": "\\x0d\\x0a"
}

// 3. Join channel
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "NICK MyBot",
  "terminator": "\\x0d\\x0a"
}
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "USER bot 0 * :My Bot",
  "terminator": "\\x0d\\x0a"
}
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "JOIN #channel",
  "terminator": "\\x0d\\x0a"
}
```

### Telnet Session

```json
// 1. Connect to telnet server
tcp_connect: {"host": "telnet.example.com", "port": 23}

// 2. Set up login trigger
tcp_set_trigger: {
  "connection_id": "YOUR_ID",
  "trigger_id": "username",
  "pattern": "login:",
  "response": "admin",
  "response_terminator": "\\x0d\\x0a"
}

tcp_set_trigger: {
  "connection_id": "YOUR_ID",
  "trigger_id": "password",
  "pattern": "Password:",
  "response": "secret123",
  "response_terminator": "\\x0d\\x0a"
}

// 3. Send commands
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "ls -la",
  "terminator": "\\x0d\\x0a"
}
```

## Advanced Usage Patterns

### Pattern 1: Multi-Connection Management

Managing multiple services simultaneously:

```json
// Connect to multiple services
tcp_connect: {"host": "api.service1.com", "port": 443, "connection_id": "api1"}
tcp_connect: {"host": "api.service2.com", "port": 443, "connection_id": "api2"}
tcp_connect: {"host": "db.internal", "port": 5432, "connection_id": "database"}

// Send requests to different services
tcp_send: {"connection_id": "api1", "data": "GET /data"}
tcp_send: {"connection_id": "api2", "data": "GET /status"}
tcp_send: {"connection_id": "database", "data": "SELECT NOW()"}

// List all connections
tcp_list_connections: {}
```

### Pattern 2: Protocol State Machine

Implementing a state machine with triggers:

```json
// Initial state - waiting for connection
tcp_set_trigger: {
  "connection_id": "fsm",
  "trigger_id": "state_init",
  "pattern": "HELLO",
  "response": "READY",
  "response_terminator": "\\x0d\\x0a"
}

// After READY, wait for AUTH
tcp_set_trigger: {
  "connection_id": "fsm",
  "trigger_id": "state_auth",
  "pattern": "AUTH (\\w+)",
  "response": "AUTH_OK",
  "response_terminator": "\\x0d\\x0a"
}

// After AUTH_OK, accept commands
tcp_set_trigger: {
  "connection_id": "fsm",
  "trigger_id": "state_command",
  "pattern": "CMD:(.*)",
  "response": "PROCESSING",
  "response_terminator": "\\x0d\\x0a"
}
```

### Pattern 3: Binary Protocol Parser

Handling complex binary protocols:

```json
// Send packet with header
tcp_send: {
  "connection_id": "binary",
  "data": "\\xaa\\x55",  // Sync bytes
  "encoding": "hex"
}

tcp_send: {
  "connection_id": "binary",
  "data": "\\x00\\x10",  // Length field
  "encoding": "hex"
}

tcp_send: {
  "connection_id": "binary",
  "data": "0102030405060708090a0b0c0d0e0f10",  // 16 bytes of data
  "encoding": "hex"
}

tcp_send: {
  "connection_id": "binary",
  "data": "\\x00\\x00",  // Checksum
  "encoding": "hex",
  "terminator": "\\x55\\xaa"  // End markers
}
```

### Pattern 4: Performance Monitoring

Monitor connection performance:

```json
// Get initial stats
tcp_buffer_info: {"connection_id": "monitor"}

// Send test data
tcp_send: {
  "connection_id": "monitor",
  "data": "TEST_PACKET_1234567890",
  "terminator": "\\x0d\\x0a"
}

// Check buffer growth
tcp_buffer_info: {"connection_id": "monitor"}

// Read and analyze response time
tcp_read_buffer: {"connection_id": "monitor"}

// Get detailed connection info
tcp_connection_info: {"connection_id": "monitor"}
```

## Best Practices

### 1. Connection Management
- Always store connection IDs for later use
- Close connections when done to free resources
- Use meaningful connection IDs for multiple connections
- Check connection status before sending data

### 2. Data Encoding
- Use hex encoding for binary protocols
- Use terminators for consistent line endings
- Choose appropriate format when reading buffers
- Be explicit about encoding to avoid ambiguity

### 3. Error Handling
- Check response success fields
- Handle connection failures gracefully
- Clear buffers when switching protocols
- Remove triggers when changing states

### 4. Performance
- Use triggers for repetitive responses
- Batch send operations when possible
- Clear buffers periodically to manage memory
- Monitor buffer sizes with tcp_buffer_info

### 5. Security
- Never send sensitive data in plain text
- Use appropriate ports for services
- Close connections after authentication
- Clear buffers containing sensitive data

## Troubleshooting

### Common Issues and Solutions

**Connection Refused**
- Verify host and port are correct
- Check if service is running
- Ensure firewall allows connection

**No Response**
- Check if terminator is needed
- Verify protocol requirements
- Use tcp_buffer_info to check for data

**Binary Data Corruption**
- Use hex or base64 encoding
- Check format when reading buffer
- Verify terminator doesn't conflict

**Trigger Not Working**
- Verify pattern regex is correct
- Check trigger_id is unique
- Ensure pattern matches exactly

## Summary

The TCP Socket MCP Server provides comprehensive TCP communication capabilities, supporting:
- Any TCP-based protocol (HTTP, SMTP, FTP, Telnet, SSH, custom)
- Both text and binary data transmission
- Automatic response handling through triggers
- Multiple simultaneous connections
- Full buffer management
- Protocol-compliant terminators

Use this server whenever you need to:
- Communicate with network services
- Test or debug protocols
- Automate network interactions
- Handle binary protocols
- Integrate with legacy systems
- Build protocol handlers

The server handles all the low-level TCP details, allowing you to focus on the protocol logic and data exchange.