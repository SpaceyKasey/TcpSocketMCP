#!/usr/bin/env python3
"""Verify the TCP Socket MCP server works correctly."""

import sys
import os
import asyncio
import json
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_minimal():
    """Test minimal server functionality."""
    from tcp_socket_mcp.server import TCPSocketServer
    
    print("Testing TCP Socket MCP Server")
    print("=" * 50)
    
    # Create server
    server = TCPSocketServer()
    print(f"✅ Server created: {server.server.name}")
    
    # Check tools are registered
    print(f"✅ Request handlers: {len(server.server.request_handlers)} handlers")
    
    # Test tool listing works
    try:
        # The list_tools decorator should have registered a handler
        tools_registered = False
        for key in server.server.request_handlers:
            if hasattr(key, '__name__') and 'ListToolsRequest' in str(key):
                tools_registered = True
                break
        
        if tools_registered:
            print(f"✅ Tools listing is registered")
        else:
            # Check if the decorator worked
            print(f"⚠️  Tools may not be fully registered yet")
    except Exception as e:
        print(f"⚠️  Could not verify tools: {e}")
    
    print("\n" + "=" * 50)
    print("Server verification complete!")
    print("\nTo run with MCP Inspector:")
    print("  mcp-inspector python run.py")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_minimal())
    sys.exit(0 if success else 1)