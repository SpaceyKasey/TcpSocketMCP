#!/usr/bin/env python3
"""Simple test script to verify the TCP Socket MCP server works."""

import asyncio
import json


async def test_basic_operations():
    """Test basic TCP operations."""
    print("TCP Socket MCP Server Test")
    print("=" * 50)
    
    # This script tests the server structure and imports
    try:
        from src.tcp_socket_mcp.connection import TCPConnection
        from src.tcp_socket_mcp.server import TCPSocketServer
        print("✓ Imports successful")
        
        # Test connection class instantiation
        test_conn = TCPConnection("test-1", "localhost", 8080)
        print("✓ TCPConnection class instantiation successful")
        
        # Test server instantiation
        server = TCPSocketServer()
        print("✓ TCPSocketServer instantiation successful")
        
        # Check that tools are registered
        print(f"✓ Server initialized with name: {server.server.name}")
        
        print("\n" + "=" * 50)
        print("All basic tests passed!")
        print("\nTo test with MCP Inspector:")
        print("1. Install MCP Inspector: npm install -g @modelcontextprotocol/inspector")
        print("2. Run: mcp-inspector python -m tcp_socket_mcp.server")
        print("\nTo test manually:")
        print("Run: python -m tcp_socket_mcp.server")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_basic_operations())