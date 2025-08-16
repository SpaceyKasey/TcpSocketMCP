"""Test TCP server helpers for integration testing."""

import asyncio
import logging
import re
from typing import Optional, Callable, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class TestTCPServer:
    """Base test TCP server for integration testing."""
    
    def __init__(self, host: str = "localhost", port: int = 0):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.clients: list = []
        self.running = False
        
    async def start(self) -> int:
        """Start the server and return the actual port."""
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        self.running = True
        
        # Get the actual port if 0 was specified
        if self.port == 0:
            self.port = self.server.sockets[0].getsockname()[1]
            
        logger.info(f"Test server started on {self.host}:{self.port}")
        return self.port
        
    async def stop(self):
        """Stop the server and close all clients."""
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
                await client.wait_closed()
            except Exception as e:
                logger.warning(f"Error closing client: {e}")
        self.clients.clear()
        
        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        logger.info(f"Test server stopped on {self.host}:{self.port}")
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connections - override in subclasses."""
        self.clients.append(writer)
        try:
            await self._client_handler(reader, writer)
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            if writer in self.clients:
                self.clients.remove(writer)
                
    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Override this method in subclasses."""
        raise NotImplementedError


class EchoServer(TestTCPServer):
    """Simple echo server that returns whatever it receives."""
    
    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Echo back all received data."""
        while self.running:
            try:
                data = await reader.read(4096)
                if not data:
                    break
                    
                writer.write(data)
                await writer.drain()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Echo server error: {e}")
                break


class HTTPLikeServer(TestTCPServer):
    """HTTP-like server for testing protocol interactions."""
    
    def __init__(self, host: str = "localhost", port: int = 0, 
                 response: bytes = b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello, World!"):
        super().__init__(host, port)
        self.response = response
        
    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle HTTP-like requests."""
        try:
            # Read until we get a complete HTTP request (double CRLF)
            request = b""
            while b"\r\n\r\n" not in request:
                data = await reader.read(1024)
                if not data:
                    break
                request += data
                
            if request:
                # Send response
                writer.write(self.response)
                await writer.drain()
                
            # Close connection after response (HTTP/1.0 style)
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.error(f"HTTP server error: {e}")


class IRCLikeServer(TestTCPServer):
    """IRC-like server for testing trigger functionality."""
    
    def __init__(self, host: str = "localhost", port: int = 0):
        super().__init__(host, port)
        self.ping_interval = 1.0  # Send PING every second
        
    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle IRC-like protocol with PING/PONG."""
        try:
            # Start ping task
            ping_task = asyncio.create_task(self._ping_loop(writer))
            
            # Handle incoming messages
            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=0.1)
                    if not data:
                        break
                        
                    # Process received data
                    message = data.decode('utf-8', errors='ignore')
                    await self._process_message(message, writer)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"IRC server message error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"IRC server error: {e}")
        finally:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass
                
    async def _ping_loop(self, writer: asyncio.StreamWriter):
        """Send periodic PING messages."""
        ping_count = 0
        while self.running:
            try:
                await asyncio.sleep(self.ping_interval)
                ping_msg = f"PING :server{ping_count}\r\n".encode()
                writer.write(ping_msg)
                await writer.drain()
                ping_count += 1
            except Exception as e:
                logger.error(f"PING error: {e}")
                break
                
    async def _process_message(self, message: str, writer: asyncio.StreamWriter):
        """Process IRC-like messages."""
        lines = message.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('PONG'):
                # Client responded to PING
                logger.debug(f"Received PONG: {line}")
            elif line.startswith('NICK'):
                # Nickname command
                response = ":server 001 nickname :Welcome\r\n"
                writer.write(response.encode())
                await writer.drain()


class SlowServer(TestTCPServer):
    """Server that responds slowly for testing timing."""
    
    def __init__(self, host: str = "localhost", port: int = 0, delay: float = 1.0):
        super().__init__(host, port)
        self.delay = delay
        
    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Respond slowly to requests."""
        try:
            data = await reader.read(4096)
            if data:
                # Wait before responding
                await asyncio.sleep(self.delay)
                
                # Echo back with a timestamp
                response = f"SLOW_RESPONSE:{data.decode('utf-8', errors='ignore')}"
                writer.write(response.encode())
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Slow server error: {e}")


class MalformedDataServer(TestTCPServer):
    """Server that sends malformed data for error testing."""
    
    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Send various types of malformed data."""
        try:
            data = await reader.read(4096)
            if data:
                # Send different types of malformed responses
                malformed_responses = [
                    b"\x00\x01\x02\x03\x04\x05",  # Binary data
                    b"\xff\xfe\xfd\xfc",  # Invalid UTF-8
                    b"PARTIAL_RESP",  # Incomplete response
                    b"",  # Empty response
                ]
                
                for response in malformed_responses:
                    writer.write(response)
                    await writer.drain()
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Malformed server error: {e}")


@asynccontextmanager
async def test_server(server_class: type, *args, **kwargs):
    """Context manager for test servers."""
    server = server_class(*args, **kwargs)
    try:
        port = await server.start()
        yield server, port
    finally:
        await server.stop()


# Convenience functions for common test servers
async def echo_server(host: str = "localhost", port: int = 0):
    """Create an echo server context manager."""
    return test_server(EchoServer, host, port)


async def http_server(host: str = "localhost", port: int = 0, response: bytes = None):
    """Create an HTTP-like server context manager."""
    kwargs = {'host': host, 'port': port}
    if response:
        kwargs['response'] = response
    return test_server(HTTPLikeServer, **kwargs)


async def irc_server(host: str = "localhost", port: int = 0):
    """Create an IRC-like server context manager."""
    return test_server(IRCLikeServer, host, port)


async def slow_server(host: str = "localhost", port: int = 0, delay: float = 1.0):
    """Create a slow server context manager."""
    return test_server(SlowServer, host, port, delay)


async def malformed_server(host: str = "localhost", port: int = 0):
    """Create a malformed data server context manager."""
    return test_server(MalformedDataServer, host, port)