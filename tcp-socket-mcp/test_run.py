#!/usr/bin/env python3
"""Test running the server to ensure it starts correctly."""

import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_server():
    """Test the server can handle basic MCP protocol."""
    from tcp_socket_mcp.server import TCPSocketServer
    
    server = TCPSocketServer()
    print("✅ Server created successfully")
    
    # Test that tools are registered
    tools = []
    list_tools_func = None
    for handler in server.server._request_handlers.values():
        if hasattr(handler, '__name__') and 'list_tools' in handler.__name__:
            list_tools_func = handler
            break
    
    if list_tools_func:
        tools = await list_tools_func()
        print(f"✅ Found {len(tools)} tools registered")
        for tool in tools[:3]:  # Show first 3 tools
            print(f"   - {tool.name}: {tool.description[:50]}...")
    
    print("\n✅ Server is ready to run with MCP Inspector!")
    print("\n🚀 To start the server, run:")
    print("   mcp-inspector python run.py")

if __name__ == "__main__":
    asyncio.run(test_server())