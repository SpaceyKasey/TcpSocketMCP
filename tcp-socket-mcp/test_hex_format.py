#!/usr/bin/env python3
"""Test the simplified hex format for tcp_send."""

import asyncio
import sys
import os
import json

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tcp_socket_mcp.server import TCPSocketServer

async def test_hex_formats():
    """Test different hex format options."""
    server = TCPSocketServer()
    
    print("Testing Hex Format Changes")
    print("=" * 50)
    
    # Test the _parse_hex_string method directly
    print("\n1. Testing _parse_hex_string method:")
    
    # Test plain hex pairs (new recommended format)
    test_cases = [
        ("48656C6C6F", b"Hello"),  # Plain hex pairs
        ("48656c6c6f", b"Hello"),  # Lowercase
        ("0D0A", b"\r\n"),  # CRLF
        ("474554202F20485454502F312E310D0A", b"GET / HTTP/1.1\r\n"),  # HTTP request
        ("\\x48\\x65\\x6C\\x6C\\x6F", b"Hello"),  # Legacy format still works
    ]
    
    for hex_input, expected in test_cases:
        result = server._parse_hex_string(hex_input)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{hex_input[:20]}...' -> {repr(result)}")
    
    print("\n2. Testing tcp_send with plain hex format:")
    
    # Connect to a test server
    connect_args = {
        "host": "httpbin.org",
        "port": 80,
        "connection_id": "hex-test"
    }
    
    connect_result = await server._handle_connect(connect_args)
    connect_response = json.loads(connect_result[0]["text"])
    
    if connect_response.get("success"):
        print(f"  Connected: {connect_response['connection_id']}")
        
        # Test 1: Send HTTP request using plain hex
        hex_data = "474554202F737461747573" "2F32303020485454502F31" "2E310D0A486F73743A2068" "747470" "62696E2E6F72670D0A436F" "6E6E656374696F6E3A2063" "6C6F73650D0A0D0A"
        # This is: "GET /status/200 HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
        
        send_args = {
            "connection_id": "hex-test",
            "data": hex_data,
            "encoding": "hex"
        }
        
        send_result = await server._handle_send(send_args)
        send_response = json.loads(send_result[0]["text"])
        
        print(f"  Sent {send_response.get('bytes_sent', 0)} bytes using plain hex")
        
        # Wait for response
        await asyncio.sleep(0.5)
        
        # Read response
        read_args = {
            "connection_id": "hex-test",
            "count": 1
        }
        
        read_result = await server._handle_read_buffer(read_args)
        read_response = json.loads(read_result[0]["text"])
        
        if read_response.get("data"):
            print(f"  Received response: {read_response['data'][0][:100]}...")
        
        # Clean up
        await server._handle_disconnect({"connection_id": "hex-test"})
    
    print("\n3. Testing terminator as plain hex:")
    
    # Connect again
    connect_args2 = {
        "host": "httpbin.org",
        "port": 80,
        "connection_id": "term-test"
    }
    
    connect_result2 = await server._handle_connect(connect_args2)
    connect_response2 = json.loads(connect_result2[0]["text"])
    
    if connect_response2.get("success"):
        # Send with plain hex terminator
        send_args2 = {
            "connection_id": "term-test",
            "data": "GET /status/200 HTTP/1.1",
            "terminator": "0D0A"  # Plain hex for CRLF
        }
        
        send_result2 = await server._handle_send(send_args2)
        send_response2 = json.loads(send_result2[0]["text"])
        print(f"  Sent with plain hex terminator: {send_response2.get('bytes_sent', 0)} bytes")
        
        # Send more lines
        await server._handle_send({
            "connection_id": "term-test", 
            "data": "Host: httpbin.org",
            "terminator": "0D0A"
        })
        
        await server._handle_send({
            "connection_id": "term-test",
            "data": "Connection: close",
            "terminator": "0D0A0D0A"  # Double CRLF
        })
        
        # Wait and read
        await asyncio.sleep(0.5)
        read_result2 = await server._handle_read_buffer({"connection_id": "term-test", "count": 1})
        read_response2 = json.loads(read_result2[0]["text"])
        
        if read_response2.get("data"):
            print(f"  Received: {read_response2['data'][0][:50]}...")
        
        # Clean up
        await server._handle_disconnect({"connection_id": "term-test"})
    
    print("\n4. Testing pre-registered trigger with plain hex:")
    
    # Pre-register trigger with hex response
    trigger_args = {
        "connection_id": "trigger-test",
        "trigger_id": "hex-response",
        "pattern": "^PING",
        "response": "504F4E470D0A",  # "PONG\r\n" in plain hex
        "response_encoding": "hex"
    }
    
    trigger_result = await server._handle_set_trigger(trigger_args)
    trigger_response = json.loads(trigger_result[0]["text"])
    print(f"  Pre-registered trigger: {trigger_response.get('status', 'unknown')}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(test_hex_formats(), timeout=10))
    except asyncio.TimeoutError:
        print("\nTest timed out after 10 seconds")
    except Exception as e:
        print(f"\nTest error: {e}")