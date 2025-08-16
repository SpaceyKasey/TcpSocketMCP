# TCP Socket MCP - Hex Encoding for Binary Data

## Overview
The TCP Socket MCP server now supports sending binary data using hex encoding. This allows you to send any byte sequence including null bytes, control characters, and non-printable data.

## Supported Hex Formats

### 1. Escaped Hex Format (`\xNN`)
Use `\x` followed by two hex digits for each byte:
```json
{
  "data": "\\x48\\x65\\x6c\\x6c\\x6f\\x00\\x57\\x6f\\x72\\x6c\\x64",
  "encoding": "hex"
}
```
This sends: `Hello\0World` (with a null byte in the middle)

### 2. Plain Hex String
A continuous string of hex digits:
```json
{
  "data": "48656c6c6f00576f726c64",
  "encoding": "hex"
}
```
This sends the same: `Hello\0World`

### 3. Mixed Format
You can mix literal text with hex escapes:
```json
{
  "data": "Hello\\x00World\\x0d\\x0a",
  "encoding": "hex"
}
```
This sends: `Hello\0World\r\n`

### 4. Spaced Hex String
Spaces are automatically removed:
```json
{
  "data": "48 65 6c 6c 6f 00 57 6f 72 6c 64",
  "encoding": "hex"
}
```

## Examples for tcp_send

### Example 1: Send Binary Protocol Header
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "\\x01\\x00\\x00\\x10\\xff\\xfe",
  "encoding": "hex"
}
```
Sends 6 bytes: 0x01, 0x00, 0x00, 0x10, 0xFF, 0xFE

### Example 2: Send HTTP Request with CRLF
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "GET / HTTP/1.1\\x0d\\x0aHost: example.com\\x0d\\x0a\\x0d\\x0a",
  "encoding": "hex"
}
```

### Example 3: Send Binary Packet
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "0200001a0000000148656c6c6f",
  "encoding": "hex"
}
```

### Example 4: Send Mixed ASCII and Binary
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "START\\x00\\x00\\x00\\x04DATA\\xffEND",
  "encoding": "hex"
}
```

## Examples for tcp_set_trigger

### Example 1: Binary Protocol Response
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "binary_ack",
  "pattern": "\\x01\\x00",
  "response": "\\x06\\x00\\x00\\x01\\xAC\\xED",
  "response_encoding": "hex"
}
```
When the server sends 0x01 0x00, auto-respond with ACK packet

### Example 2: Null-Terminated String Response
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "null_term",
  "pattern": "LOGIN",
  "response": "OK\\x00",
  "response_encoding": "hex"
}
```

### Example 3: Binary Protocol Handshake
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "handshake",
  "pattern": "\\xFF\\xFE",
  "response": "\\xFF\\xFC\\x01\\xFF\\xFC\\x21",
  "response_encoding": "hex"
}
```

## Common Use Cases

### 1. Telnet Protocol
Send Telnet commands with IAC (0xFF) sequences:
```json
{
  "data": "\\xff\\xfb\\x01\\xff\\xfb\\x03",
  "encoding": "hex"
}
```

### 2. Binary Protocols
Send packet headers with length fields:
```json
{
  "data": "\\x00\\x00\\x00\\x1a",
  "encoding": "hex"
}
```
Sends a 4-byte big-endian length field (26 bytes)

### 3. Control Characters
Send control characters like STX, ETX, EOT:
```json
{
  "data": "\\x02DATA\\x03",
  "encoding": "hex"
}
```

### 4. WebSocket Frames
Send WebSocket frame headers:
```json
{
  "data": "\\x81\\x85\\x37\\xfa\\x21\\x3d\\x7f\\x9f\\x4d\\x51\\x58",
  "encoding": "hex"
}
```

## Testing Binary Data

### Test with Echo Server
1. Start echo server:
```bash
python example_usage.py echo
```

2. Connect via MCP Inspector:
```json
tcp_connect: {"host": "localhost", "port": 9999}
```

3. Send binary data:
```json
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "\\x00\\x01\\x02\\x03\\x04\\x05",
  "encoding": "hex"
}
```

4. Read buffer to see echoed binary:
```json
tcp_read_buffer: {
  "connection_id": "YOUR_ID",
  "format": "hex"
}
```

### Test with Binary Trigger
1. Set binary trigger:
```json
tcp_set_trigger: {
  "connection_id": "YOUR_ID",
  "trigger_id": "binary_test",
  "pattern": "\\x00\\x00",
  "response": "\\xff\\xff\\xff\\xff",
  "response_encoding": "hex"
}
```

2. Send trigger pattern:
```json
tcp_send: {
  "connection_id": "YOUR_ID",
  "data": "\\x00\\x00",
  "encoding": "hex"
}
```

3. Check buffer for auto-response (should see 0xFF 0xFF 0xFF 0xFF)

## Hex Conversion Reference

| ASCII | Hex  | Description |
|-------|------|-------------|
| NUL   | \\x00 | Null byte |
| SOH   | \\x01 | Start of Header |
| STX   | \\x02 | Start of Text |
| ETX   | \\x03 | End of Text |
| EOT   | \\x04 | End of Transmission |
| LF    | \\x0a | Line Feed (\n) |
| CR    | \\x0d | Carriage Return (\r) |
| ESC   | \\x1b | Escape |
| Space | \\x20 | Space |
| DEL   | \\x7f | Delete |
| 0xFF  | \\xff | Common in binary protocols |

## Tips
1. **Debugging**: Use `format: "hex"` in `tcp_read_buffer` to see received data in hex
2. **Testing**: The echo server will echo back your binary data exactly
3. **Patterns**: Regex patterns in triggers work with the raw binary data
4. **Mixed Data**: You can mix UTF-8 text with hex escapes in hex encoding mode
5. **Case Insensitive**: Hex digits can be uppercase or lowercase (\\xFF = \\xff)