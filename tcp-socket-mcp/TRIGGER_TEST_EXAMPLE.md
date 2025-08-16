# TCP Socket MCP - Trigger Testing Example

## Overview
This example shows how to test the auto-response trigger functionality using the echo server test utility.

## Step 1: Start the Echo Server
In Terminal 1, start the echo server:
```bash
cd /Volumes/ExtraSpace\ External/Dev/TcpSocketMCP/tcp-socket-mcp
python example_usage.py echo
```
This starts an echo server on `localhost:9999` that echoes back whatever you send.

## Step 2: Start MCP Inspector
In Terminal 2, start the MCP Inspector:
```bash
cd /Volumes/ExtraSpace\ External/Dev/TcpSocketMCP/tcp-socket-mcp
mcp-inspector python run.py
```

## Step 3: Connect to Echo Server
In MCP Inspector, call `tcp_connect`:
```json
{
  "host": "localhost",
  "port": 9999
}
```

Save the `connection_id` from the response (e.g., "abc123-def456...")

## Step 4: Set Up Triggers

### Example 1: Simple Greeting Trigger
Call `tcp_set_trigger`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "greeting_trigger",
  "pattern": "(?i)hello",
  "response": "Hi there! How can I help you?\n"
}
```
This trigger responds with a greeting whenever it sees "hello" (case-insensitive).

### Example 2: Command Response Trigger
Call `tcp_set_trigger`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "status_trigger",
  "pattern": "STATUS",
  "response": "System Status: All systems operational\n"
}
```
This trigger responds with status info when it sees "STATUS".

### Example 3: Pattern Matching Trigger
Call `tcp_set_trigger`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "user_trigger",
  "pattern": "USER:(\\w+)",
  "response": "Welcome, user! Your session has been logged.\n"
}
```
This trigger matches "USER:username" patterns.

### Example 4: Multi-line Response Trigger
Call `tcp_set_trigger`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "help_trigger",
  "pattern": "HELP",
  "response": "Available Commands:\n1. STATUS - Get system status\n2. HELP - Show this message\n3. QUIT - Disconnect\n"
}
```

### Example 5: Binary Response Trigger (Base64)
Call `tcp_set_trigger`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "binary_trigger",
  "pattern": "BINARY",
  "response": "SGVsbG8gV29ybGQh",
  "response_encoding": "base64"
}
```
This sends "Hello World!" as binary data when "BINARY" is received.

## Step 5: Test the Triggers

### Send Test Data
Call `tcp_send` to trigger the auto-responses:

**Test greeting trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "hello\n"
}
```

**Test status trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "STATUS\n"
}
```

**Test help trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "HELP\n"
}
```

**Test pattern matching:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "data": "USER:john_doe\n"
}
```

## Step 6: Read Responses
Call `tcp_read_buffer` to see all the data (both echoes and trigger responses):
```json
{
  "connection_id": "YOUR_CONNECTION_ID"
}
```

You should see:
1. The echo of your original message
2. The echo of the trigger's auto-response
3. The actual data from the server

## Step 7: Manage Triggers

### List Connection Info (includes triggers)
Call `tcp_connection_info`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID"
}
```

### Remove a Trigger
Call `tcp_remove_trigger`:
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "greeting_trigger"
}
```

## Advanced Example: Chat Protocol Simulation

Set up multiple triggers to simulate a chat protocol:

**1. Login trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "login",
  "pattern": "LOGIN:(\\w+):(\\w+)",
  "response": "AUTH_SUCCESS:session_12345\n"
}
```

**2. Message trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "message",
  "pattern": "MSG:(.*)",
  "response": "MSG_RECEIVED:OK\n"
}
```

**3. Ping/Pong trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "ping",
  "pattern": "PING",
  "response": "PONG\n"
}
```

**4. Error trigger:**
```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "error",
  "pattern": "ERROR",
  "response": "ERROR_HANDLED:Please contact support\n"
}
```

## Testing HTTP-like Protocol

You can also test HTTP-like responses:

```json
{
  "connection_id": "YOUR_CONNECTION_ID",
  "trigger_id": "http_response",
  "pattern": "GET /api/status",
  "response": "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 27\r\n\r\n{\"status\":\"operational\"}\r\n"
}
```

## Tips for Testing

1. **Use Case-Insensitive Patterns**: Add `(?i)` at the start of patterns for case-insensitive matching
2. **Test Pattern Groups**: Use `(\\w+)` or `(.*)` to match variable content
3. **Multiple Triggers**: You can have multiple triggers active simultaneously
4. **Order Matters**: First matching trigger wins if patterns overlap
5. **Clear Buffer**: Use `tcp_clear_buffer` between tests to avoid confusion

## Debugging Triggers

1. Check active triggers with `tcp_connection_info`
2. Monitor the buffer with `tcp_read_buffer` after each operation
3. Use `tcp_buffer_info` to see buffer statistics
4. Remove and re-add triggers if behavior seems incorrect

## Complete Test Flow Example

```bash
# 1. Connect
tcp_connect: {"host": "localhost", "port": 9999}
# Save connection_id: "abc123"

# 2. Set trigger
tcp_set_trigger: {
  "connection_id": "abc123",
  "trigger_id": "test",
  "pattern": "HELLO",
  "response": "WORLD\n"
}

# 3. Send data that matches
tcp_send: {"connection_id": "abc123", "data": "HELLO\n"}

# 4. Read buffer (should show: "HELLO\n", "WORLD\n", and their echoes)
tcp_read_buffer: {"connection_id": "abc123"}

# 5. Clean up
tcp_remove_trigger: {"connection_id": "abc123", "trigger_id": "test"}
tcp_disconnect: {"connection_id": "abc123"}
```

The trigger system is perfect for:
- Protocol testing
- Automated responses
- State machine simulation
- Mock server behaviors
- Integration testing