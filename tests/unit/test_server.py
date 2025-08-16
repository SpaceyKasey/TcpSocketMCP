"""Unit tests for TCPSocketServer class."""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
import base64

from TcpSocketMCP.server import TCPSocketServer
from TcpSocketMCP.connection import TCPConnection


@pytest.mark.unit
class TestTCPSocketServer:
    """Test suite for TCPSocketServer class."""
    
    def test_init(self):
        """Test TCPSocketServer initialization."""
        server = TCPSocketServer()
        
        assert server.server is not None
        assert server.connections == {}
        assert server.pending_triggers == {}
        
    def test_parse_hex_string_plain_hex(self):
        """Test parsing plain hex string."""
        server = TCPSocketServer()
        
        # Test plain hex
        result = server._parse_hex_string("48656C6C6F")
        assert result == b"Hello"
        
        # Test with spaces
        result = server._parse_hex_string("48 65 6C 6C 6F")
        assert result == b"Hello"
        
        # Test with 0x prefix
        result = server._parse_hex_string("0x48656C6C6F")
        assert result == b"Hello"
        
    def test_parse_hex_string_escape_format(self):
        """Test parsing hex string with escape sequences."""
        server = TCPSocketServer()
        
        # Test \x format
        result = server._parse_hex_string("\\x48\\x65\\x6C\\x6C\\x6F")
        assert result == b"Hello"
        
        # Test mixed format
        result = server._parse_hex_string("Hello\\x0D\\x0A")
        assert result == b"Hello\r\n"
        
    def test_parse_hex_string_invalid_hex(self):
        """Test parsing invalid hex string falls back to UTF-8."""
        server = TCPSocketServer()
        
        result = server._parse_hex_string("invalid_hex")
        assert result == b"invalid_hex"
        
    @pytest.mark.asyncio
    async def test_handle_connect_success(self):
        """Test successful connection handling."""
        server = TCPSocketServer()
        
        args = {
            "host": "localhost",
            "port": 8080,
            "connection_id": "test-conn"
        }
        
        # Mock the TCPConnection
        with patch('TcpSocketMCP.server.TCPConnection') as mock_conn_class:
            mock_conn = AsyncMock()
            mock_conn.connect.return_value = True
            mock_conn_class.return_value = mock_conn
            
            result = await server._handle_connect(args)
            
            # Check result structure
            assert len(result) == 1
            assert result[0]["type"] == "text"
            response = json.loads(result[0]["text"])
            
            assert response["success"] is True
            assert response["connection_id"] == "test-conn"
            assert response["host"] == "localhost"
            assert response["port"] == 8080
            assert response["status"] == "connected"
            
            # Verify connection is stored
            assert "test-conn" in server.connections
            
    @pytest.mark.asyncio
    async def test_handle_connect_failure(self):
        """Test connection failure handling."""
        server = TCPSocketServer()
        
        args = {
            "host": "invalid-host",
            "port": 8080
        }
        
        # Mock the TCPConnection to fail
        with patch('TcpSocketMCP.server.TCPConnection') as mock_conn_class:
            mock_conn = AsyncMock()
            mock_conn.connect.return_value = False
            mock_conn_class.return_value = mock_conn
            
            result = await server._handle_connect(args)
            
            # Check result structure
            assert len(result) == 1
            assert result[0]["type"] == "text"
            response = json.loads(result[0]["text"])
            
            assert "error" in response
            assert response["message"] == "Failed to connect to invalid-host:8080"
            
    @pytest.mark.asyncio
    async def test_handle_connect_auto_id(self):
        """Test connection with auto-generated ID."""
        server = TCPSocketServer()
        
        args = {
            "host": "localhost",
            "port": 8080
        }
        
        with patch('TcpSocketMCP.server.TCPConnection') as mock_conn_class:
            mock_conn = AsyncMock()
            mock_conn.connect.return_value = True
            mock_conn_class.return_value = mock_conn
            
            with patch('uuid.uuid4', return_value=MagicMock()):
                result = await server._handle_connect(args)
                
                assert len(result) == 1
                response = json.loads(result[0]["text"])
                assert response["success"] is True
                assert "connection_id" in response
                
    @pytest.mark.asyncio
    async def test_handle_disconnect_success(self):
        """Test successful disconnection."""
        server = TCPSocketServer()
        
        # Setup existing connection
        mock_conn = AsyncMock()
        server.connections["test-conn"] = mock_conn
        
        args = {"connection_id": "test-conn"}
        
        result = await server._handle_disconnect(args)
        
        # Check result
        assert len(result) == 1
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        assert response["connection_id"] == "test-conn"
        assert response["status"] == "disconnected"
        
        # Verify connection removed
        assert "test-conn" not in server.connections
        mock_conn.disconnect.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_handle_disconnect_not_found(self):
        """Test disconnection when connection doesn't exist."""
        server = TCPSocketServer()
        
        args = {"connection_id": "nonexistent"}
        
        result = await server._handle_disconnect(args)
        
        # Check result
        assert len(result) == 1
        response = json.loads(result[0]["text"])
        assert "error" in response
        assert response["message"] == "Connection nonexistent not found"
        
    @pytest.mark.asyncio
    async def test_handle_send_success(self):
        """Test successful data sending."""
        server = TCPSocketServer()
        
        # Setup existing connection
        mock_conn = AsyncMock()
        mock_conn.send.return_value = True
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "data": "48656C6C6F",  # "Hello" in hex
            "encoding": "hex"
        }
        
        result = await server._handle_send(args)
        
        # Check result
        assert len(result) == 1
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        assert response["bytes_sent"] == 5
        
        # Verify send was called with correct data
        mock_conn.send.assert_called_once_with(b"Hello")
        
    @pytest.mark.asyncio
    async def test_handle_send_utf8_encoding(self):
        """Test sending with UTF-8 encoding."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.send.return_value = True
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "data": "Hello World",
            "encoding": "utf-8"
        }
        
        result = await server._handle_send(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        mock_conn.send.assert_called_once_with(b"Hello World")
        
    @pytest.mark.asyncio
    async def test_handle_send_base64_encoding(self):
        """Test sending with base64 encoding."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.send.return_value = True
        server.connections["test-conn"] = mock_conn
        
        # "Hello" in base64
        hello_b64 = base64.b64encode(b"Hello").decode()
        
        args = {
            "connection_id": "test-conn",
            "data": hello_b64,
            "encoding": "base64"
        }
        
        result = await server._handle_send(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        mock_conn.send.assert_called_once_with(b"Hello")
        
    @pytest.mark.asyncio
    async def test_handle_send_with_terminator(self):
        """Test sending with hex terminator."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.send.return_value = True
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "data": "Hello",
            "encoding": "utf-8",
            "terminator": "0D0A"  # CRLF
        }
        
        result = await server._handle_send(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        mock_conn.send.assert_called_once_with(b"Hello\r\n")
        
    @pytest.mark.asyncio
    async def test_handle_send_connection_not_found(self):
        """Test sending when connection doesn't exist."""
        server = TCPSocketServer()
        
        args = {
            "connection_id": "nonexistent",
            "data": "Hello"
        }
        
        result = await server._handle_send(args)
        
        response = json.loads(result[0]["text"])
        assert "error" in response
        assert response["message"] == "Connection nonexistent not found"
        
    @pytest.mark.asyncio
    async def test_handle_send_failure(self):
        """Test send failure."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.send.return_value = False
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "data": "Hello"
        }
        
        result = await server._handle_send(args)
        
        response = json.loads(result[0]["text"])
        assert "error" in response
        assert response["message"] == "Failed to send data"
        
    @pytest.mark.asyncio
    async def test_handle_read_buffer_success(self):
        """Test successful buffer reading."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.read_buffer.return_value = [b"chunk1", b"chunk2"]
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "format": "utf-8"
        }
        
        result = await server._handle_read_buffer(args)
        
        response = json.loads(result[0]["text"])
        assert response["connection_id"] == "test-conn"
        assert response["data"] == ["chunk1", "chunk2"]
        assert response["chunks"] == 2
        assert response["format"] == "utf-8"
        
    @pytest.mark.asyncio
    async def test_handle_read_buffer_hex_format(self):
        """Test buffer reading with hex format."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.read_buffer.return_value = [b"Hello"]
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "format": "hex"
        }
        
        result = await server._handle_read_buffer(args)
        
        response = json.loads(result[0]["text"])
        assert response["connection_id"] == "test-conn"
        assert response["data"] == ["48656c6c6f"]  # "Hello" in hex
        assert response["format"] == "hex"
        
    @pytest.mark.asyncio
    async def test_handle_read_buffer_with_index_count(self):
        """Test buffer reading with index and count."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.read_buffer.return_value = [b"chunk2"]
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "index": 1,
            "count": 1,
            "format": "utf-8"
        }
        
        result = await server._handle_read_buffer(args)
        
        response = json.loads(result[0]["text"])
        assert response["connection_id"] == "test-conn"
        assert response["data"] == ["chunk2"]
        mock_conn.read_buffer.assert_called_once_with(1, 1)
        
    @pytest.mark.asyncio
    async def test_handle_clear_buffer_success(self):
        """Test successful buffer clearing."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        server.connections["test-conn"] = mock_conn
        
        args = {"connection_id": "test-conn"}
        
        result = await server._handle_clear_buffer(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        mock_conn.clear_buffer.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_handle_buffer_info_success(self):
        """Test successful buffer info retrieval."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.get_buffer_info.return_value = {
            "chunks": 3,
            "total_bytes": 150,
            "bytes_sent": 100,
            "bytes_received": 200,
            "connected": True
        }
        server.connections["test-conn"] = mock_conn
        
        args = {"connection_id": "test-conn"}
        
        result = await server._handle_buffer_info(args)
        
        response = json.loads(result[0]["text"])
        assert response["chunks"] == 3
        assert response["total_bytes"] == 150
        assert response["bytes_sent"] == 100
        assert response["bytes_received"] == 200
        assert response["connected"] is True
        
    @pytest.mark.asyncio
    async def test_handle_set_trigger_success(self):
        """Test successful trigger setting."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.add_trigger = Mock()
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "trigger_id": "ping_handler",
            "pattern": r"PING :(.+)",
            "response": "PONG :$1\r\n",
            "response_encoding": "utf-8"
        }
        
        result = await server._handle_set_trigger(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        assert response["trigger_id"] == "ping_handler"
        assert response["status"] == "active"
        
        mock_conn.add_trigger.assert_called_once_with(
            "ping_handler", 
            r"PING :(.+)", 
            b"PONG :$1\r\n"
        )
        
    @pytest.mark.asyncio
    async def test_handle_set_trigger_pre_registration(self):
        """Test trigger pre-registration before connection exists."""
        server = TCPSocketServer()
        
        args = {
            "connection_id": "future-conn",
            "trigger_id": "ping_handler",
            "pattern": r"PING :(.+)",
            "response": "PONG :$1\r\n"
        }
        
        result = await server._handle_set_trigger(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        assert response["status"] == "pending"
        
        # Check pending triggers
        assert "future-conn" in server.pending_triggers
        assert "ping_handler" in server.pending_triggers["future-conn"]
        
    @pytest.mark.asyncio
    async def test_handle_remove_trigger_success(self):
        """Test successful trigger removal."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.remove_trigger = Mock(return_value=True)
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "trigger_id": "ping_handler"
        }
        
        result = await server._handle_remove_trigger(args)
        
        response = json.loads(result[0]["text"])
        assert response["success"] is True
        mock_conn.remove_trigger.assert_called_once_with("ping_handler")
        
    @pytest.mark.asyncio
    async def test_handle_remove_trigger_not_found(self):
        """Test trigger removal when trigger doesn't exist."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.remove_trigger = Mock(return_value=False)
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "trigger_id": "nonexistent"
        }
        
        result = await server._handle_remove_trigger(args)
        
        response = json.loads(result[0]["text"])
        assert "error" in response
        assert response["error"] == "not_found"
        assert "not found" in response["message"]
        
    @pytest.mark.asyncio
    async def test_handle_list_connections_empty(self):
        """Test listing connections when none exist."""
        server = TCPSocketServer()
        
        result = await server._handle_list_connections()
        
        response = json.loads(result[0]["text"])
        assert response["total_connections"] == 0
        assert response["connections"] == []
        
    @pytest.mark.asyncio
    async def test_handle_list_connections_with_connections(self):
        """Test listing connections when some exist."""
        server = TCPSocketServer()
        
        # Setup mock connections
        mock_conn1 = AsyncMock()
        mock_conn1.connection_id = "conn1"
        mock_conn1.host = "host1"
        mock_conn1.port = 8080
        mock_conn1.connected = True
        mock_conn1.bytes_sent = 100
        mock_conn1.bytes_received = 200
        mock_conn1.get_buffer_info.return_value = {
            "chunks": 2,
            "bytes_sent": 100,
            "bytes_received": 200
        }
        mock_conn1.triggers = {"pattern1": ("t1", b"response")}
        
        server.connections["conn1"] = mock_conn1
        
        result = await server._handle_list_connections()
        
        response = json.loads(result[0]["text"])
        assert response["total_connections"] == 1
        assert len(response["connections"]) == 1
        
        conn_info = response["connections"][0]
        assert conn_info["connection_id"] == "conn1"
        assert conn_info["host"] == "host1"
        assert conn_info["port"] == 8080
        assert conn_info["connected"] is True
        assert conn_info["bytes_sent"] == 100
        assert conn_info["bytes_received"] == 200
        assert conn_info["buffer_chunks"] == 2
        assert conn_info["triggers"] == 1
        
    @pytest.mark.asyncio
    async def test_handle_connection_info_success(self):
        """Test successful connection info retrieval."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.connection_id = "test-conn"
        mock_conn.host = "localhost"
        mock_conn.port = 8080
        mock_conn.connected = True
        mock_conn.created_at = Mock()
        mock_conn.created_at.isoformat.return_value = "2023-01-01T00:00:00"
        mock_conn.get_buffer_info.return_value = {
            "chunks": 2,
            "total_bytes": 100,
            "bytes_sent": 50,
            "bytes_received": 150
        }
        mock_conn.get_triggers = Mock(return_value=[
            {"trigger_id": "t1", "pattern": "test", "response_size": 10}
        ])
        
        server.connections["test-conn"] = mock_conn
        
        args = {"connection_id": "test-conn"}
        
        result = await server._handle_connection_info(args)
        
        response = json.loads(result[0]["text"])
        assert response["connection_id"] == "test-conn"
        assert response["host"] == "localhost"
        assert response["port"] == 8080
        assert response["connected"] is True
        assert "created_at" in response
        assert "buffer" in response
        assert len(response["triggers"]) == 1
        
    @pytest.mark.asyncio
    async def test_handle_connect_and_send_success(self):
        """Test successful connect and send operation."""
        server = TCPSocketServer()
        
        args = {
            "host": "localhost",
            "port": 8080,
            "data": "Hello",
            "encoding": "utf-8"
        }
        
        with patch('TcpSocketMCP.server.TCPConnection') as mock_conn_class:
            mock_conn = AsyncMock()
            mock_conn.connect.return_value = True
            mock_conn.send.return_value = True
            mock_conn.get_buffer_info.return_value = {"chunks": 0}
            mock_conn_class.return_value = mock_conn
            
            # Mock sleep to speed up test
            with patch('asyncio.sleep'):
                result = await server._handle_connect_and_send(args)
                
                response = json.loads(result[0]["text"])
                assert response["success"] is True
                assert response["bytes_sent"] == 5
                assert response["status"] == "connected"
                
                # Verify connection was made and data sent
                mock_conn.connect.assert_called_once()
                mock_conn.send.assert_called_once_with(b"Hello")


@pytest.mark.unit
class TestTCPSocketServerErrorHandling:
    """Test error handling in TCPSocketServer."""
    
    @pytest.mark.asyncio
    async def test_handle_connect_exception(self):
        """Test connection handling when exception occurs."""
        server = TCPSocketServer()
        
        args = {"host": "localhost", "port": 8080}
        
        with patch('TcpSocketMCP.server.TCPConnection', side_effect=Exception("Connection error")):
            # The actual exception will be raised since we're calling the handler directly
            with pytest.raises(Exception, match="Connection error"):
                await server._handle_connect(args)
            
    @pytest.mark.asyncio
    async def test_handle_send_exception(self):
        """Test send handling when exception occurs."""
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        mock_conn.send.side_effect = Exception("Send error")
        server.connections["test-conn"] = mock_conn
        
        args = {"connection_id": "test-conn", "data": "Hello"}
        
        # When calling the handler directly, exceptions are raised
        with pytest.raises(Exception, match="Send error"):
            await server._handle_send(args)
        
    @pytest.mark.asyncio
    async def test_invalid_base64_encoding(self):
        """Test handling of invalid base64 data."""
        import binascii
        server = TCPSocketServer()
        
        mock_conn = AsyncMock()
        server.connections["test-conn"] = mock_conn
        
        args = {
            "connection_id": "test-conn",
            "data": "invalid_base64!@#",
            "encoding": "base64"
        }
        
        # Invalid base64 raises binascii.Error during base64.b64decode()
        with pytest.raises(binascii.Error):
            await server._handle_send(args)


@pytest.mark.unit
class TestTCPSocketServerIntegration:
    """Integration-style unit tests for TCPSocketServer."""
    
    @pytest.mark.asyncio
    async def test_trigger_pre_registration_workflow(self):
        """Test the complete trigger pre-registration workflow."""
        server = TCPSocketServer()
        
        # Step 1: Pre-register a trigger
        trigger_args = {
            "connection_id": "future-conn",
            "trigger_id": "ping_handler",
            "pattern": r"PING",
            "response": "PONG"
        }
        
        await server._handle_set_trigger(trigger_args)
        assert "future-conn" in server.pending_triggers
        
        # Step 2: Connect with the pre-registered connection ID
        connect_args = {
            "host": "localhost",
            "port": 8080,
            "connection_id": "future-conn"
        }
        
        with patch('TcpSocketMCP.server.TCPConnection') as mock_conn_class:
            mock_conn = AsyncMock()
            mock_conn.connect.return_value = True
            mock_conn.add_trigger = Mock()
            mock_conn_class.return_value = mock_conn
            
            result = await server._handle_connect(connect_args)
            
            # Check that trigger was applied
            response = json.loads(result[0]["text"])
            assert "applied_triggers" in response
            assert "ping_handler" in response["applied_triggers"]
            
            # Check that pending triggers were cleared
            assert "future-conn" not in server.pending_triggers
            
            # Verify trigger was added to connection
            mock_conn.add_trigger.assert_called_once_with(
                "ping_handler", r"PING", b"PONG"
            )
            
    @pytest.mark.asyncio
    async def test_connection_lifecycle_management(self):
        """Test complete connection lifecycle management."""
        server = TCPSocketServer()
        
        # Connect
        with patch('TcpSocketMCP.server.TCPConnection') as mock_conn_class:
            mock_conn = AsyncMock()
            mock_conn.connect.return_value = True
            mock_conn.send.return_value = True
            mock_conn.get_buffer_info.return_value = {
                "chunks": 1,
                "total_bytes": 5,
                "bytes_sent": 5,
                "bytes_received": 0,
                "connected": True
            }
            mock_conn_class.return_value = mock_conn
            
            # Step 1: Connect
            connect_args = {"host": "localhost", "port": 8080, "connection_id": "test"}
            await server._handle_connect(connect_args)
            assert "test" in server.connections
            
            # Step 2: Send data
            send_args = {"connection_id": "test", "data": "Hello"}
            await server._handle_send(send_args)
            mock_conn.send.assert_called_once()
            
            # Step 3: Check buffer info
            await server._handle_buffer_info({"connection_id": "test"})
            mock_conn.get_buffer_info.assert_called()
            
            # Step 4: Disconnect
            await server._handle_disconnect({"connection_id": "test"})
            assert "test" not in server.connections
            mock_conn.disconnect.assert_called_once()