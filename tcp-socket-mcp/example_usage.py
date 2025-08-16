#!/usr/bin/env python3
"""Example usage of the TCP Socket MCP server for testing."""

import asyncio
import json
from src.tcp_socket_mcp.connection import TCPConnection


async def example_echo_server():
    """
    Example: Create a simple echo server for testing.
    Run this first, then use the MCP tools to connect to it.
    """
    print("Starting Echo Server on port 9999...")
    
    async def handle_client(reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Client connected from {addr}")
        
        while True:
            try:
                data = await reader.read(1024)
                if not data:
                    break
                
                message = data.decode('utf-8', errors='ignore')
                print(f"Received: {message}")
                
                # Echo back
                writer.write(f"ECHO: {message}".encode())
                await writer.drain()
                
            except Exception as e:
                print(f"Error: {e}")
                break
        
        print(f"Client {addr} disconnected")
        writer.close()
        await writer.wait_closed()
    
    server = await asyncio.start_server(handle_client, 'localhost', 9999)
    
    addr = server.sockets[0].getsockname()
    print(f"Echo server listening on {addr[0]}:{addr[1]}")
    print("\nYou can now test the MCP server by:")
    print('1. Run MCP Inspector: mcp-inspector python -m tcp_socket_mcp.server')
    print('2. Use tcp_connect with host="localhost" and port=9999')
    print('3. Send data with tcp_send')
    print('4. Read responses with tcp_read_buffer')
    print("\nPress Ctrl+C to stop the echo server")
    
    async with server:
        await server.serve_forever()


async def example_http_test():
    """Example of making an HTTP request using the TCP connection directly."""
    print("Example HTTP Request Test")
    print("=" * 50)
    
    # Create a connection
    conn = TCPConnection("http-test", "httpbin.org", 80)
    
    # Connect
    success = await conn.connect()
    if not success:
        print("Failed to connect")
        return
    
    print("✓ Connected to httpbin.org:80")
    
    # Send HTTP GET request
    request = b"GET /get HTTP/1.1\r\nHost: httpbin.org\r\n\r\n"
    await conn.send(request)
    print(f"✓ Sent {len(request)} bytes")
    
    # Wait for response
    await asyncio.sleep(1)
    
    # Read buffer
    buffer = await conn.read_buffer()
    if buffer:
        response = b''.join(buffer).decode('utf-8', errors='ignore')
        print("\n✓ Received response:")
        print("-" * 40)
        print(response[:500])  # First 500 chars
        if len(response) > 500:
            print(f"... ({len(response)} total bytes)")
        print("-" * 40)
    
    # Get buffer info
    info = await conn.get_buffer_info()
    print(f"\n✓ Buffer info: {json.dumps(info, indent=2)}")
    
    # Disconnect
    await conn.disconnect()
    print("✓ Disconnected")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "echo":
        # Run echo server
        try:
            asyncio.run(example_echo_server())
        except KeyboardInterrupt:
            print("\nEcho server stopped")
    else:
        # Run HTTP test
        asyncio.run(example_http_test())
        print("\nTo run the echo server: python example_usage.py echo")