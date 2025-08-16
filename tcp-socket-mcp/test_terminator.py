#!/usr/bin/env python3
"""Test terminator functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_terminator():
    """Test the terminator functionality."""
    from tcp_socket_mcp.server import TCPSocketServer
    
    server = TCPSocketServer()
    
    test_cases = [
        # Test case: (data, terminator, expected_result)
        ("Hello", "\\x0d\\x0a", b"Hello\r\n"),
        ("Test", "\\x00", b"Test\x00"),
        ("Data", "\\xff\\xfe", b"Data\xff\xfe"),
        ("Multi", "\\x0d\\x0a\\x0d\\x0a", b"Multi\r\n\r\n"),
        ("Binary", "\\x01\\x02\\x03", b"Binary\x01\x02\x03"),
    ]
    
    print("Testing terminator functionality")
    print("=" * 50)
    
    for data, terminator, expected in test_cases:
        print(f"Testing: data='{data}', terminator='{terminator}'")
        
        # Parse the terminator
        terminator_bytes = server._parse_hex_string(terminator)
        data_bytes = data.encode('utf-8')
        result = data_bytes + terminator_bytes
        
        if result == expected:
            print(f"  ✅ Success: {result!r}")
        else:
            print(f"  ❌ Failed: Expected {expected!r}, got {result!r}")
        print()
    
    # Test hex data with terminator
    print("Testing hex data with terminator:")
    hex_data = "\\x00\\x01\\x02"
    terminator = "\\xff\\xfe"
    
    data_bytes = server._parse_hex_string(hex_data)
    terminator_bytes = server._parse_hex_string(terminator)
    result = data_bytes + terminator_bytes
    expected = b"\x00\x01\x02\xff\xfe"
    
    if result == expected:
        print(f"  ✅ Hex with terminator: {result!r}")
    else:
        print(f"  ❌ Failed: Expected {expected!r}, got {result!r}")

if __name__ == "__main__":
    test_terminator()
    print("\n" + "=" * 50)
    print("All terminator tests completed!")