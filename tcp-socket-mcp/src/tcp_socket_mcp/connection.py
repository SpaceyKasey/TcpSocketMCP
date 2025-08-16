"""TCP Connection management with buffer and trigger support."""

import asyncio
import re
from typing import Optional, Dict, List, Tuple, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TCPConnection:
    """Manages a single TCP connection with buffer and trigger support."""
    
    def __init__(self, connection_id: str, host: str, port: int):
        self.connection_id = connection_id
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.buffer: List[bytes] = []
        self.triggers: Dict[str, Tuple[str, bytes]] = {}  # pattern -> (trigger_id, response)
        self.connected = False
        self.created_at = datetime.now()
        self.bytes_sent = 0
        self.bytes_received = 0
        self._read_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Establish TCP connection."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.connected = True
            # Start reading task
            self._read_task = asyncio.create_task(self._read_loop())
            logger.info(f"Connection {self.connection_id} established to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect {self.connection_id}: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close the TCP connection."""
        self.connected = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing connection {self.connection_id}: {e}")
        
        self.reader = None
        self.writer = None
        logger.info(f"Connection {self.connection_id} closed")
    
    async def send(self, data: bytes) -> bool:
        """Send data over the connection."""
        if not self.connected or not self.writer:
            return False
        
        try:
            self.writer.write(data)
            await self.writer.drain()
            self.bytes_sent += len(data)
            logger.debug(f"Sent {len(data)} bytes on connection {self.connection_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending data on {self.connection_id}: {e}")
            self.connected = False
            return False
    
    async def _read_loop(self):
        """Continuously read data from the connection."""
        while self.connected and self.reader:
            try:
                data = await self.reader.read(4096)
                if not data:
                    logger.info(f"Connection {self.connection_id} closed by remote")
                    self.connected = False
                    break
                
                async with self._lock:
                    self.buffer.append(data)
                    self.bytes_received += len(data)
                
                # Check triggers
                await self._check_triggers(data)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading from {self.connection_id}: {e}")
                self.connected = False
                break
    
    async def _check_triggers(self, data: bytes):
        """Check if received data matches any triggers."""
        try:
            data_str = data.decode('utf-8', errors='ignore')
            for pattern, (trigger_id, response) in self.triggers.items():
                if re.search(pattern, data_str):
                    logger.info(f"Trigger {trigger_id} matched on {self.connection_id}")
                    await self.send(response)
        except Exception as e:
            logger.error(f"Error checking triggers: {e}")
    
    async def read_buffer(self, index: Optional[int] = None, count: Optional[int] = None) -> List[bytes]:
        """Read data from buffer."""
        async with self._lock:
            if index is None:
                # Return all buffer
                return self.buffer.copy()
            elif count is None:
                # Return from index to end
                return self.buffer[index:].copy() if index < len(self.buffer) else []
            else:
                # Return specific range
                end_index = min(index + count, len(self.buffer))
                return self.buffer[index:end_index].copy() if index < len(self.buffer) else []
    
    async def clear_buffer(self):
        """Clear the buffer."""
        async with self._lock:
            self.buffer.clear()
    
    async def get_buffer_info(self) -> Dict:
        """Get information about the buffer."""
        async with self._lock:
            total_bytes = sum(len(chunk) for chunk in self.buffer)
            return {
                "connection_id": self.connection_id,
                "chunks": len(self.buffer),
                "total_bytes": total_bytes,
                "bytes_sent": self.bytes_sent,
                "bytes_received": self.bytes_received,
                "connected": self.connected
            }
    
    def add_trigger(self, trigger_id: str, pattern: str, response: bytes):
        """Add a trigger pattern and auto-response."""
        self.triggers[pattern] = (trigger_id, response)
    
    def remove_trigger(self, trigger_id: str) -> bool:
        """Remove a trigger by ID."""
        for pattern, (tid, _) in list(self.triggers.items()):
            if tid == trigger_id:
                del self.triggers[pattern]
                return True
        return False
    
    def get_triggers(self) -> List[Dict]:
        """Get all triggers for this connection."""
        return [
            {
                "trigger_id": tid,
                "pattern": pattern,
                "response_size": len(response)
            }
            for pattern, (tid, response) in self.triggers.items()
        ]