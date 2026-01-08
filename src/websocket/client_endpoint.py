"""WebSocket endpoint for client (browser) connections."""

import json
import logging
from datetime import datetime
from typing import Set, Dict
from fastapi import WebSocket, WebSocketDisconnect, Query, status
from pydantic import ValidationError

from ..auth.dependencies import get_current_user_ws
from ..storage.memory_store import get_store

logger = logging.getLogger(__name__)


class ClientConnection:
    """Represents a connected client with their subscriptions."""
    
    def __init__(self, websocket: WebSocket, username: str):
        self.websocket = websocket
        self.username = username
        self.subscriptions: Set[tuple] = set()  # Set of (hub_id, port_id) tuples
    
    def is_subscribed(self, hub_id: str, port_id: str) -> bool:
        """Check if client is subscribed to a specific hub+port."""
        return (hub_id, port_id) in self.subscriptions
    
    def subscribe(self, hub_id: str, port_id: str) -> None:
        """Subscribe to a hub+port combination."""
        self.subscriptions.add((hub_id, port_id))
    
    def unsubscribe(self, hub_id: str, port_id: str) -> None:
        """Unsubscribe from a hub+port combination."""
        self.subscriptions.discard((hub_id, port_id))


# Global client connections manager
class ClientManager:
    """Manages all active client WebSocket connections."""
    
    def __init__(self):
        self.clients: Dict[str, ClientConnection] = {}  # connection_id -> ClientConnection
        self._connection_counter = 0
    
    def add_client(self, websocket: WebSocket, username: str) -> str:
        """Add a new client connection and return its ID."""
        self._connection_counter += 1
        connection_id = f"client_{self._connection_counter}"
        self.clients[connection_id] = ClientConnection(websocket, username)
        return connection_id
    
    def remove_client(self, connection_id: str) -> None:
        """Remove a client connection."""
        self.clients.pop(connection_id, None)
    
    async def broadcast_telemetry(self, hub_id: str, port_id: str, message: dict) -> None:
        """Broadcast telemetry to all subscribed clients."""
        disconnected = []
        
        for connection_id, client in self.clients.items():
            if client.is_subscribed(hub_id, port_id):
                try:
                    await client.websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to client {connection_id}: {e}")
                    disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.remove_client(connection_id)
    
    async def broadcast_health(self, hub_id: str, message: dict) -> None:
        """Broadcast health updates to all clients (not subscription-filtered)."""
        disconnected = []
        
        for connection_id, client in self.clients.items():
            try:
                await client.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending health to client {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.remove_client(connection_id)
    
    async def broadcast_device_event(self, hub_id: str, port_id: str, message: dict) -> None:
        """Broadcast device events to all subscribed clients."""
        disconnected = []
        
        for connection_id, client in self.clients.items():
            if client.is_subscribed(hub_id, port_id):
                try:
                    await client.websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending device event to client {connection_id}: {e}")
                    disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.remove_client(connection_id)

    async def broadcast_task_status(self, hub_id: str, message: dict) -> None:
        """Broadcast task status updates to all clients (no subscription filter)."""
        disconnected = []

        for connection_id, client in self.clients.items():
            try:
                await client.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending task status to client {connection_id}: {e}")
                disconnected.append(connection_id)

        for connection_id in disconnected:
            self.remove_client(connection_id)


# Global client manager instance
client_manager = ClientManager()


async def handle_client_connection(websocket: WebSocket, token: str = Query(...)):
    """
    Handle WebSocket connection from a browser client.
    
    Requires JWT token for authentication.
    Supports subscription-based telemetry streaming.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else "unknown"
    
    logger.info(
        f"Client WebSocket connection attempt from {client_host}:{client_port}"
    )
    
    try:
        # Authenticate using JWT token
        username = await get_current_user_ws(token)
        if not username:
            logger.warning(f"Invalid token from {client_host}:{client_port}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return
    
    await websocket.accept()
    
    logger.info(f"Client WebSocket connected: {username} from {client_host}:{client_port}")
    
    # Register client connection
    connection_id = client_manager.add_client(websocket, username)
    
    try:
        # Send welcome message
        welcome = {
            "type": "connected",
            "message": "Connected to telemetry stream",
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_text(json.dumps(welcome))
        
        # Message loop
        while True:
            message_data = await websocket.receive_text()
            message_dict = json.loads(message_data)
            
            # Route message
            await route_client_message(connection_id, message_dict)
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {username}")
    
    except Exception as e:
        logger.error(f"Error in client connection: {e}", exc_info=True)
    
    finally:
        # Cleanup
        client_manager.remove_client(connection_id)
        logger.info(f"Client connection cleaned up: {username}")


async def route_client_message(connection_id: str, message: dict):
    """
    Route incoming client message to appropriate handler.
    
    Args:
        connection_id: Client connection identifier
        message: Message dictionary
    """
    message_type = message.get("type")
    
    try:
        if message_type == "subscribe":
            await handle_subscribe(connection_id, message)
        elif message_type == "unsubscribe":
            await handle_unsubscribe(connection_id, message)
        else:
            logger.warning(f"Unknown message type from client {connection_id}: {message_type}")
    
    except ValidationError as e:
        logger.warning(f"Invalid message from client {connection_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling message from client {connection_id}: {e}", exc_info=True)


async def handle_subscribe(connection_id: str, message: dict):
    """Handle subscription request from client."""
    client = client_manager.clients.get(connection_id)
    if not client:
        return
    
    subscriptions = message.get("subscriptions", [])
    
    for sub in subscriptions:
        hub_id = sub.get("hubId")
        port_id = sub.get("portId")
        
        if hub_id and port_id:
            client.subscribe(hub_id, port_id)
            logger.info(f"Client {client.username} subscribed to {hub_id}:{port_id}")
    
    # Send confirmation
    confirmation = {
        "type": "subscription_status",
        "subscriptions": [
            {
                "hubId": hub_id,
                "portId": port_id,
                "status": "active"
            }
            for hub_id, port_id in client.subscriptions
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
    await client.websocket.send_text(json.dumps(confirmation))


async def handle_unsubscribe(connection_id: str, message: dict):
    """Handle unsubscription request from client."""
    client = client_manager.clients.get(connection_id)
    if not client:
        return
    
    subscriptions = message.get("subscriptions", [])
    
    for sub in subscriptions:
        hub_id = sub.get("hubId")
        port_id = sub.get("portId")
        
        if hub_id and port_id:
            client.unsubscribe(hub_id, port_id)
            logger.info(f"Client {client.username} unsubscribed from {hub_id}:{port_id}")
    
    # Send confirmation
    confirmation = {
        "type": "subscription_status",
        "subscriptions": [
            {
                "hubId": hub_id,
                "portId": port_id,
                "status": "inactive"
            }
            for sub in subscriptions
            if (hub_id := sub.get("hubId")) and (port_id := sub.get("portId"))
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
    await client.websocket.send_text(json.dumps(confirmation))


def get_client_manager() -> ClientManager:
    """Get the global client manager instance."""
    return client_manager
