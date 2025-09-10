"""
WebSocket client with automatic reconnection

Handles real-time communication with the Coact server.
"""

import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, Awaitable
from enum import Enum

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from coact_client.config.settings import settings
from coact_client.core.device import device_manager, DeviceError

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class WebSocketError(Exception):
    """WebSocket related errors"""
    pass


class WebSocketClient:
    """WebSocket client with automatic reconnection and message handling"""
    
    def __init__(self):
        self.device_token: Optional[str] = None
        self.ws_url: Optional[str] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 1
        self.max_reconnect_delay = 300
        self.heartbeat_interval = 30
        self.message_timeout = 30
        
        # Event handlers
        self.on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_message: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.on_error: Optional[Callable[[Exception], Awaitable[None]]] = None
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._connection_task: Optional[asyncio.Task] = None
        self._message_loop_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    async def initialize(self) -> None:
        """Initialize WebSocket client with device information"""
        device_info = await device_manager.ensure_valid_device()
        if not device_info:
            raise WebSocketError("Device not enrolled or invalid")
        
        self.device_token = device_info.device_token
        self.ws_url = device_info.wss_url
        
        logger.info(f"WebSocket client initialized for device: {device_info.device_id}")
    
    async def connect(self) -> None:
        """Connect to WebSocket server"""
        if self.state in [ConnectionState.CONNECTING, ConnectionState.CONNECTED]:
            return
        
        if not self.device_token or not self.ws_url:
            await self.initialize()
        
        self.state = ConnectionState.CONNECTING
        logger.info("Connecting to WebSocket server...")
        
        try:
            await self._establish_connection()
            self.state = ConnectionState.CONNECTED
            self.reconnect_attempts = 0
            logger.info("WebSocket connection established")
            
            # Start background tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._message_loop_task = asyncio.create_task(self._message_loop())
            
            # Call connect handler
            if self.on_connect:
                await self.on_connect()
                
        except Exception as e:
            self.state = ConnectionState.FAILED
            logger.error(f"Failed to connect to WebSocket: {e}")
            if self.on_error:
                await self.on_error(e)
            raise WebSocketError(f"Connection failed: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionClosed, InvalidStatusCode, OSError))
    )
    async def _establish_connection(self) -> None:
        """Establish WebSocket connection with retry"""
        ws_endpoint = f"{self.ws_url}/v1/ws/agent?token={self.device_token}"
        
        # Connect with timeout (removed extra_headers for compatibility)
        self.websocket = await asyncio.wait_for(
            websockets.connect(
                ws_endpoint,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=1024 * 1024,  # 1MB max message size
            ),
            timeout=self.message_timeout
        )
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket server"""
        self._shutdown = True
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._message_loop_task:
            self._message_loop_task.cancel()
        if self._connection_task:
            self._connection_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self._heartbeat_task, self._message_loop_task, self._connection_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Close WebSocket connection
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        self.state = ConnectionState.DISCONNECTED
        logger.info("WebSocket disconnected")
        
        # Call disconnect handler
        if self.on_disconnect:
            await self.on_disconnect()
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to server"""
        if self.state != ConnectionState.CONNECTED or not self.websocket:
            raise WebSocketError("WebSocket not connected")
        
        try:
            message_json = json.dumps(message)
            await self.websocket.send(message_json)
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise WebSocketError(f"Failed to send message: {e}")
    
    async def send_heartbeat(self) -> None:
        """Send heartbeat message"""
        try:
            await self.send_message({"type": "heartbeat"})
        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")
    
    async def send_task_result(self, task_id: str, results: list, status: str = "completed") -> None:
        """Send task execution result"""
        message = {
            "type": "task.result",
            "task_id": task_id,
            "device_id": device_manager.get_device_info().device_id if device_manager.get_device_info() else None,
            "results": results,
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.send_message(message)
        logger.info(f"Task result sent for task: {task_id}")
    
    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop"""
        try:
            while not self._shutdown and self.state == ConnectionState.CONNECTED:
                await self.send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
    
    async def _message_loop(self) -> None:
        """Background message processing loop"""
        try:
            while not self._shutdown and self.state == ConnectionState.CONNECTED:
                if not self.websocket:
                    break
                
                try:
                    # Wait for message with timeout
                    message_str = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=self.message_timeout
                    )
                    
                    # Parse and handle message
                    try:
                        message = json.loads(message_str)
                        await self._handle_message(message)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse message: {e}")
                    
                except asyncio.TimeoutError:
                    # No message received, continue
                    continue
                except ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Message loop error: {e}")
            if self.on_error:
                await self.on_error(e)
        
        # Connection lost, attempt reconnection
        if not self._shutdown:
            await self._handle_disconnect()
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming message"""
        message_type = message.get("type")
        logger.debug(f"Received message: {message_type}")
        
        # Update last activity
        self.last_message_time = datetime.now(timezone.utc)
        
        # Call message handler
        if self.on_message:
            try:
                await self.on_message(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                if self.on_error:
                    await self.on_error(e)
    
    async def _handle_disconnect(self) -> None:
        """Handle connection loss and attempt reconnection"""
        if self._shutdown:
            return
        
        self.state = ConnectionState.RECONNECTING
        logger.warning("Connection lost, attempting to reconnect...")
        
        # Call disconnect handler
        if self.on_disconnect:
            try:
                await self.on_disconnect()
            except Exception as e:
                logger.error(f"Disconnect handler error: {e}")
        
        # Start reconnection process
        self._connection_task = asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self) -> None:
        """Background reconnection loop"""
        try:
            while (not self._shutdown and 
                   self.state == ConnectionState.RECONNECTING and 
                   self.reconnect_attempts < self.max_reconnect_attempts):
                
                self.reconnect_attempts += 1
                delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), self.max_reconnect_delay)
                
                logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay}s")
                await asyncio.sleep(delay)
                
                try:
                    # Refresh device token if needed
                    device_info = await device_manager.ensure_valid_device()
                    if device_info:
                        self.device_token = device_info.device_token
                    
                    # Attempt reconnection
                    await self._establish_connection()
                    
                    # Success
                    self.state = ConnectionState.CONNECTED
                    self.reconnect_attempts = 0
                    logger.info("WebSocket reconnected successfully")
                    
                    # Restart background tasks
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    self._message_loop_task = asyncio.create_task(self._message_loop())
                    
                    # Call connect handler
                    if self.on_connect:
                        await self.on_connect()
                    
                    return
                    
                except Exception as e:
                    logger.warning(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
            
            # Max attempts reached
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.state = ConnectionState.FAILED
                logger.error("Max reconnection attempts reached, giving up")
                if self.on_error:
                    await self.on_error(WebSocketError("Max reconnection attempts reached"))
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.state = ConnectionState.FAILED
            logger.error(f"Reconnection loop error: {e}")
            if self.on_error:
                await self.on_error(e)
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        try:
            # Primary check: state must be CONNECTED
            if self.state != ConnectionState.CONNECTED:
                return False
            
            # Secondary check: websocket object must exist  
            if not self.websocket:
                return False
                
            # If we have a websocket and state is CONNECTED, we're connected
            # Don't check 'closed' attribute as it may not exist in all websocket implementations
            return True
            
        except Exception as e:
            logger.debug(f"Error checking connection status: {e}")
            return False
    
    def get_state(self) -> ConnectionState:
        """Get current connection state"""
        return self.state


# Global WebSocket client instance
websocket_client = WebSocketClient()