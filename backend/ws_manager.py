"""
WebSocket Connection Manager.

Manages two pools of connections per business_id:
  - Admin dashboards: receive fleet-wide broadcasts
  - Driver clients:   send location updates, receive route pushes
"""

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # business_id → set of admin WebSocket connections
        self._admins: dict[int, set[WebSocket]] = defaultdict(set)
        # business_id → {driver_id: WebSocket}
        self._drivers: dict[int, dict[int, WebSocket]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect_admin(self, ws: WebSocket, business_id: int) -> None:
        await ws.accept()
        async with self._lock:
            self._admins[business_id].add(ws)
        logger.info("Admin connected | business=%d | total_admins=%d", business_id, len(self._admins[business_id]))

    async def connect_driver(self, ws: WebSocket, business_id: int, driver_id: int) -> None:
        await ws.accept()
        async with self._lock:
            self._drivers[business_id][driver_id] = ws
        logger.info("Driver connected | driver=%d | business=%d", driver_id, business_id)

    async def disconnect_admin(self, ws: WebSocket, business_id: int) -> None:
        async with self._lock:
            self._admins[business_id].discard(ws)
        logger.info("Admin disconnected | business=%d | remaining=%d", business_id, len(self._admins[business_id]))

    async def disconnect_driver(self, business_id: int, driver_id: int) -> None:
        async with self._lock:
            self._drivers[business_id].pop(driver_id, None)
        logger.info("Driver disconnected | driver=%d | business=%d", driver_id, business_id)

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def broadcast_to_admins(self, business_id: int, message: str) -> None:
        """Broadcast a JSON string to every admin watching this business."""
        async with self._lock:
            targets = list(self._admins.get(business_id, set()))

        if not targets:
            return

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception as exc:
                logger.warning("Failed to send to admin; removing. Error: %s", exc)
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._admins[business_id].discard(ws)

    async def push_to_driver(self, business_id: int, driver_id: int, message: str) -> None:
        """Push a JSON string directly to a specific driver (e.g. route update)."""
        async with self._lock:
            ws = self._drivers.get(business_id, {}).get(driver_id)

        if ws is not None:
            try:
                await ws.send_text(message)
            except Exception as exc:
                logger.warning("Failed to push to driver %d: %s", driver_id, exc)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_active_driver_ids(self, business_id: int) -> list[int]:
        return list(self._drivers.get(business_id, {}).keys())

    def admin_count(self, business_id: int) -> int:
        return len(self._admins.get(business_id, set()))

    def driver_count(self, business_id: int) -> int:
        return len(self._drivers.get(business_id, {}))


# Singleton shared across the application
manager = ConnectionManager()
