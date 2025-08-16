#!/usr/bin/env python3
"""Test that the MCP server can be imported and initialized."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from tcp_socket_mcp.server import TCPSocketServer
    server = TCPSocketServer()
    print("✅ SUCCESS: MCP Server initialized correctly!")
    print(f"✅ Server name: {server.server.name}")
    print("✅ Ready to use with: mcp-inspector python run.py")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()