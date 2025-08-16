# Trigger Pre-Registration Feature

## Overview

The TCP Socket MCP server now supports **pre-registering triggers before establishing a connection**. This powerful feature enables immediate protocol handshakes and responses without any delay after connection.

## Why Pre-Registration?

Many protocols require immediate handshakes or responses upon connection:
- **IRC**: Servers send PING immediately after connection
- **SSH**: Banner exchange happens immediately
- **Game Servers**: Often require immediate authentication
- **Custom Protocols**: May have strict timing requirements

Without pre-registration, there's a race condition:
1. Connect to server
2. Server sends handshake request
3. You try to set up trigger
4. **Too late!** The server may have already disconnected

With pre-registration:
1. Set up triggers for expected patterns
2. Connect to server
3. **Triggers are already active!** Immediate response to handshake

## How It Works

### Step 1: Pre-Register Triggers

Call `tcp_set_trigger` with a connection_id that doesn't exist yet:

```json
{
  "connection_id": "irc-bot",
  "trigger_id": "auto-pong",
  "pattern": "PING :(.*)",
  "response": "PONG :$1",
  "response_terminator": "\\x0d\\x0a"
}
```

**Response:**
```json
{
  "success": true,
  "connection_id": "irc-bot",
  "trigger_id": "auto-pong",
  "pattern": "PING :(.*)",
  "status": "pending",
  "message": "Trigger pre-registered and will activate when connection is established"
}
```

### Step 2: Connect

When you connect using the same connection_id, triggers automatically activate:

```json
// Using tcp_connect
{
  "host": "irc.freenode.net",
  "port": 6667,
  "connection_id": "irc-bot"
}
```

**Response:**
```json
{
  "success": true,
  "connection_id": "irc-bot",
  "host": "irc.freenode.net",
  "port": 6667,
  "status": "connected",
  "applied_triggers": ["auto-pong"],
  "message": "Applied 1 pre-registered trigger(s)"
}
```

## Complete Examples

### IRC Bot with Auto-PONG

```python
# 1. Pre-register PONG response
tcp_set_trigger(
    connection_id="irc-bot",
    trigger_id="pong",
    pattern="PING :(.*)",
    response="PONG :$1",
    response_terminator="\\x0d\\x0a"
)

# 2. Pre-register nick registration
tcp_set_trigger(
    connection_id="irc-bot",
    trigger_id="nick",
    pattern="NOTICE.*",
    response="NICK MyBot\\x0d\\x0aUSER bot 0 * :My Bot",
    response_terminator="\\x0d\\x0a"
)

# 3. Connect - triggers activate immediately
tcp_connect("irc-bot", "irc.server.com", 6667)
# Server sends PING → Auto-responds with PONG
# Server sends NOTICE → Auto-registers nick
```

### Game Server Authentication

```python
# 1. Pre-register authentication sequence
tcp_set_trigger(
    connection_id="game",
    trigger_id="auth",
    pattern="AUTH_REQUIRED",
    response="AUTH_TOKEN:abc123def456",
    response_terminator="\\x00"
)

# 2. Pre-register protocol version
tcp_set_trigger(
    connection_id="game",
    trigger_id="version",
    pattern="VERSION\\?",
    response="VERSION:2.0",
    response_terminator="\\x00"
)

# 3. Connect and send initial packet
tcp_connect_and_send(
    connection_id="game",
    host="game.server.com",
    port=9999,
    data="HELLO",
    terminator="\\x00"
)
# Triggers handle authentication automatically
```

### SSH-like Banner Exchange

```python
# 1. Pre-register banner response
tcp_set_trigger(
    connection_id="ssh-like",
    trigger_id="banner",
    pattern="^SSH-.*",
    response="SSH-2.0-MyClient_1.0",
    response_terminator="\\x0d\\x0a"
)

# 2. Connect
tcp_connect("ssh-like", "server.com", 22)
# Server sends SSH banner → Auto-responds with client banner
```

## Managing Pre-Registered Triggers

### List Pending Triggers

Currently, pending triggers are not directly listable, but they are reported when:
- Setting a trigger (returns "pending" status)
- Connecting (shows "applied_triggers" list)

### Remove Pending Triggers

You can remove pending triggers just like active ones:

```json
{
  "connection_id": "not-connected-yet",
  "trigger_id": "some-trigger"
}
```

**Response:**
```json
{
  "success": true,
  "connection_id": "not-connected-yet",
  "trigger_id": "some-trigger",
  "status": "removed_pending"
}
```

## Use Cases

### 1. Time-Critical Protocols
Protocols that disconnect if response isn't immediate:
- Pre-register expected challenges
- Connect and let triggers handle responses
- No race conditions

### 2. Complex Handshakes
Multi-step authentication sequences:
- Pre-register entire handshake chain
- Connect once, everything happens automatically
- Reduces round-trip delays

### 3. Protocol Testing
Testing server implementations:
- Pre-register various response patterns
- Connect to test different scenarios
- Automated protocol compliance testing

### 4. Resilient Clients
Building robust client applications:
- Pre-register error handlers
- Pre-register keep-alive responses
- Pre-register reconnection sequences

## Best Practices

1. **Use Unique Connection IDs**: Choose descriptive IDs that won't conflict
2. **Test Patterns**: Verify regex patterns match expected input
3. **Order Matters**: More specific patterns should be registered first
4. **Clean Up**: Remove unused pending triggers to avoid confusion
5. **Error Handling**: Pre-register triggers for error conditions too

## Technical Details

- **Storage**: Pending triggers stored in `pending_triggers` dictionary
- **Activation**: Triggers move from pending to active on connection
- **Persistence**: Pending triggers remain until connection or removal
- **Encoding**: All encoding options (hex, base64, utf-8) supported
- **Terminators**: Line ending handling works as expected

## Limitations

- **No Persistence**: Pending triggers are lost if server restarts
- **Memory Only**: All triggers stored in memory
- **No Timeout**: Pending triggers remain indefinitely until used
- **No Listing**: Can't directly query all pending triggers

## Status Codes

When working with triggers, the status field indicates:
- **"pending"**: Trigger pre-registered, waiting for connection
- **"active"**: Trigger active on live connection
- **"removed_pending"**: Pending trigger was removed
- **"removed_active"**: Active trigger was removed