"""In-memory storage for testing."""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class HubConnection:
    """Hub connection data."""
    hub_id: str
    connected_at: datetime
    last_seen: datetime
    version: str
    websocket: Any  # WebSocket connection


@dataclass
class TelemetryData:
    """Telemetry data entry."""
    timestamp: datetime
    port_id: str
    session_id: str
    data: str  # Base64 encoded
    data_size_bytes: int


@dataclass
class HealthData:
    """Health metrics data."""
    timestamp: datetime
    uptime_seconds: int
    system: Dict[str, Any]
    service: Dict[str, Any]
    errors: Dict[str, Any]


@dataclass
class DeviceEvent:
    """Device event data."""
    timestamp: datetime
    event_type: str
    port_id: str
    device_info: Optional[Dict[str, Any]] = None


@dataclass
class TaskStatus:
    """Task status data."""
    timestamp: datetime
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MemoryStore:
    """Thread-safe in-memory storage."""

    def __init__(self, max_telemetry_per_hub: int = 1000):
        """Initialize memory store.
        
        Args:
            max_telemetry_per_hub: Maximum telemetry entries per hub
        """
        self._lock = asyncio.Lock()
        self.max_telemetry_per_hub = max_telemetry_per_hub

        # Hub connections
        self._hubs: Dict[str, HubConnection] = {}

        # Telemetry data (hub_id -> list of entries)
        self._telemetry: Dict[str, List[TelemetryData]] = defaultdict(list)

        # Health data (hub_id -> latest entry)
        self._health: Dict[str, HealthData] = {}

        # Device events (hub_id -> list of events)
        self._device_events: Dict[str, List[DeviceEvent]] = defaultdict(list)

        # Task status (hub_id -> task_id -> status)
        self._task_status: Dict[str, Dict[str, TaskStatus]] = defaultdict(dict)

    # Hub Connection Management
    async def add_hub_connection(
        self, hub_id: str, websocket: Any, version: str = "1.0.0"
    ) -> None:
        """Add hub connection."""
        async with self._lock:
            now = datetime.utcnow()
            self._hubs[hub_id] = HubConnection(
                hub_id=hub_id,
                connected_at=now,
                last_seen=now,
                version=version,
                websocket=websocket,
            )

    async def remove_hub_connection(self, hub_id: str) -> None:
        """Remove hub connection."""
        async with self._lock:
            self._hubs.pop(hub_id, None)

    async def update_hub_last_seen(self, hub_id: str) -> None:
        """Update hub last seen timestamp."""
        async with self._lock:
            if hub_id in self._hubs:
                self._hubs[hub_id].last_seen = datetime.utcnow()

    async def get_hub_connection(self, hub_id: str) -> Optional[HubConnection]:
        """Get hub connection."""
        async with self._lock:
            return self._hubs.get(hub_id)

    async def get_all_hubs(self) -> List[HubConnection]:
        """Get all hub connections."""
        async with self._lock:
            return list(self._hubs.values())

    async def is_hub_connected(self, hub_id: str) -> bool:
        """Check if hub is connected."""
        async with self._lock:
            return hub_id in self._hubs

    # Telemetry Management
    async def add_telemetry(
        self,
        hub_id: str,
        port_id: str,
        session_id: str,
        data: str,
        data_size_bytes: int,
    ) -> None:
        """Add telemetry entry."""
        async with self._lock:
            entry = TelemetryData(
                timestamp=datetime.utcnow(),
                port_id=port_id,
                session_id=session_id,
                data=data,
                data_size_bytes=data_size_bytes,
            )
            self._telemetry[hub_id].append(entry)

            # Limit size
            if len(self._telemetry[hub_id]) > self.max_telemetry_per_hub:
                self._telemetry[hub_id] = self._telemetry[hub_id][
                    -self.max_telemetry_per_hub :
                ]

    async def get_telemetry(
        self, hub_id: str, limit: Optional[int] = None
    ) -> List[TelemetryData]:
        """Get telemetry entries for hub."""
        async with self._lock:
            entries = self._telemetry.get(hub_id, [])
            if limit:
                return entries[-limit:]
            return entries.copy()

    async def get_telemetry_stats(self, hub_id: str) -> Dict[str, Any]:
        """Get telemetry statistics."""
        async with self._lock:
            entries = self._telemetry.get(hub_id, [])
            total_bytes = sum(e.data_size_bytes for e in entries)
            return {
                "count": len(entries),
                "total_bytes": total_bytes,
            }

    # Health Management
    async def update_health(
        self,
        hub_id: str,
        uptime_seconds: int,
        system: Dict[str, Any],
        service: Dict[str, Any],
        errors: Dict[str, Any],
    ) -> None:
        """Update health metrics."""
        async with self._lock:
            self._health[hub_id] = HealthData(
                timestamp=datetime.utcnow(),
                uptime_seconds=uptime_seconds,
                system=system,
                service=service,
                errors=errors,
            )

    async def get_health(self, hub_id: str) -> Optional[HealthData]:
        """Get latest health metrics."""
        async with self._lock:
            return self._health.get(hub_id)

    # Device Events
    async def add_device_event(
        self,
        hub_id: str,
        event_type: str,
        port_id: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add device event."""
        async with self._lock:
            event = DeviceEvent(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                port_id=port_id,
                device_info=device_info,
            )
            self._device_events[hub_id].append(event)

    async def get_device_events(
        self, hub_id: str, limit: Optional[int] = None
    ) -> List[DeviceEvent]:
        """Get device events."""
        async with self._lock:
            events = self._device_events.get(hub_id, [])
            if limit:
                return events[-limit:]
            return events.copy()

    # Task Status
    async def update_task_status(
        self,
        hub_id: str,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status."""
        async with self._lock:
            self._task_status[hub_id][task_id] = TaskStatus(
                timestamp=datetime.utcnow(),
                task_id=task_id,
                status=status,
                progress=progress,
                result=result,
                error=error,
            )

    async def get_task_status(
        self, hub_id: str, task_id: str
    ) -> Optional[TaskStatus]:
        """Get task status."""
        async with self._lock:
            return self._task_status.get(hub_id, {}).get(task_id)

    async def get_all_task_statuses(self, hub_id: str) -> Dict[str, TaskStatus]:
        """Get all task statuses for hub."""
        async with self._lock:
            return self._task_status.get(hub_id, {}).copy()


# Global instance
_store: Optional[MemoryStore] = None


def get_store() -> MemoryStore:
    """Get memory store singleton."""
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store
