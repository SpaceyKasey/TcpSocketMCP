# TCP Connect and Send Tool

## Overview

The `tcp_connect_and_send` tool provides a time-sensitive connection and immediate data transmission capability for protocols that require rapid initial communication.

## Purpose

Some protocols are time-sensitive and may close connections if data isn't sent immediately after connection establishment. This tool combines the connection and initial send operations into a single atomic operation, ensuring data is transmitted as quickly as possible after the connection is established.

## Use Cases

1. **HTTP/HTTPS Requests**: Send requests immediately upon connection
2. **Protocol Handshakes**: Initiate handshakes without delay
3. **Time-Sensitive Protocols**: Protocols that timeout quickly
4. **Authentication Sequences**: Send credentials immediately
5. **Keep-Alive Initiation**: Start keep-alive sequences promptly

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| host | string | Yes | Target hostname or IP address |
| port | number | Yes | Target port number |
| data | string | Yes | Data to send immediately after connection |
| connection_id | string | No | Custom ID for the connection (auto-generated if not provided) |
| encoding | string | No | Data encoding: "utf-8" (default), "hex", or "base64" |
| terminator | string | No | Optional line terminator in hex format (e.g., "\\x0d\\x0a") |

## Response

```json
{
  "success": true,
  "connection_id": "conn-123",
  "host": "example.com",
  "port": 80,
  "bytes_sent": 56,
  "status": "connected",
  "immediate_response": true,
  "buffer_chunks": 1
}
```

## Examples

### Basic HTTP Request
```json
{
  "host": "httpbin.org",
  "port": 80,
  "data": "GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n",
  "connection_id": "http-quick"
}
```

### Binary Protocol with Hex Encoding
```json
{
  "host": "binary-server.com",
  "port": 9000,
  "data": "01004D5347",
  "encoding": "hex",
  "connection_id": "binary-conn"
}
```

### With Custom Terminator
```json
{
  "host": "telnet-server.com",
  "port": 23,
  "data": "USER admin",
  "terminator": "\\x0d\\x0a",
  "connection_id": "telnet-conn"
}
```

## Implementation Details

1. **Connection**: Establishes TCP connection to the specified host and port
2. **Immediate Send**: Sends data immediately after successful connection
3. **Error Handling**: If send fails, connection is cleaned up automatically
4. **Response Check**: Waits briefly (100ms) to check for immediate responses
5. **Connection Persistence**: Connection remains open for subsequent operations

## Error Handling

- **duplicate_id**: Connection ID already exists
- **connection_failed**: Unable to connect to host:port
- **send_failed**: Connected but failed to send data

## Comparison with Separate Operations

### Traditional Approach (2 operations)
```
1. tcp_connect -> wait for response -> connection_id
2. tcp_send with connection_id -> wait for response
Total time: Connection latency + Send latency + Processing overhead
```

### Combined Approach (1 operation)
```
1. tcp_connect_and_send -> immediate send
Total time: Connection latency (send happens within same operation)
```

## Benefits

1. **Reduced Latency**: Single round-trip instead of two
2. **Time-Sensitive Support**: Critical for protocols with tight timing requirements
3. **Atomic Operation**: Connection and send happen together
4. **Simplified Workflow**: One tool call instead of two
5. **Immediate Feedback**: Know if both connection and send succeeded

## Testing

The tool has been tested with:
- HTTP/1.1 requests to httpbin.org and example.com
- Hex-encoded binary data transmission
- Custom line terminators
- Various error conditions

All tests pass successfully with proper connection establishment, data transmission, and response reception.