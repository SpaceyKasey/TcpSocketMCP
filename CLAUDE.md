# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCP Socket MCP Server - A Model Context Protocol server that provides raw TCP socket access to AI models. Enables direct interaction with network services through buffered connections with automatic trigger/response capabilities.

## Development Commands

### Running the Server
```bash
# Direct execution (no installation needed)
python run.py

# Or after installation
tcp-socket-mcp
```

### Testing Connections
```bash
# Test with netcat
nc -l 8080  # Terminal 1: Start test server
python run.py  # Terminal 2: Run MCP server
# Terminal 3: Use MCP client to test tcp_connect("localhost", 8080)
```

## Architecture

### Core Components

**MCP Server Layer** (`src/TcpSocketMCP/server.py`)
- Implements MCP protocol and tool registration
- Manages connection lifecycle and routing
- Handles encoding/decoding (UTF-8, hex, base64)
- Pre-registration system for triggers before connection

**Connection Manager** (`src/TcpSocketMCP/connection.py`)
- TCPConnection class with async read loop
- Buffer management with chunked storage
- Trigger pattern matching and auto-response
- Thread-safe operations with asyncio locks

**Entry Points**
- `run.py`: Direct runner without installation (adds src to path)
- `src/TcpSocketMCP/__main__.py`: Package entry point
- Both call `server.main_sync()` for stdio MCP transport

### Key Design Patterns

**Hex Encoding Strategy**: Primary format is plain hex pairs (`"48656C6C6F"` for "Hello"). This avoids JSON escaping issues with protocols requiring specific line endings (HTTP, SMTP, IRC).

**Buffer Architecture**: All received data stored in chunks until explicitly cleared. Allows multiple reads, partial reads with index/count, and preserves data for analysis.

**Trigger System**: Pre-registration allows setting up auto-responses before connection. Essential for protocols requiring immediate handshakes. Uses regex with capture group substitution.

**Connection ID Management**: Auto-generated UUIDs or custom IDs. Custom IDs enable pre-registration workflow where triggers are set up before connection exists.

## Critical Implementation Details

### Hex Parsing (`_parse_hex_string`)
Supports both plain hex (`"48656C6C6F"`) and legacy escaped format (`"\x48\x65"`). Always prefer plain hex in documentation and examples.

### Async Read Loop
Each connection runs `_read_loop()` task that:
1. Continuously reads from socket
2. Appends to buffer
3. Checks triggers for pattern matches
4. Sends automatic responses when triggered

### Error Handling
- Connection failures return descriptive errors
- Invalid hex falls back to UTF-8 encoding
- Disconnected connections cleaned up automatically
- Trigger errors logged but don't crash connection

## Publishing & Distribution

Package is configured for PyPI distribution:
- Build backend: hatchling
- Package name: TcpSocketMCP
- Entry point: TcpSocketMCP command
- Python requirement: >=3.10

## MCP Integration Points

Tools exposed via MCP:
- `tcp_connect`: Create connections with optional custom ID
- `tcp_send`: Send data with encoding options
- `tcp_read_buffer`: Read with format options
- `tcp_set_trigger`: Pattern-based auto-responses
- `tcp_connect_and_send`: Atomic connect+send
- Utility tools for connection management

Each tool returns structured responses with success/error status and relevant data (connection_id, bytes_sent, buffer content, etc.).