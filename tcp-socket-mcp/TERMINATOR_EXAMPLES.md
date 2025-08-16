# TCP Socket MCP - Terminator Feature

## Overview
The terminator feature allows you to automatically append specific bytes to every send operation or trigger response. This is extremely useful for protocols that require consistent line endings or packet terminators.

## Terminator Parameter
The `terminator` parameter accepts hex-formatted strings to specify the bytes to append:
- `\x0d\x0a` - CRLF (Windows line ending)
- `\x0a` - LF (Unix line ending)
- `\x0d` - CR (Classic Mac line ending)
- `\x00` - Null terminator
- Any hex sequence you need

## Examples for tcp_send

### Example 1: HTTP Request with CRLF Terminator
Instead of manually adding `\r\n` to each line:
```json
{
  "connection_id": "web-conn",
  "data": "GET / HTTP/1.1",
  "terminator": "\\x0d\\x0a"
}
```
This sends: `GET / HTTP/1.1\r\n`

### Example 2: Multiple Commands with Consistent Line Endings
```json
// First command
{
  "connection_id": "telnet-conn",
  "data": "USER admin",
  "terminator": "\\x0d\\x0a"
}

// Second command
{
  "connection_id": "telnet-conn",
  "data": "PASS secret",
  "terminator": "\\x0d\\x0a"
}
```

### Example 3: Null-Terminated Strings
For C-style protocols:
```json
{
  "connection_id": "binary-conn",
  "data": "HELLO",
  "terminator": "\\x00"
}
```
This sends: `HELLO\0`

### Example 4: Binary Protocol with Fixed Terminator
```json
{
  "connection_id": "proto-conn",
  "data": "\\x01\\x00\\x00\\x10DATA",
  "encoding": "hex",
  "terminator": "\\xff\\xfe"
}
```
This sends the hex data followed by 0xFF 0xFE

### Example 5: Mixed Text and Hex with Terminator
```json
{
  "connection_id": "mixed-conn",
  "data": "START\\x00DATA",
  "encoding": "hex",
  "terminator": "\\x03"
}
```
This sends: `START\0DATA\x03` (ETX at the end)

## Examples for tcp_set_trigger

### Example 1: Chat Protocol with Line Endings
```json
{
  "connection_id": "chat-conn",
  "trigger_id": "welcome",
  "pattern": "HELLO",
  "response": "Welcome to the server!",
  "response_terminator": "\\x0d\\x0a"
}
```
Auto-responds with: `Welcome to the server!\r\n`

### Example 2: Binary Protocol ACK with Terminator
```json
{
  "connection_id": "binary-conn",
  "trigger_id": "ack",
  "pattern": "\\x01\\x00",
  "response": "\\x06",
  "response_encoding": "hex",
  "response_terminator": "\\x00\\x00"
}
```
When receiving 0x01 0x00, responds with: 0x06 0x00 0x00

### Example 3: Command Response with Multiple Terminators
```json
{
  "connection_id": "cmd-conn",
  "trigger_id": "status",
  "pattern": "STATUS",
  "response": "OK: System operational",
  "response_terminator": "\\x0d\\x0a\\x0d\\x0a"
}
```
Responds with double CRLF (common in HTTP-like protocols)

## Common Protocol Terminators

| Protocol | Terminator | Hex Format | Description |
|----------|------------|------------|-------------|
| HTTP | CRLF | `\\x0d\\x0a` | Line ending |
| HTTP | Double CRLF | `\\x0d\\x0a\\x0d\\x0a` | Header/body separator |
| Telnet | CRLF | `\\x0d\\x0a` | Command terminator |
| SMTP | CRLF | `\\x0d\\x0a` | Line ending |
| FTP | CRLF | `\\x0d\\x0a` | Command terminator |
| IRC | CRLF | `\\x0d\\x0a` | Message terminator |
| Unix | LF | `\\x0a` | Line ending |
| C Strings | NULL | `\\x00` | String terminator |
| STX/ETX | ETX | `\\x03` | End of text |
| Binary | Custom | Various | Protocol-specific |

## Use Cases

### 1. Interactive Protocols (Telnet, SSH)
Always use CRLF terminator for commands:
```json
{
  "connection_id": "telnet",
  "data": "ls -la",
  "terminator": "\\x0d\\x0a"
}
```

### 2. HTTP Requests
Build requests with consistent line endings:
```json
{
  "connection_id": "http",
  "data": "Host: example.com",
  "terminator": "\\x0d\\x0a"
}
```

### 3. Binary Protocols
Add packet terminators:
```json
{
  "connection_id": "binary",
  "data": "0102030405",
  "encoding": "hex",
  "terminator": "\\xff\\xff"
}
```

### 4. Database Protocols
Send SQL with proper terminators:
```json
{
  "connection_id": "db",
  "data": "SELECT * FROM users",
  "terminator": "\\x00"
}
```

## Testing with Echo Server

1. Start echo server:
```bash
python example_usage.py echo
```

2. Connect and test terminators:
```json
// Connect
tcp_connect: {"host": "localhost", "port": 9999}

// Send with CRLF terminator
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "TEST",
  "terminator": "\\x0d\\x0a"
}

// Read buffer in hex to see terminator
tcp_read_buffer: {
  "connection_id": "YOUR_ID",
  "format": "hex"
}
// Should show: 54455354 0d0a (TEST + CRLF)
```

## Advanced Example: Protocol Handler

Set up a complete protocol handler with consistent terminators:

```json
// Set trigger for login with terminator
tcp_set_trigger: {
  "connection_id": "proto",
  "trigger_id": "login_response",
  "pattern": "LOGIN:(\\w+)",
  "response": "220 Welcome",
  "response_terminator": "\\x0d\\x0a"
}

// Set trigger for commands with terminator
tcp_set_trigger: {
  "connection_id": "proto",
  "trigger_id": "cmd_response",
  "pattern": "CMD:(\\w+)",
  "response": "250 OK",
  "response_terminator": "\\x0d\\x0a"
}

// Send login with terminator
tcp_send: {
  "connection_id": "proto",
  "data": "LOGIN:user",
  "terminator": "\\x0d\\x0a"
}
```

## Tips

1. **Consistency**: Use the same terminator throughout a session for protocol consistency
2. **Hex Format**: Always use `\\xNN` format for terminators (two hex digits)
3. **Multiple Bytes**: Chain multiple bytes like `\\x0d\\x0a` for multi-byte terminators
4. **Binary Safety**: Terminators work with any encoding (utf-8, base64, hex)
5. **Debugging**: Use `format: "hex"` in tcp_read_buffer to verify terminators are sent correctly