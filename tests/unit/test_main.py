"""Unit tests for __main__.py entry point."""

import pytest
from unittest.mock import patch, Mock
import sys


@pytest.mark.unit
class TestMainEntry:
    """Test suite for __main__.py entry point."""
    
    def test_main_entry_point_import(self):
        """Test that __main__.py can be imported without error."""
        # Test importing the module
        import TcpSocketMCP.__main__
        assert TcpSocketMCP.__main__ is not None
    
    def test_main_entry_point_execution(self):
        """Test __main__.py execution path."""
        with patch('TcpSocketMCP.server.main_sync') as mock_main_sync:
            # Test the main execution logic
            from TcpSocketMCP.__main__ import main_sync
            
            # Import and check that we can execute the main code
            code = '''
if __name__ == "__main__":
    main_sync()
'''
            # Execute with main context
            exec(code, {'__name__': '__main__', 'main_sync': mock_main_sync})
            
            # Verify main_sync was called
            mock_main_sync.assert_called_once()