#!/usr/bin/env python3
"""Simple test for tcp_connect_and_send tool."""

import asyncio
import sys
import os
import json

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tcp_socket_mcp.server import TCPSocketServer

async def test_connect_and_send():
    """Test the tcp_connect_and_send tool."""
    server = TCPSocketServer()
    
    print("Testing tcp_connect_and_send tool...")
    print("-" * 50)
    
    # Test 1: Basic HTTP request
    print("\nTest 1: HTTP GET request to httpbin.org")
    args = {
        "host": "httpbin.org",
        "port": 80,
        "data": "GET /status/200 HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n",
        "connection_id": "test-http"
    }
    
    result = await server._handle_connect_and_send(args)
    response = json.loads(result[0]["text"])
    
    print(f"Success: {response.get('success', False)}")
    print(f"Connection ID: {response.get('connection_id', 'N/A')}")
    print(f"Bytes sent: {response.get('bytes_sent', 0)}")
    print(f"Immediate response: {response.get('immediate_response', False)}")
    print(f"Buffer chunks: {response.get('buffer_chunks', 0)}")
    
    # Give time for response
    await asyncio.sleep(1)
    
    # Check buffer
    if response.get('success') and "test-http" in server.connections:
        try:
            buffer_result = await server._handle_read_buffer({
                "connection_id": "test-http",
                "count": 1
            })
            buffer_data = json.loads(buffer_result[0]["text"])
            if buffer_data.get("data"):
                print(f"\nReceived response (first 200 chars): {buffer_data['data'][0][:200]}...")
        except Exception as e:
            print(f"Error reading buffer: {e}")
    
    # Clean up
    if "test-http" in server.connections:
        try:
            await server._handle_disconnect({"connection_id": "test-http"})
        except Exception:
            pass
    
    print("\n" + "-" * 50)
    
    # Test 2: With hex encoding
    print("\nTest 2: With hex encoding")
    # This hex string is: "HEAD / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
    args2 = {
        "host": "httpbin.org",
        "port": 80,
        "data": "48454144202f20485454502f312e310d0a486f73743a20687474706262696e2e6f72670d0a436f6e6e656374696f6e3a20636c6f73650d0a0d0a",
        "encoding": "hex",
        "connection_id": "test-hex"
    }
    
    try:
        result2 = await server._handle_connect_and_send(args2)
        response2 = json.loads(result2[0]["text"])
        
        print(f"Success: {response2.get('success', False)}")
        print(f"Bytes sent: {response2.get('bytes_sent', 0)}")
    except Exception as e:
        print(f"Test 2 error: {e}")
    
    # Clean up
    if "test-hex" in server.connections:
        try:
            await server._handle_disconnect({"connection_id": "test-hex"})
        except Exception:
            pass
    
    print("\n" + "-" * 50)
    
    # Test 3: With terminator
    print("\nTest 3: With custom terminator")
    args3 = {
        "host": "httpbin.org",
        "port": 80,
        "data": "GET /status/200 HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close",
        "terminator": "\\x0d\\x0a\\x0d\\x0a",
        "connection_id": "test-term"
    }
    
    try:
        result3 = await server._handle_connect_and_send(args3)
        response3 = json.loads(result3[0]["text"])
        
        print(f"Success: {response3.get('success', False)}")
        print(f"Bytes sent: {response3.get('bytes_sent', 0)}")
    except Exception as e:
        print(f"Test 3 error: {e}")
    
    # Clean up
    if "test-term" in server.connections:
        try:
            await server._handle_disconnect({"connection_id": "test-term"})
        except Exception:
            pass
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(test_connect_and_send(), timeout=5))
    except asyncio.TimeoutError:
        print("\nTest timed out after 5 seconds")
    except Exception as e:
        print(f"\nTest error: {e}")