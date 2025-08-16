#!/usr/bin/env python3
"""Test script for tcp_connect_and_send tool."""

import json
import subprocess
import sys

def test_connect_and_send():
    """Test the tcp_connect_and_send tool."""
    
    # Test 1: HTTP GET request to httpbin.org
    print("Test 1: HTTP GET request with immediate send")
    print("-" * 50)
    
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "tcp_connect_and_send",
            "arguments": {
                "host": "httpbin.org",
                "port": 80,
                "data": "GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n",
                "connection_id": "http-test"
            }
        },
        "id": 1
    }
    
    # Run the server and send the request
    proc = subprocess.Popen(
        ["python", "run.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    
    # Read response
    response_line = proc.stdout.readline()
    try:
        response = json.loads(response_line)
        result = json.loads(response["result"][0]["text"])
        
        print(f"Success: {result.get('success', False)}")
        print(f"Connection ID: {result.get('connection_id', 'N/A')}")
        print(f"Bytes sent: {result.get('bytes_sent', 0)}")
        print(f"Immediate response: {result.get('immediate_response', False)}")
        print(f"Buffer chunks: {result.get('buffer_chunks', 0)}")
        
        if result.get('success'):
            # Now read the buffer to see the response
            read_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "tcp_read_buffer",
                    "arguments": {
                        "connection_id": "http-test"
                    }
                },
                "id": 2
            }
            
            proc.stdin.write(json.dumps(read_request) + "\n")
            proc.stdin.flush()
            
            response_line = proc.stdout.readline()
            response = json.loads(response_line)
            buffer_data = json.loads(response["result"][0]["text"])
            
            print("\nBuffer contents (first 500 chars):")
            if buffer_data.get("data"):
                print(buffer_data["data"][0][:500])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response_line}")
    
    # Terminate the process
    proc.terminate()
    
    print("\n" + "=" * 50 + "\n")
    
    # Test 2: Connect and send with hex encoding
    print("Test 2: Connect and send with hex encoding")
    print("-" * 50)
    
    request2 = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "tcp_connect_and_send",
            "arguments": {
                "host": "example.com",
                "port": 80,
                "data": "474554202f20485454502f312e310d0a486f73743a206578616d706c652e636f6d0d0a0d0a",
                "encoding": "hex",
                "connection_id": "hex-test"
            }
        },
        "id": 3
    }
    
    proc2 = subprocess.Popen(
        ["python", "run.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    proc2.stdin.write(json.dumps(request2) + "\n")
    proc2.stdin.flush()
    
    response_line = proc2.stdout.readline()
    try:
        response = json.loads(response_line)
        result = json.loads(response["result"][0]["text"])
        
        print(f"Success: {result.get('success', False)}")
        print(f"Connection ID: {result.get('connection_id', 'N/A')}")
        print(f"Bytes sent: {result.get('bytes_sent', 0)}")
        print(f"Immediate response: {result.get('immediate_response', False)}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error: {e}")
    
    proc2.terminate()
    
    print("\n" + "=" * 50 + "\n")
    
    # Test 3: Test with custom terminator
    print("Test 3: Connect and send with custom terminator")
    print("-" * 50)
    
    request3 = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "tcp_connect_and_send",
            "arguments": {
                "host": "example.com",
                "port": 80,
                "data": "GET / HTTP/1.1\r\nHost: example.com",
                "terminator": "\\x0d\\x0a\\x0d\\x0a",
                "connection_id": "terminator-test"
            }
        },
        "id": 4
    }
    
    proc3 = subprocess.Popen(
        ["python", "run.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    proc3.stdin.write(json.dumps(request3) + "\n")
    proc3.stdin.flush()
    
    response_line = proc3.stdout.readline()
    try:
        response = json.loads(response_line)
        result = json.loads(response["result"][0]["text"])
        
        print(f"Success: {result.get('success', False)}")
        print(f"Connection ID: {result.get('connection_id', 'N/A')}")
        print(f"Bytes sent: {result.get('bytes_sent', 0)}")
        print(f"Status: {result.get('status', 'N/A')}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error: {e}")
    
    proc3.terminate()

if __name__ == "__main__":
    test_connect_and_send()