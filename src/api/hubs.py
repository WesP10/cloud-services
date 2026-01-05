"""Hub management API endpoints."""

import uuid
import base64
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models import (
    HubListResponse,
    HubInfo,
    TelemetryListResponse,
    TelemetryEntry,
    SerialWriteRequest,
    FlashFirmwareRequest,
    RestartDeviceRequest,
    CommandResponse,
)
from ..auth.dependencies import get_current_user
from ..storage.memory_store import get_store
from ..services.command_service import send_command_to_hub

router = APIRouter(prefix="/api/hubs", tags=["hubs"])


@router.get("", response_model=HubListResponse)
async def list_hubs(current_user: dict = Depends(get_current_user)):
    """
    List all connected hubs.
    """
    store = get_store()
    hubs = await store.get_all_hubs()

    hub_infos = [
        HubInfo(
            hubId=hub.hub_id,
            connected=True,
            connectedAt=hub.connected_at,
            lastSeen=hub.last_seen,
            version=hub.version,
        )
        for hub in hubs
    ]

    return HubListResponse(hubs=hub_infos, count=len(hub_infos))


@router.get("/{hub_id}", response_model=HubInfo)
async def get_hub(hub_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get hub details.
    """
    store = get_store()
    hub = await store.get_hub_connection(hub_id)

    if not hub:
        raise HTTPException(status_code=404, detail=f"Hub not found: {hub_id}")

    return HubInfo(
        hubId=hub.hub_id,
        connected=True,
        connectedAt=hub.connected_at,
        lastSeen=hub.last_seen,
        version=hub.version,
    )


@router.get("/{hub_id}/telemetry", response_model=TelemetryListResponse)
async def get_telemetry(
    hub_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """
    Get telemetry data for hub.
    """
    store = get_store()

    # Check if hub exists
    if not await store.is_hub_connected(hub_id):
        raise HTTPException(status_code=404, detail=f"Hub not found: {hub_id}")

    # Get telemetry
    telemetry_data = await store.get_telemetry(hub_id, limit=limit)
    stats = await store.get_telemetry_stats(hub_id)

    entries = [
        TelemetryEntry(
            timestamp=entry.timestamp,
            portId=entry.port_id,
            sessionId=entry.session_id,
            data=entry.data,
            dataSizeBytes=entry.data_size_bytes,
        )
        for entry in telemetry_data
    ]

    return TelemetryListResponse(
        hubId=hub_id,
        telemetry=entries,
        count=stats["count"],
        totalBytes=stats["total_bytes"],
    )


@router.post("/{hub_id}/commands/write", response_model=CommandResponse)
async def send_serial_write_command(
    hub_id: str,
    request: SerialWriteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Send serial write command to hub.
    """
    store = get_store()

    # Check if hub is connected
    if not await store.is_hub_connected(hub_id):
        raise HTTPException(status_code=404, detail=f"Hub not connected: {hub_id}")

    # Generate command ID
    command_id = f"cmd-{uuid.uuid4()}"

    # Prepare command
    command = {
        "commandId": command_id,
        "commandType": "serial_write",
        "portId": request.portId,
        "params": {
            "data": request.data,
            "encoding": request.encoding,
        },
        "priority": request.priority,
    }

    # Send command
    success = await send_command_to_hub(hub_id, command)

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to send command to hub"
        )

    return CommandResponse(
        commandId=command_id,
        hubId=hub_id,
        status="sent",
        message="Command sent to hub",
    )


@router.post("/{hub_id}/commands/flash", response_model=CommandResponse)
async def send_flash_firmware_command(
    hub_id: str,
    request: FlashFirmwareRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Send flash firmware command to hub.
    """
    store = get_store()

    # Check if hub is connected
    if not await store.is_hub_connected(hub_id):
        raise HTTPException(status_code=404, detail=f"Hub not connected: {hub_id}")

    # Generate command ID
    command_id = f"cmd-{uuid.uuid4()}"

    # Prepare command
    command = {
        "commandId": command_id,
        "commandType": "flash",
        "portId": request.portId,
        "params": {
            "firmwareData": request.firmwareData,
            "boardFqbn": request.boardFqbn,
        },
        "priority": request.priority,
    }

    # Send command
    success = await send_command_to_hub(hub_id, command)

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to send command to hub"
        )

    return CommandResponse(
        commandId=command_id,
        hubId=hub_id,
        status="sent",
        message="Flash command sent to hub",
    )


@router.post("/{hub_id}/commands/restart", response_model=CommandResponse)
async def send_restart_device_command(
    hub_id: str,
    request: RestartDeviceRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Send restart device command to hub.
    """
    store = get_store()

    # Check if hub is connected
    if not await store.is_hub_connected(hub_id):
        raise HTTPException(status_code=404, detail=f"Hub not connected: {hub_id}")

    # Generate command ID
    command_id = f"cmd-{uuid.uuid4()}"

    # Prepare command
    command = {
        "commandId": command_id,
        "commandType": "restart",
        "portId": request.portId,
        "params": {},
        "priority": request.priority,
    }

    # Send command
    success = await send_command_to_hub(hub_id, command)

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to send command to hub"
        )

    return CommandResponse(
        commandId=command_id,
        hubId=hub_id,
        status="sent",
        message="Restart command sent to hub",
    )
