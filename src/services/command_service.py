"""Command service for sending commands to hubs."""

import json
from typing import Dict, Any
import logging

from ..storage.memory_store import get_store

logger = logging.getLogger(__name__)


async def send_command_to_hub(hub_id: str, command: Dict[str, Any]) -> bool:
    """
    Send command to connected hub via WebSocket.
    
    Args:
        hub_id: Target hub ID
        command: Command dictionary
        
    Returns:
        True if command was sent successfully
    """
    store = get_store()

    # Get hub connection
    hub = await store.get_hub_connection(hub_id)
    if not hub:
        logger.warning(f"Hub not connected: {hub_id}")
        return False

    # Prepare command envelope
    envelope = {
        "type": "command",
        "command": command,
    }

    try:
        # Send via WebSocket
        await hub.websocket.send_text(json.dumps(envelope))
        logger.info(f"Command sent to hub {hub_id}: {command['commandId']}")
        return True

    except Exception as e:
        logger.error(f"Error sending command to hub {hub_id}: {e}")
        return False
