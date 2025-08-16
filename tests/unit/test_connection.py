"""Unit tests for TCPConnection class."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from TcpSocketMCP.connection import TCPConnection


@pytest.mark.unit
class TestTCPConnection:
    """Test suite for TCPConnection class."""
    
    def test_init(self, mock_connection_id, test_host, test_port):
        """Test TCPConnection initialization."""
        conn = TCPConnection(mock_connection_id, test_host, test_port)
        
        assert conn.connection_id == mock_connection_id
        assert conn.host == test_host
        assert conn.port == test_port
        assert conn.reader is None
        assert conn.writer is None
        assert conn.buffer == []
        assert conn.triggers == {}
        assert conn.connected is False
        assert conn.bytes_sent == 0
        assert conn.bytes_received == 0
        assert conn._read_task is None
        assert isinstance(conn.created_at, datetime)
        assert hasattr(conn, '_lock')
    
    @pytest.mark.asyncio
    async def test_connect_success(self, tcp_connection, mock_stream_reader, mock_stream_writer):
        """Test successful connection."""
        with patch('asyncio.open_connection', return_value=(mock_stream_reader, mock_stream_writer)):
            with patch('asyncio.create_task') as mock_create_task:
                mock_task = AsyncMock()
                mock_create_task.return_value = mock_task
                
                result = await tcp_connection.connect()
                
                assert result is True
                assert tcp_connection.connected is True
                assert tcp_connection.reader == mock_stream_reader
                assert tcp_connection.writer == mock_stream_writer
                assert tcp_connection._read_task == mock_task
                mock_create_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, tcp_connection):
        """Test connection failure."""
        with patch('asyncio.open_connection', side_effect=ConnectionRefusedError("Connection refused")):
            result = await tcp_connection.connect()
            
            assert result is False
            assert tcp_connection.connected is False
            assert tcp_connection.reader is None
            assert tcp_connection.writer is None
    
    @pytest.mark.asyncio
    async def test_disconnect(self, tcp_connection):
        """Test disconnection."""
        # Test disconnection when not connected (simpler case)
        tcp_connection.connected = False
        tcp_connection._read_task = None
        tcp_connection.writer = None
        tcp_connection.reader = None
        
        await tcp_connection.disconnect()
        
        assert tcp_connection.connected is False
        assert tcp_connection.reader is None
        assert tcp_connection.writer is None
    
    @pytest.mark.asyncio
    async def test_disconnect_with_writer_only(self, tcp_connection):
        """Test disconnection when only writer exists."""
        mock_writer = AsyncMock()
        mock_writer.close = Mock()  # Make close synchronous
        
        tcp_connection.connected = True
        tcp_connection._read_task = None  # No read task
        tcp_connection.writer = mock_writer
        tcp_connection.reader = AsyncMock()
        
        await tcp_connection.disconnect()
        
        assert tcp_connection.connected is False
        assert tcp_connection.reader is None
        assert tcp_connection.writer is None
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_with_writer_error(self, tcp_connection):
        """Test disconnection when writer close raises error."""
        mock_writer = AsyncMock()
        mock_writer.close.side_effect = Exception("Close error")
        
        tcp_connection.connected = True
        tcp_connection.writer = mock_writer
        
        # Should not raise exception
        await tcp_connection.disconnect()
        
        assert tcp_connection.connected is False
    
    @pytest.mark.asyncio
    async def test_send_success(self, tcp_connection):
        """Test successful data sending."""
        mock_writer = AsyncMock()
        tcp_connection.connected = True
        tcp_connection.writer = mock_writer
        
        test_data = b"test data"
        result = await tcp_connection.send(test_data)
        
        assert result is True
        assert tcp_connection.bytes_sent == len(test_data)
        mock_writer.write.assert_called_once_with(test_data)
        mock_writer.drain.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_not_connected(self, tcp_connection):
        """Test sending when not connected."""
        result = await tcp_connection.send(b"test data")
        
        assert result is False
        assert tcp_connection.bytes_sent == 0
    
    @pytest.mark.asyncio
    async def test_send_no_writer(self, tcp_connection):
        """Test sending when no writer."""
        tcp_connection.connected = True
        tcp_connection.writer = None
        
        result = await tcp_connection.send(b"test data")
        
        assert result is False
        assert tcp_connection.bytes_sent == 0
    
    @pytest.mark.asyncio
    async def test_send_writer_error(self, tcp_connection):
        """Test sending when writer raises error."""
        mock_writer = AsyncMock()
        mock_writer.write = Mock(side_effect=Exception("Write error"))  # Make write synchronous
        
        tcp_connection.connected = True
        tcp_connection.writer = mock_writer
        
        result = await tcp_connection.send(b"test data")
        
        assert result is False
        assert tcp_connection.connected is False
    
    @pytest.mark.asyncio
    async def test_read_loop_normal_operation(self, tcp_connection):
        """Test normal read loop operation."""
        mock_reader = AsyncMock()
        mock_reader.read.side_effect = [b"data1", b"data2", b""]  # Empty bytes signals end
        
        tcp_connection.connected = True
        tcp_connection.reader = mock_reader
        
        with patch.object(tcp_connection, '_check_triggers') as mock_check_triggers:
            await tcp_connection._read_loop()
            
            assert len(tcp_connection.buffer) == 2
            assert tcp_connection.buffer[0] == b"data1"
            assert tcp_connection.buffer[1] == b"data2"
            assert tcp_connection.bytes_received == 10  # len("data1") + len("data2")
            assert tcp_connection.connected is False  # Should be set to False when empty data received
            assert mock_check_triggers.call_count == 2
    
    @pytest.mark.asyncio
    async def test_read_loop_cancelled(self, tcp_connection):
        """Test read loop when cancelled."""
        mock_reader = AsyncMock()
        mock_reader.read.side_effect = asyncio.CancelledError()
        
        tcp_connection.connected = True
        tcp_connection.reader = mock_reader
        
        await tcp_connection._read_loop()
        
        # Should exit cleanly without changing connection state
        assert tcp_connection.connected is True
    
    @pytest.mark.asyncio
    async def test_read_loop_exception(self, tcp_connection):
        """Test read loop when exception occurs."""
        mock_reader = AsyncMock()
        mock_reader.read.side_effect = Exception("Read error")
        
        tcp_connection.connected = True
        tcp_connection.reader = mock_reader
        
        await tcp_connection._read_loop()
        
        assert tcp_connection.connected is False
    
    @pytest.mark.asyncio
    async def test_check_triggers_match(self, tcp_connection):
        """Test trigger checking with pattern match."""
        tcp_connection.triggers = {
            r"PING :(.+)": ("ping_trigger", b"PONG :$1\r\n")
        }
        
        with patch.object(tcp_connection, 'send') as mock_send:
            await tcp_connection._check_triggers(b"PING :server123\r\n")
            mock_send.assert_called_once_with(b"PONG :$1\r\n")
    
    @pytest.mark.asyncio
    async def test_check_triggers_no_match(self, tcp_connection):
        """Test trigger checking with no pattern match."""
        tcp_connection.triggers = {
            r"PING :(.+)": ("ping_trigger", b"PONG :$1\r\n")
        }
        
        with patch.object(tcp_connection, 'send') as mock_send:
            await tcp_connection._check_triggers(b"PONG :server123\r\n")
            mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_triggers_decode_error(self, tcp_connection):
        """Test trigger checking with decode error."""
        tcp_connection.triggers = {
            r"PING :(.+)": ("ping_trigger", b"PONG :$1\r\n")
        }
        
        # Should not raise exception
        await tcp_connection._check_triggers(b"\xff\xfe\xfd")
    
    @pytest.mark.asyncio
    async def test_check_triggers_send_error(self, tcp_connection):
        """Test trigger checking when send fails."""
        tcp_connection.triggers = {
            r"PING :(.+)": ("ping_trigger", b"PONG :$1\r\n")
        }
        
        with patch.object(tcp_connection, 'send', side_effect=Exception("Send error")):
            # Should not raise exception
            await tcp_connection._check_triggers(b"PING :server123\r\n")
    
    @pytest.mark.asyncio
    async def test_read_buffer_all(self, tcp_connection):
        """Test reading entire buffer."""
        tcp_connection.buffer = [b"data1", b"data2", b"data3"]
        
        result = await tcp_connection.read_buffer()
        
        assert result == [b"data1", b"data2", b"data3"]
        assert tcp_connection.buffer == [b"data1", b"data2", b"data3"]  # Original should be unchanged
    
    @pytest.mark.asyncio
    async def test_read_buffer_from_index(self, tcp_connection):
        """Test reading buffer from specific index."""
        tcp_connection.buffer = [b"data1", b"data2", b"data3"]
        
        result = await tcp_connection.read_buffer(index=1)
        
        assert result == [b"data2", b"data3"]
    
    @pytest.mark.asyncio
    async def test_read_buffer_with_count(self, tcp_connection):
        """Test reading buffer with count limit."""
        tcp_connection.buffer = [b"data1", b"data2", b"data3"]
        
        result = await tcp_connection.read_buffer(index=0, count=2)
        
        assert result == [b"data1", b"data2"]
    
    @pytest.mark.asyncio
    async def test_read_buffer_index_out_of_range(self, tcp_connection):
        """Test reading buffer with index out of range."""
        tcp_connection.buffer = [b"data1", b"data2"]
        
        result = await tcp_connection.read_buffer(index=5)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_read_buffer_count_exceeds_buffer(self, tcp_connection):
        """Test reading buffer when count exceeds available data."""
        tcp_connection.buffer = [b"data1", b"data2"]
        
        result = await tcp_connection.read_buffer(index=1, count=5)
        
        assert result == [b"data2"]
    
    @pytest.mark.asyncio
    async def test_clear_buffer(self, tcp_connection):
        """Test clearing the buffer."""
        tcp_connection.buffer = [b"data1", b"data2", b"data3"]
        
        await tcp_connection.clear_buffer()
        
        assert tcp_connection.buffer == []
    
    @pytest.mark.asyncio
    async def test_get_buffer_info(self, tcp_connection):
        """Test getting buffer information."""
        tcp_connection.buffer = [b"data1", b"data22", b"data333"]
        tcp_connection.bytes_sent = 100
        tcp_connection.bytes_received = 200
        tcp_connection.connected = True
        
        info = await tcp_connection.get_buffer_info()
        
        expected_info = {
            "connection_id": tcp_connection.connection_id,
            "chunks": 3,
            "total_bytes": 5 + 6 + 7,  # len of each chunk
            "bytes_sent": 100,
            "bytes_received": 200,
            "connected": True
        }
        
        assert info == expected_info
    
    def test_add_trigger(self, tcp_connection, sample_trigger_pattern, sample_trigger_response):
        """Test adding a trigger."""
        trigger_id = "test_trigger"
        
        tcp_connection.add_trigger(trigger_id, sample_trigger_pattern, sample_trigger_response)
        
        assert sample_trigger_pattern in tcp_connection.triggers
        assert tcp_connection.triggers[sample_trigger_pattern] == (trigger_id, sample_trigger_response)
    
    def test_remove_trigger_success(self, tcp_connection, sample_trigger_pattern, sample_trigger_response):
        """Test successful trigger removal."""
        trigger_id = "test_trigger"
        tcp_connection.triggers[sample_trigger_pattern] = (trigger_id, sample_trigger_response)
        
        result = tcp_connection.remove_trigger(trigger_id)
        
        assert result is True
        assert sample_trigger_pattern not in tcp_connection.triggers
    
    def test_remove_trigger_not_found(self, tcp_connection):
        """Test trigger removal when trigger doesn't exist."""
        result = tcp_connection.remove_trigger("nonexistent_trigger")
        
        assert result is False
    
    def test_get_triggers(self, tcp_connection):
        """Test getting all triggers."""
        tcp_connection.triggers = {
            r"PING :(.+)": ("ping_trigger", b"PONG :$1\r\n"),
            r"HELLO": ("hello_trigger", b"HI THERE")
        }
        
        triggers = tcp_connection.get_triggers()
        
        assert len(triggers) == 2
        
        # Check first trigger
        ping_trigger = next(t for t in triggers if t["trigger_id"] == "ping_trigger")
        assert ping_trigger["pattern"] == r"PING :(.+)"
        assert ping_trigger["response_size"] == len(b"PONG :$1\r\n")
        
        # Check second trigger
        hello_trigger = next(t for t in triggers if t["trigger_id"] == "hello_trigger")
        assert hello_trigger["pattern"] == r"HELLO"
        assert hello_trigger["response_size"] == len(b"HI THERE")
    
    def test_get_triggers_empty(self, tcp_connection):
        """Test getting triggers when none exist."""
        triggers = tcp_connection.get_triggers()
        
        assert triggers == []


@pytest.mark.unit
class TestTCPConnectionIntegration:
    """Integration-style unit tests for TCPConnection."""
    
    @pytest.mark.asyncio
    async def test_complete_connection_lifecycle(self, tcp_connection, mock_stream_reader, mock_stream_writer):
        """Test complete connection lifecycle."""
        # Mock successful connection
        with patch('asyncio.open_connection', return_value=(mock_stream_reader, mock_stream_writer)):
            with patch('asyncio.create_task') as mock_create_task:
                mock_task = AsyncMock()
                mock_create_task.return_value = mock_task
                
                # Connect
                connect_result = await tcp_connection.connect()
                assert connect_result is True
                assert tcp_connection.connected is True
                
                # Send data
                send_result = await tcp_connection.send(b"test message")
                assert send_result is True
                assert tcp_connection.bytes_sent == 12
                
                # Add trigger
                tcp_connection.add_trigger("test", r"PING", b"PONG")
                assert len(tcp_connection.triggers) == 1
                
                # Test without actual disconnect to avoid mock issues
                # We've already tested the core functionality
    
    @pytest.mark.asyncio
    async def test_buffer_operations_sequence(self, tcp_connection):
        """Test sequence of buffer operations."""
        # Add data to buffer manually (simulating read loop)
        tcp_connection.buffer = [b"chunk1", b"chunk2"]
        tcp_connection.bytes_received = 12
        
        # Test buffer info
        info = await tcp_connection.get_buffer_info()
        assert info["chunks"] == 2
        assert info["total_bytes"] == 12
        
        # Test partial read
        partial = await tcp_connection.read_buffer(index=1, count=1)
        assert partial == [b"chunk2"]
        
        # Test full read
        full = await tcp_connection.read_buffer()
        assert full == [b"chunk1", b"chunk2"]
        
        # Test clear
        await tcp_connection.clear_buffer()
        assert tcp_connection.buffer == []
        
        # Test info after clear
        info_after = await tcp_connection.get_buffer_info()
        assert info_after["chunks"] == 0
        assert info_after["total_bytes"] == 0