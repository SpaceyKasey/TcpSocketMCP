#!/usr/bin/env python3
"""Inspect the MCP Server object to understand its API."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp.server import Server, InitializationOptions
from tcp_socket_mcp.server import TCPSocketServer

# Create servers
mcp_server = Server("test")
tcp_server = TCPSocketServer()

print("MCP Server attributes:")
attrs = [attr for attr in dir(mcp_server) if not attr.startswith('__')]
for attr in sorted(attrs):
    print(f"  - {attr}")

print("\nLooking for handlers...")
if hasattr(mcp_server, 'request_handlers'):
    print(f"  ✓ request_handlers: {mcp_server.request_handlers}")
if hasattr(mcp_server, '_handlers'):
    print(f"  ✓ _handlers: {mcp_server._handlers}")

print("\n✅ Server inspection complete")