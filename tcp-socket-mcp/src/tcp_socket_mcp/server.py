#!/usr/bin/env python3
"""TCP Socket MCP Server - Provides raw TCP socket access with buffer management."""

import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, List, Iterable
import uuid
import base64

from mcp.server import Server
from mcp.types import Tool, INTERNAL_ERROR

from .connection import TCPConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TCPSocketServer:
    """MCP Server for TCP Socket operations."""
    
    def __init__(self):
        self.server = Server("tcp-socket-mcp")
        self.connections: Dict[str, TCPConnection] = {}
        self._setup_tools()
    
    def _setup_tools(self):
        """Register all MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="tcp_connect",
                    description="Open a new TCP connection to a host and port",
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
                    description="Close a TCP connection",
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
                    description="Send raw data over a TCP connection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"},
                            "data": {"type": "string", "description": "Data to send (base64 encoded for binary)"},
                            "encoding": {"type": "string", "enum": ["utf-8", "base64"], "description": "Data encoding", "default": "utf-8"}
                        },
                        "required": ["connection_id", "data"]
                    }
                ),
                Tool(
                    name="tcp_read_buffer",
                    description="Read data from a connection's buffer",
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
                    description="Clear a connection's buffer",
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
                    description="Get information about a connection's buffer",
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
                    description="Set a trigger to auto-respond when pattern is received",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"},
                            "trigger_id": {"type": "string", "description": "Unique trigger ID"},
                            "pattern": {"type": "string", "description": "Regex pattern to match"},
                            "response": {"type": "string", "description": "Response data to send"},
                            "response_encoding": {"type": "string", "enum": ["utf-8", "base64"], "description": "Response encoding", "default": "utf-8"}
                        },
                        "required": ["connection_id", "trigger_id", "pattern", "response"]
                    }
                ),
                Tool(
                    name="tcp_remove_trigger",
                    description="Remove a trigger from a connection",
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
                    name="tcp_list_connections",
                    description="List all active TCP connections",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="tcp_connection_info",
                    description="Get detailed information about a connection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connection_id": {"type": "string", "description": "Connection ID"}
                        },
                        "required": ["connection_id"]
                    }
                )
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
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "connection_id": connection_id,
                    "host": host,
                    "port": port,
                    "status": "connected"
                })
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
        else:
            data = data_str.encode("utf-8")
        
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
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        # Convert response based on encoding
        if response_encoding == "base64":
            response = base64.b64decode(response_str)
        else:
            response = response_str.encode("utf-8")
        
        conn = self.connections[connection_id]
        conn.add_trigger(trigger_id, pattern, response)
        
        return [{
            "type": "text",
            "text": json.dumps({
                "success": True,
                "connection_id": connection_id,
                "trigger_id": trigger_id,
                "pattern": pattern
            })
        }]
    
    async def _handle_remove_trigger(self, args: Dict[str, Any]):
        """Handle removing a trigger."""
        connection_id = args["connection_id"]
        trigger_id = args["trigger_id"]
        
        if connection_id not in self.connections:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Connection {connection_id} not found"
                })
            }]
        
        conn = self.connections[connection_id]
        success = conn.remove_trigger(trigger_id)
        
        if success:
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "connection_id": connection_id,
                    "trigger_id": trigger_id
                })
            }]
        else:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "not_found",
                    "message": f"Trigger {trigger_id} not found"
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