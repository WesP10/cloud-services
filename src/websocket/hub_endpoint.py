"""WebSocket endpoint for hub connections."""

import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..models import (
    HubHandshake,
    TelemetryMessage,
    HealthMessage,
    DeviceEventMessage,
    TaskStatusMessage,
)
from ..auth.auth_service import verify_device_token
from ..storage.memory_store import get_store

logger = logging.getLogger(__name__)


async def handle_hub_connection(websocket: WebSocket):
    """
    Handle WebSocket connection from RPi hub.
    
    Expects handshake message with device token authentication.
    Routes incoming messages to appropriate handlers.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else "unknown"
    
    logger.info(
        f"WebSocket connection attempt from {client_host}:{client_port}",
        extra={"client_host": client_host, "client_port": client_port}
    )
    
    await websocket.accept()
    
    logger.info(
        f"WebSocket connection accepted from {client_host}:{client_port}",
        extra={"client_host": client_host, "client_port": client_port}
    )
    
    hub_id: str = None

    try:
        # Wait for handshake
        logger.info("Waiting for handshake message...")
        handshake_data = await websocket.receive_text()
        logger.info(f"Received handshake: {handshake_data}")
        handshake_dict = json.loads(handshake_data)

        # Validate handshake
        try:
            handshake = HubHandshake(**handshake_dict)
        except ValidationError as e:
            logger.warning(f"Invalid handshake: {e}")
            await websocket.close(code=1008, reason="Invalid handshake")
            return

        # Verify device token
        authenticated_hub_id = verify_device_token(handshake.deviceToken)
        if not authenticated_hub_id:
            logger.warning(f"Invalid device token for hub: {handshake.hubId}")
            await websocket.close(code=1008, reason="Invalid device token")
            return

        # Verify hub ID matches token
        if authenticated_hub_id != handshake.hubId:
            logger.warning(
                f"Hub ID mismatch: token={authenticated_hub_id}, claimed={handshake.hubId}"
            )
            await websocket.close(code=1008, reason="Hub ID mismatch")
            return

        hub_id = handshake.hubId
        logger.info(f"Hub connected: {hub_id} (version {handshake.version})")

        # Register connection
        store = get_store()
        await store.add_hub_connection(hub_id, websocket, handshake.version)

        # Send acknowledgment (optional)
        ack = {
            "type": "hub_connected",
            "hubId": hub_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_text(json.dumps(ack))

        # Message loop
        while True:
            message_data = await websocket.receive_text()
            message_dict = json.loads(message_data)

            # Update last seen
            await store.update_hub_last_seen(hub_id)

            # Route message
            await route_hub_message(hub_id, message_dict)

    except WebSocketDisconnect:
        logger.info(f"Hub disconnected: {hub_id}")

    except Exception as e:
        logger.error(f"Error in hub connection: {e}", exc_info=True)

    finally:
        # Cleanup
        if hub_id:
            store = get_store()
            await store.remove_hub_connection(hub_id)
            logger.info(f"Hub connection cleaned up: {hub_id}")


async def route_hub_message(hub_id: str, message: dict):
    """
    Route incoming hub message to appropriate handler.
    
    Args:
        hub_id: Hub identifier
        message: Message dictionary
    """
    message_type = message.get("type")

    try:
        if message_type == "telemetry":
            await handle_telemetry(hub_id, message)
        elif message_type == "health":
            await handle_health(hub_id, message)
        elif message_type == "device_event":
            await handle_device_event(hub_id, message)
        elif message_type == "task_status":
            await handle_task_status(hub_id, message)
        else:
            logger.warning(f"Unknown message type from {hub_id}: {message_type}")

    except ValidationError as e:
        logger.warning(f"Invalid message from {hub_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling message from {hub_id}: {e}", exc_info=True)


async def handle_telemetry(hub_id: str, message: dict):
    """Handle telemetry message."""
    telemetry = TelemetryMessage(**message)
    store = get_store()

    # Decode data size
    import base64
    data_bytes = base64.b64decode(telemetry.data)

    await store.add_telemetry(
        hub_id=hub_id,
        port_id=telemetry.portId,
        session_id=telemetry.sessionId,
        data=telemetry.data,
        data_size_bytes=len(data_bytes),
    )

    logger.debug(f"Telemetry from {hub_id}: {len(data_bytes)} bytes")


async def handle_health(hub_id: str, message: dict):
    """Handle health message."""
    health = HealthMessage(**message)
    store = get_store()

    await store.update_health(
        hub_id=hub_id,
        uptime_seconds=health.uptime_seconds,
        system=health.system,
        service=health.service,
        errors=health.errors,
    )

    logger.info(
        f"Health from {hub_id}: uptime={health.uptime_seconds}s, "
        f"cpu={health.system.get('cpu', {}).get('percent')}%"
    )


async def handle_device_event(hub_id: str, message: dict):
    """Handle device event message."""
    event = DeviceEventMessage(**message)
    store = get_store()

    await store.add_device_event(
        hub_id=hub_id,
        event_type=event.eventType,
        port_id=event.portId,
        device_info=event.deviceInfo,
    )

    logger.info(f"Device event from {hub_id}: {event.eventType} - {event.portId}")


async def handle_task_status(hub_id: str, message: dict):
    """Handle task status message."""
    task_status = TaskStatusMessage(**message)
    store = get_store()

    await store.update_task_status(
        hub_id=hub_id,
        task_id=task_status.taskId,
        status=task_status.status,
        progress=task_status.progress,
        result=task_status.result,
        error=task_status.error,
    )

    logger.info(
        f"Task status from {hub_id}: {task_status.taskId} - {task_status.status}"
    )
