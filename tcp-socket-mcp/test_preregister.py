#!/usr/bin/env python3
"""Test pre-registration of triggers before connection."""

import asyncio
import sys
import os
import json

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tcp_socket_mcp.server import TCPSocketServer

async def test_preregister_triggers():
    """Test pre-registering triggers before connection."""
    server = TCPSocketServer()
    
    print("Testing Pre-Registration of Triggers")
    print("=" * 50)
    
    # Test 1: Pre-register a trigger before connection exists
    print("\n1. Pre-registering trigger for non-existent connection...")
    trigger_args = {
        "connection_id": "test-preregister",
        "trigger_id": "auto-response",
        "pattern": "^HELLO",
        "response": "WORLD",
        "response_terminator": "\\x0d\\x0a"
    }
    
    result = await server._handle_set_trigger(trigger_args)
    response = json.loads(result[0]["text"])
    
    print(f"   Status: {response.get('status', 'unknown')}")
    print(f"   Message: {response.get('message', 'N/A')}")
    print(f"   Trigger ID: {response.get('trigger_id', 'N/A')}")
    
    # Verify trigger is in pending_triggers
    print(f"\n   Pending triggers: {list(server.pending_triggers.keys())}")
    if "test-preregister" in server.pending_triggers:
        print(f"   Triggers for 'test-preregister': {list(server.pending_triggers['test-preregister'].keys())}")
    
    # Test 2: Add another trigger to the same non-existent connection
    print("\n2. Adding second trigger to same pending connection...")
    trigger_args2 = {
        "connection_id": "test-preregister",
        "trigger_id": "ping-pong",
        "pattern": "PING",
        "response": "PONG",
        "response_terminator": "\\x0d\\x0a"
    }
    
    result2 = await server._handle_set_trigger(trigger_args2)
    response2 = json.loads(result2[0]["text"])
    print(f"   Status: {response2.get('status', 'unknown')}")
    
    if "test-preregister" in server.pending_triggers:
        print(f"   Total pending triggers: {len(server.pending_triggers['test-preregister'])}")
        print(f"   Trigger IDs: {list(server.pending_triggers['test-preregister'].keys())}")
    
    # Test 3: Now connect with the pre-registered connection_id
    print("\n3. Connecting with pre-registered triggers...")
    
    # Use a simple echo server for testing (netcat or httpbin)
    connect_args = {
        "host": "httpbin.org",
        "port": 80,
        "connection_id": "test-preregister"
    }
    
    connect_result = await server._handle_connect(connect_args)
    connect_response = json.loads(connect_result[0]["text"])
    
    print(f"   Connection success: {connect_response.get('success', False)}")
    print(f"   Applied triggers: {connect_response.get('applied_triggers', [])}")
    print(f"   Message: {connect_response.get('message', 'N/A')}")
    
    # Verify triggers were moved from pending to active
    print(f"\n   Pending triggers after connect: {list(server.pending_triggers.keys())}")
    print(f"   Active connections: {list(server.connections.keys())}")
    
    if "test-preregister" in server.connections:
        conn = server.connections["test-preregister"]
        triggers = conn.get_triggers()
        print(f"   Active triggers on connection: {triggers}")
    
    # Clean up
    if "test-preregister" in server.connections:
        await server._handle_disconnect({"connection_id": "test-preregister"})
    
    print("\n" + "=" * 50)
    
    # Test 4: Test with tcp_connect_and_send
    print("\n4. Testing pre-registration with tcp_connect_and_send...")
    
    # Pre-register trigger
    trigger_args3 = {
        "connection_id": "test-send",
        "trigger_id": "http-ok",
        "pattern": "HTTP/1.1 200",
        "response": "GOT OK RESPONSE",
        "response_terminator": "\\x0d\\x0a"
    }
    
    result3 = await server._handle_set_trigger(trigger_args3)
    response3 = json.loads(result3[0]["text"])
    print(f"   Pre-registered trigger: {response3.get('status', 'unknown')}")
    
    # Connect and send
    connect_send_args = {
        "host": "httpbin.org",
        "port": 80,
        "connection_id": "test-send",
        "data": "GET /status/200 HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
    }
    
    try:
        cs_result = await server._handle_connect_and_send(connect_send_args)
        cs_response = json.loads(cs_result[0]["text"])
        
        print(f"   Connection success: {cs_response.get('success', False)}")
        print(f"   Applied triggers: {cs_response.get('applied_triggers', [])}")
        print(f"   Bytes sent: {cs_response.get('bytes_sent', 0)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Clean up
    if "test-send" in server.connections:
        await server._handle_disconnect({"connection_id": "test-send"})
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(test_preregister_triggers(), timeout=10))
    except asyncio.TimeoutError:
        print("\nTest timed out after 10 seconds")
    except Exception as e:
        print(f"\nTest error: {e}")