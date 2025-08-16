"""Shared test fixtures and configuration."""

import asyncio
import socket
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

from TcpSocketMCP.connection import TCPConnection
from TcpSocketMCP.server import TCPSocketServer


@pytest.fixture
def mock_connection_id() -> str:
    """Provide a test connection ID."""
    return "test-conn-123"


@pytest.fixture
def test_host() -> str:
    """Provide a test host."""
    return "localhost"


@pytest.fixture
def test_port() -> int:
    """Provide a test port."""
    return 12345


@pytest.fixture
def tcp_connection(mock_connection_id: str, test_host: str, test_port: int) -> TCPConnection:
    """Create a TCPConnection instance for testing."""
    return TCPConnection(mock_connection_id, test_host, test_port)


@pytest.fixture
def mock_stream_reader() -> AsyncMock:
    """Create a mock StreamReader."""
    reader = AsyncMock()
    reader.read = AsyncMock(return_value=b"test data")
    return reader


@pytest.fixture
def mock_stream_writer() -> AsyncMock:
    """Create a mock StreamWriter."""
    writer = AsyncMock()
    writer.write = Mock()
    writer.drain = AsyncMock()
    writer.close = Mock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.fixture
async def mcp_server() -> AsyncGenerator[TCPSocketServer, None]:
    """Create an MCP server instance for testing."""
    server = TCPSocketServer()
    await server.setup()
    yield server
    # Cleanup any connections
    for conn in list(server.connections.values()):
        await conn.disconnect()
    server.connections.clear()


@pytest.fixture
def available_port() -> int:
    """Find an available port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def sample_hex_data() -> str:
    """Provide sample hex encoded data."""
    return "48656C6C6F20576F726C64"  # "Hello World"


@pytest.fixture
def sample_binary_data() -> bytes:
    """Provide sample binary data."""
    return b"Hello World"


@pytest.fixture
def sample_trigger_pattern() -> str:
    """Provide a sample trigger pattern."""
    return r"^PING :(.+)"


@pytest.fixture
def sample_trigger_response() -> bytes:
    """Provide a sample trigger response."""
    return b"PONG :$1\r\n"