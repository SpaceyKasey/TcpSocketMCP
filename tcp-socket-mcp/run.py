#!/usr/bin/env python3
"""Direct runner for TCP Socket MCP Server without installation."""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run the server
from tcp_socket_mcp.server import main_sync

if __name__ == "__main__":
    main_sync()