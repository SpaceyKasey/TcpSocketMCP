#!/usr/bin/env python3
"""TCP Socket MCP Server - Provides raw TCP socket access with buffer management."""

import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, List, Iterable
import uuid
import base64
import re

from mcp.server import Server
from mcp.types import Tool, INTERNAL_ERROR

from .connection import TCPConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TCPSocketServer:
    """MCP Server for TCP Socket operations."""
    
    def __init__(self):
        self.server = Server(
            "TcpSocketMCP",
            version="1.0.0"
        )
        self.connections: Dict[str, TCPConnection] = {}
        self.pending_triggers: Dict[str, Dict[str, Dict[str, Any]]] = {}  # For pre-registered triggers
        self._setup_tools()
    
    def _parse_hex_string(self, hex_str: str) -> bytes:
        """Parse a hex string into bytes. Primary format: plain hex pairs like '48656C6C6F' for 'Hello'.
        Also supports legacy \\xNN format for compatibility."""
        # Remove common hex prefixes and whitespace
        clean_hex = hex_str.replace("0x", "").replace("0X", "").replace(" ", "").replace("\n", "").replace("\r", "")
        
        # If the string contains \x escape sequences, parse them
        if "\\x" in hex_str:
            # Parse \xNN format
            hex_bytes = bytearray()
            # Find all \xNN patterns
            pattern = r'\\x([0-9a-fA-F]{2})'
            matches = re.findall(pattern, hex_str)
            for hex_val in matches:
                hex_bytes.append(int(hex_val, 16))
            # Also include any literal text between hex escapes
            remaining = re.sub(pattern, '\x00', hex_str)
            if remaining and remaining != '\x00' * len(matches):
                # Mix of hex and literal - parse more carefully
                parts = re.split(r'(\\x[0-9a-fA-F]{2})', hex_str)
                hex_bytes = bytearray()
                for part in parts:
                    if part.startswith('\\x') and len(part) == 4:
                        hex_bytes.append(int(part[2:], 16))
                    elif part:
                        hex_bytes.extend(part.encode('utf-8'))
            return bytes(hex_bytes)
        else:
            # Plain hex string like "48656c6c6f"
            try:
                return bytes.fromhex(clean_hex)
            except ValueError as e:
                # If not valid hex, treat as UTF-8
                logger.warning(f"Invalid hex string, treating as UTF-8: {e}")
                return hex_str.encode("utf-8")
    
    def _setup_tools(self):
        """Register all MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="tcp_connect",
                    description="""Open a new TCP connection to any TCP service.

## Typical Workflow
```
1. tcp_connect → returns connection_id
2. tcp_send using that connection_id
3. tcp_read_buffer using that connection_id
4. tcp_disconnect using that connection_id
```

## Notes
- Connection ID is auto-generated if not provided
- **SAVE THE CONNECTION_ID** - You'll need it for ALL subsequent operations
- Always close connections when done to free resources

## Error Conditions
Returns error if:
- Connection refused (service not running)
- Host not found (DNS resolution failed)
- Port out of range (not 1-65535)
- Connection timeout
- Duplicate connection_id specified""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "host": {"type": "string", "description": "Target host address"},
                            "port": {"type": "integer", "description": "Target port number"},
                            "connection_id": {"type": "string", "description": "Optional custom connection ID"}
                        },
                        "required": ["host", "port"]
                    }
                ),
                Tool(
                    name="tcp_disconnect",
                    description="""Close a TCP connection and free resources.

## Required Parameter
- **connection_id** (REQUIRED): The ID of the connection to close

## Notes
- Always close connections when done to free resources
- All associated triggers are automatically removed
- Buffer data is cleared on disconnect

## Error Conditions
Returns error if:
- Connection doesn't exist
- Connection already closed""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID to close"}
                        },
                        "required": ["connection_id"]
                    }
                ),
                Tool(
                    name="tcp_send",
                    description="""Send data over TCP connection.

**Required**: connection_id (from tcp_connect), data

**Encoding options**:
- utf-8 (default): Text with JSON escapes (\r\n for CRLF)
- hex: Plain hex pairs like "48656C6C6F" (recommended for precise byte control)
- base64: Base64 encoded binary

**Terminator**: Optional hex suffix like "0D0A" for CRLF

**Important**: For protocols requiring specific line endings (HTTP, SMTP, IRC), use hex encoding to avoid JSON escape issues. Example: "474554202F20485454502F312E310D0A" instead of "GET / HTTP/1.1\r\n"
**Important**: Only send pairs of hex digits for hex encoding (e.g., "0A" for LF, "0D" for CR) no escaping allowed.

Returns: success, connection_id, bytes_sent""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID from tcp_connect"},
                            "data": {"type": "string", "description": "Data to send (text, hex pairs, or base64)"},
                            "encoding": {"type": "string", "enum": ["utf-8", "base64", "hex"], "description": "Data encoding", "default": "utf-8"},
                            "terminator": {"type": "string", "description": "Optional terminator as hex pairs (e.g., '0D0A' for CRLF)"}
                        },
                        "required": ["connection_id", "data"]
                    }
                ),
                Tool(
                    name="tcp_read_buffer",
                    description="""Read received data from connection's buffer.

## Required Parameter
- **connection_id** (REQUIRED): The ID from tcp_connect

## Format Options
- **utf-8** (default): Text format, replaces invalid bytes with �
- **hex**: Hexadecimal format for binary analysis
- **base64**: Base64 encoded binary data

## Parameters
- **index** (optional): Starting position in buffer
- **count** (optional): Number of chunks to read
- **format** (optional): Output format

## Usage Examples

## Important Notes
- **Timing**: After tcp_send, received data may not be immediately available. Try:
  1. Wait 1-2 seconds after sending
  2. Call tcp_read_buffer multiple times
  3. Use tcp_buffer_info first to check if data has arrived
- Buffer stores all received data until cleared
- Data is stored in chunks as received
- Use hex format for debugging binary protocols
- Index is 0-based
- **tcp_read_buffer**: Actually retrieves and displays the data
- **tcp_buffer_info**: Check if data exists without consuming it

## Troubleshooting
- **Empty response?** Wait longer or check multiple times - network responses take time
- **Partial data?** Keep reading - data may arrive in multiple chunks
- **Binary data looks corrupted?** Use `format: "hex"` for binary protocols

## Error Conditions
Returns error if:
- Connection doesn't exist
- Invalid format specified""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"},
                            "index": {"type": "integer", "description": "Starting index in buffer"},
                            "count": {"type": "integer", "description": "Number of chunks to read"},
                            "format": {"type": "string", "enum": ["utf-8", "hex", "base64"], "description": "Output format", "default": "utf-8"}
                        },
                        "required": ["connection_id"]
                    }
                ),
                Tool(
                    name="tcp_clear_buffer",
                    description="""Clear all received data from connection's buffer.

## Required Parameter
- **connection_id** (REQUIRED): The ID from tcp_connect

## When to Use
- Between different protocol phases
- After processing received data
- To free memory for long-running connections
- When switching communication modes

## Notes
- Irreversible operation - data cannot be recovered
- Does not affect connection state
- Triggers remain active

## Error Conditions
Returns error if:
- Connection doesn't exist""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"}
                        },
                        "required": ["connection_id"]
                    }
                ),
                Tool(
                    name="tcp_buffer_info",
                    description="""Get detailed buffer statistics for a connection.

## Required Parameter
- **connection_id** (REQUIRED): The ID from tcp_connect

## Statistics Provided
- **chunks**: Number of data chunks in buffer
- **total_size**: Total bytes in buffer
- **bytes_received**: Total bytes received since connection
- **bytes_sent**: Total bytes sent since connection
- **last_received**: Timestamp of last received data

## Use Cases
- Monitor data flow
- Debug communication issues  
- Check buffer growth
- Performance analysis
- Memory usage tracking
- **Check if data exists without consuming it** (unlike tcp_read_buffer which retrieves data)

## Error Conditions
Returns error if:
- Connection doesn't exist""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"}
                        },
                        "required": ["connection_id"]
                    }
                ),
                Tool(
                    name="tcp_set_trigger",
                    description="""Set automatic response for pattern matches.

**Pre-Registration**: Set triggers BEFORE connecting - they activate automatically on connection.

**Required**: connection_id, trigger_id, pattern (regex), response

**Pattern**: Full regex support with capture groups ($1, $2, etc.)

**Response encoding**: utf-8, hex (recommended for binary), base64

**Response terminator**: Optional hex suffix


**Use hex encoding for binary patterns and responses for best results.**

Returns: success, connection_id, trigger_id, status ("active" or "pending")""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"},
                            "trigger_id": {"type": "string", "description": "Unique trigger ID"},
                            "pattern": {"type": "string", "description": "Regex pattern to match"},
                            "response": {"type": "string", "description": "Response data to send"},
                            "response_encoding": {"type": "string", "enum": ["utf-8", "base64", "hex"], "description": "Response encoding", "default": "utf-8"},
                            "response_terminator": {"type": "string", "description": "Optional terminator as hex pairs"}
                        },
                        "required": ["connection_id", "trigger_id", "pattern", "response"]
                    }
                ),
                Tool(
                    name="tcp_remove_trigger",
                    description="""Remove a previously set auto-response trigger.

## Required Parameters
- **connection_id** (REQUIRED): The ID from tcp_connect
- **trigger_id** (REQUIRED): The trigger ID to remove

## When to Use
- Changing protocol states
- Disabling specific auto-responses
- Updating trigger patterns (remove then re-add)
- Cleanup before disconnect

## Notes
- Use the same trigger_id that was used in tcp_set_trigger
- All triggers removed automatically on disconnect

## Error Conditions
Returns error if:
- Connection doesn't exist
- Trigger_id not found""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"},
                            "trigger_id": {"type": "string", "description": "Trigger ID to remove"}
                        },
                        "required": ["connection_id", "trigger_id"]
                    }
                ),
                Tool(
                    name="tcp_connect_and_send",
                    description="""Connect and immediately send data in one operation. Useful for protocols that require immediate handshakes or banner grabbing. Also prefer over separate connect/send calls if immediately sending data upon connection (eg http requests).

**Required**: host, port, data

**Use for**: Time-sensitive protocols, immediate handshakes, banner grabbing

**Encoding**: utf-8, hex (recommended for binary), base64

**Terminator**: Optional hex suffix

**Encoding options**:
- utf-8 (default): Text with JSON escapes (\r\n for CRLF)
- hex: Plain hex pairs like "48656C6C6F" (recommended for precise byte control)
- base64: Base64 encoded binary

**Terminator**: Optional hex suffix like "0D0A" for CRLF

**Important**: For protocols requiring specific line endings (HTTP, SMTP, IRC), use hex encoding to avoid JSON escape issues. Example: "474554202F20485454502F312E310D0A" instead of "GET / HTTP/1.1\r\n"
**Important**: Only send pairs of hex digits for hex encoding (e.g., "0A" for LF, "0D" for CR) no escaping allowed.

Returns: success, connection_id, bytes_sent, immediate_response (if any)""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "host": {"type": "string", "description": "Target host address"},
                            "port": {"type": "integer", "description": "Target port number"},
                            "data": {"type": "string", "description": "Data to send immediately"},
                            "connection_id": {"type": "string", "description": "Optional custom connection ID"},
                            "encoding": {"type": "string", "enum": ["utf-8", "base64", "hex"], "description": "Data encoding", "default": "utf-8"},
                            "terminator": {"type": "string", "description": "Optional terminator as hex pairs"}
                        },
                        "required": ["host", "port", "data"]
                    }
                ),
                Tool(
                    name="tcp_list_connections",  
                    description="""List all active TCP connections with statistics.

## Information Provided
- **connection_id**: Unique identifier for connection
- **host**: Target hostname or IP
- **port**: Target port number
- **connected**: Connection status
- **bytes_sent**: Total bytes sent
- **bytes_received**: Total bytes received
- **buffer_chunks**: Number of unread data chunks
- **triggers**: Number of active triggers

## Use Cases
- Manage multiple simultaneous connections
- Monitor resource usage
- Debug connection issues
- Get overview of active sessions""",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="tcp_connection_info",
                    description="""Get detailed information about a specific connection.

## Required Parameter
- **connection_id** (REQUIRED): The ID of the connection to inspect

## Information Provided

### Connection Details
- **connection_id**: Unique identifier
- **host**: Target hostname or IP
- **port**: Target port number
- **connected**: Current connection status
- **created_at**: Connection creation timestamp

### Buffer Statistics
- **chunks**: Number of data chunks in buffer
- **total_size**: Total bytes in buffer
- **bytes_received**: Total received since connection
- **bytes_sent**: Total sent since connection
- **last_received**: Last data reception timestamp

### Active Triggers
- **trigger_id**: Unique trigger identifier
- **pattern**: Regex pattern being matched
- **response_length**: Length of response data

## Use Cases
- Debug specific connection issues
- Monitor connection health
- View active triggers
- Track data flow
- Analyze buffer growth

## Error Conditions
Returns error if:
- Connection doesn't exist""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"}
                        },
                        "required": ["connection_id"]
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls and return content blocks."""
            try:
                if name == "tcp_connect":
                    return await self._handle_connect(arguments)
                elif name == "tcp_disconnect":
                    return await self._handle_disconnect(arguments)
                elif name == "tcp_send":
                    return await self._handle_send(arguments)
                elif name == "tcp_read_buffer":
                    return await self._handle_read_buffer(arguments)
                elif name == "tcp_clear_buffer":
                    return await self._handle_clear_buffer(arguments)
                elif name == "tcp_buffer_info":
                    return await self._handle_buffer_info(arguments)
                elif name == "tcp_set_trigger":
                    return await self._handle_set_trigger(arguments)
                elif name == "tcp_remove_trigger":
                    return await self._handle_remove_trigger(arguments)
                elif name == "tcp_list_connections":
                    return await self._handle_list_connections()
                elif name == "tcp_connection_info":
                    return await self._handle_connection_info(arguments)
                elif name == "tcp_connect_and_send":
                    return await self._handle_connect_and_send(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                # Return error as text content
                return [{
                    "type": "text",
                    "text": json.dumps({"error": str(e)})
                }]
    
    async def _handle_connect(self, args: Dict[str, Any]):
        """Handle TCP connection request."""
        host = args["host"]
        port = args["port"]
        connection_id = args.get("connection_id", str(uuid.uuid4()))
        
        if connection_id in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "duplicate_id",
                    "message": f"Connection ID {connection_id} already exists"
                })
            }]
        
        conn = TCPConnection(connection_id, host, port)
        success = await conn.connect()
        
        if success:
            self.connections[connection_id] = conn
            
            # Apply any pending triggers for this connection
            applied_triggers = []
            if connection_id in self.pending_triggers:
                for trigger_id, trigger_data in self.pending_triggers[connection_id].items():
                    conn.add_trigger(trigger_id, trigger_data["pattern"], trigger_data["response"])
                    applied_triggers.append(trigger_id)
                # Remove from pending triggers
                del self.pending_triggers[connection_id]
            
            result = {
                "success": True,
                "connection_id": connection_id,
                "host": host,
                "port": port,
                "status": "connected"
            }
            
            if applied_triggers:
                result["applied_triggers"] = applied_triggers
                result["message"] = f"Applied {len(applied_triggers)} pre-registered trigger(s)"
            
            return [{
                "type": "text",
                "text": json.dumps(result)
            }]
        else:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "connection_failed",
                    "message": f"Failed to connect to {host}:{port}"
                })
            }]
    
    async def _handle_disconnect(self, args: Dict[str, Any]):
        """Handle disconnection request."""
        connection_id = args["connection_id"]
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        await self.connections[connection_id].disconnect()
        del self.connections[connection_id]
        
        return [{
            "type": "text",
            "text": json.dumps({
                "success": True,
                "connection_id": connection_id,
                "status": "disconnected"
            })
        }]
    
    async def _handle_send(self, args: Dict[str, Any]):
        """Handle sending data."""
        connection_id = args["connection_id"]
        data_str = args["data"]
        encoding = args.get("encoding", "utf-8")
        terminator_str = args.get("terminator")
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        # Convert data based on encoding
        if encoding == "base64":
            data = base64.b64decode(data_str)
        elif encoding == "hex":
            data = self._parse_hex_string(data_str)
        else:
            data = data_str.encode("utf-8")
        
        # Add terminator if specified
        if terminator_str:
            terminator = self._parse_hex_string(terminator_str)
            data = data + terminator
        
        conn = self.connections[connection_id]
        success = await conn.send(data)
        
        if success:
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "connection_id": connection_id,
                    "bytes_sent": len(data)
                })
            }]
        else:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "send_failed",
                    "message": "Failed to send data"
                })
            }]
    
    async def _handle_read_buffer(self, args: Dict[str, Any]):
        """Handle reading from buffer."""
        connection_id = args["connection_id"]
        index = args.get("index")
        count = args.get("count")
        format_type = args.get("format", "utf-8")
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        conn = self.connections[connection_id]
        buffer_data = await conn.read_buffer(index, count)
        
        # Format the output
        formatted_data = []
        for chunk in buffer_data:
            if format_type == "hex":
                formatted_data.append(chunk.hex())
            elif format_type == "base64":
                formatted_data.append(base64.b64encode(chunk).decode('ascii'))
            else:  # utf-8
                formatted_data.append(chunk.decode('utf-8', errors='replace'))
        
        return [{
            "type": "text",
            "text": json.dumps({
                "connection_id": connection_id,
                "chunks": len(formatted_data),
                "data": formatted_data,
                "format": format_type
            })
        }]
    
    async def _handle_clear_buffer(self, args: Dict[str, Any]):
        """Handle clearing buffer."""
        connection_id = args["connection_id"]
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        await self.connections[connection_id].clear_buffer()
        
        return [{
            "type": "text",
            "text": json.dumps({
                "success": True,
                "connection_id": connection_id,
                "buffer_cleared": True
            })
        }]
    
    async def _handle_buffer_info(self, args: Dict[str, Any]):
        """Handle getting buffer info."""
        connection_id = args["connection_id"]
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        info = await self.connections[connection_id].get_buffer_info()
        
        return [{
            "type": "text",
            "text": json.dumps(info)
        }]
    
    async def _handle_set_trigger(self, args: Dict[str, Any]):
        """Handle setting a trigger."""
        connection_id = args["connection_id"]
        trigger_id = args["trigger_id"]
        pattern = args["pattern"]
        response_str = args["response"]
        response_encoding = args.get("response_encoding", "utf-8")
        response_terminator_str = args.get("response_terminator")
        
        # Convert response based on encoding
        if response_encoding == "base64":
            response = base64.b64decode(response_str)
        elif response_encoding == "hex":
            response = self._parse_hex_string(response_str)
        else:
            response = response_str.encode("utf-8")
        
        # Add terminator if specified
        if response_terminator_str:
            terminator = self._parse_hex_string(response_terminator_str)
            response = response + terminator
        
        # Check if connection exists
        if connection_id in self.connections:
            # Connection exists, add trigger directly
            conn = self.connections[connection_id]
            conn.add_trigger(trigger_id, pattern, response)
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "connection_id": connection_id,
                    "trigger_id": trigger_id,
                    "pattern": pattern,
                    "status": "active"
                })
            }]
        else:
            # Connection doesn't exist, store as pending trigger
            if connection_id not in self.pending_triggers:
                self.pending_triggers[connection_id] = {}
            
            self.pending_triggers[connection_id][trigger_id] = {
                "pattern": pattern,
                "response": response,  # Already encoded
                "response_str": response_str,  # Keep original for later
                "response_encoding": response_encoding,
                "response_terminator_str": response_terminator_str
            }
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "connection_id": connection_id,
                    "trigger_id": trigger_id,
                    "pattern": pattern,
                    "status": "pending",
                    "message": "Trigger pre-registered and will activate when connection is established"
                })
            }]
    
    async def _handle_remove_trigger(self, args: Dict[str, Any]):
        """Handle removing a trigger."""
        connection_id = args["connection_id"]
        trigger_id = args["trigger_id"]
        
        # Check if it's an active connection
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            success = conn.remove_trigger(trigger_id)
            
            if success:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "connection_id": connection_id,
                        "trigger_id": trigger_id,
                        "status": "removed_active"
                    })
                }]
            else:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "not_found",
                        "message": f"Trigger {trigger_id} not found on active connection"
                    })
                }]
        
        # Check if it's a pending trigger
        elif connection_id in self.pending_triggers:
            if trigger_id in self.pending_triggers[connection_id]:
                del self.pending_triggers[connection_id][trigger_id]
                
                # Clean up empty pending connection
                if not self.pending_triggers[connection_id]:
                    del self.pending_triggers[connection_id]
                
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "connection_id": connection_id,
                        "trigger_id": trigger_id,
                        "status": "removed_pending"
                    })
                }]
            else:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "not_found",
                        "message": f"Trigger {trigger_id} not found in pending triggers"
                    })
                }]
        
        # Connection doesn't exist at all
        else:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found (neither active nor pending)"
                })
            }]
    
    async def _handle_list_connections(self):
        """Handle listing all connections."""
        connections_list = []
        for conn_id, conn in self.connections.items():
            info = await conn.get_buffer_info()
            connections_list.append({
                "connection_id": conn_id,
                "host": conn.host,
                "port": conn.port,
                "connected": conn.connected,
                "bytes_sent": info["bytes_sent"],
                "bytes_received": info["bytes_received"],
                "buffer_chunks": info["chunks"],
                "triggers": len(conn.triggers)
            })
        
        return [{
            "type": "text",
            "text": json.dumps({
                "total_connections": len(connections_list),
                "connections": connections_list
            })
        }]
    
    async def _handle_connection_info(self, args: Dict[str, Any]):
        """Handle getting detailed connection info."""
        connection_id = args["connection_id"]
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        conn = self.connections[connection_id]
        buffer_info = await conn.get_buffer_info()
        triggers = conn.get_triggers()
        
        info = {
            "connection_id": connection_id,
            "host": conn.host,
            "port": conn.port,
            "connected": conn.connected,
            "created_at": conn.created_at.isoformat(),
            "buffer": buffer_info,
            "triggers": triggers
        }
        
        return [{
            "type": "text",
            "text": json.dumps(info)
        }]
    
    async def _handle_connect_and_send(self, args: Dict[str, Any]):
        """Handle connecting and immediately sending data."""
        host = args["host"]
        port = args["port"]
        data_str = args["data"]
        connection_id = args.get("connection_id", str(uuid.uuid4()))
        encoding = args.get("encoding", "utf-8")
        terminator_str = args.get("terminator")
        
        # Check if connection_id already exists
        if connection_id in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "duplicate_id",
                    "message": f"Connection ID {connection_id} already exists"
                })
            }]
        
        # Create and connect
        conn = TCPConnection(connection_id, host, port)
        success = await conn.connect()
        
        if not success:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "connection_failed",
                    "message": f"Failed to connect to {host}:{port}"
                })
            }]
        
        # Store connection
        self.connections[connection_id] = conn
        
        # Apply any pending triggers for this connection
        applied_triggers = []
        if connection_id in self.pending_triggers:
            for trigger_id, trigger_data in self.pending_triggers[connection_id].items():
                conn.add_trigger(trigger_id, trigger_data["pattern"], trigger_data["response"])
                applied_triggers.append(trigger_id)
            # Remove from pending triggers
            del self.pending_triggers[connection_id]
        
        # Convert data based on encoding
        if encoding == "base64":
            data = base64.b64decode(data_str)
        elif encoding == "hex":
            data = self._parse_hex_string(data_str)
        else:
            data = data_str.encode("utf-8")
        
        # Add terminator if specified
        if terminator_str:
            terminator = self._parse_hex_string(terminator_str)
            data = data + terminator
        
        # Send data immediately
        send_success = await conn.send(data)
        
        if not send_success:
            # Connection failed during send, clean up
            await conn.disconnect()
            del self.connections[connection_id]
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "send_failed",
                    "message": f"Connected but failed to send data to {host}:{port}"
                })
            }]
        
        # Wait a brief moment for any immediate response
        await asyncio.sleep(0.1)
        
        # Check for any immediate data in buffer
        buffer_info = await conn.get_buffer_info()
        
        result = {
            "success": True,
            "connection_id": connection_id,
            "host": host,
            "port": port,
            "bytes_sent": len(data),
            "status": "connected",
            "immediate_response": buffer_info["chunks"] > 0,
            "buffer_chunks": buffer_info["chunks"]
        }
        
        if applied_triggers:
            result["applied_triggers"] = applied_triggers
            result["message"] = f"Applied {len(applied_triggers)} pre-registered trigger(s)"
        
        return [{
            "type": "text",
            "text": json.dumps(result)
        }]
    
    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = TCPSocketServer()
    await server.run()


def main_sync():
    """Synchronous main for script entry."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()