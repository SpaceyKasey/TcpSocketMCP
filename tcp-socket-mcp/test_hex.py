#!/usr/bin/env python3
"""Test hex encoding functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_hex_parsing():
    """Test the hex parsing logic."""
    import re
    
    test_cases = [
        # Test case: (input_string, encoding, expected_bytes)
        ("\\x48\\x65\\x6c\\x6c\\x6f", "hex", b"Hello"),
        ("48656c6c6f", "hex", b"Hello"),
        ("48 65 6c 6c 6f", "hex", b"Hello"),
        ("\\x00\\x01\\x02\\x03", "hex", b"\x00\x01\x02\x03"),
        ("Hello\\x00World", "hex", b"Hello\x00World"),
        ("\\xff\\xfe\\xfd", "hex", b"\xff\xfe\xfd"),
        ("DEADBEEF", "hex", b"\xde\xad\xbe\xef"),
    ]
    
    for data_str, encoding, expected in test_cases:
        print(f"Testing: {repr(data_str)}")
        
        if encoding == "hex":
            # This is the same logic from server.py
            hex_str = data_str.replace("0x", "").replace("0X", "").replace(" ", "").replace("\n", "").replace("\r", "")
            
            if "\\x" in data_str:
                # Parse \xNN format
                hex_bytes = bytearray()
                pattern = r'\\x([0-9a-fA-F]{2})'
                matches = re.findall(pattern, data_str)
                for hex_val in matches:
                    hex_bytes.append(int(hex_val, 16))
                
                # Check for mixed content
                remaining = re.sub(pattern, '\x00', data_str)
                if remaining and remaining != '\x00' * len(matches):
                    # Mix of hex and literal
                    parts = re.split(r'(\\x[0-9a-fA-F]{2})', data_str)
                    hex_bytes = bytearray()
                    for part in parts:
                        if part.startswith('\\x') and len(part) == 4:
                            hex_bytes.append(int(part[2:], 16))
                        elif part:
                            hex_bytes.extend(part.encode('utf-8'))
                data = bytes(hex_bytes)
            else:
                # Plain hex string
                try:
                    data = bytes.fromhex(hex_str)
                except ValueError as e:
                    print(f"  Error: {e}")
                    data = data_str.encode("utf-8")
        
        if data == expected:
            print(f"  ✅ Success: {data!r}")
        else:
            print(f"  ❌ Failed: Expected {expected!r}, got {data!r}")
        print()

if __name__ == "__main__":
    print("Testing hex encoding functionality")
    print("=" * 50)
    test_hex_parsing()
    print("=" * 50)
    print("All tests completed!")