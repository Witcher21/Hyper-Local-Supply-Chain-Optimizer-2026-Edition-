"""
Live Fleet Tracking Router — SQLite compatible (no PostGIS).
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select, update

from database import AsyncSessionLocal
from models import Business, Driver, Order, OrderStatus
from schemas import (
    DriverResponse,
    DriverStatus,
    FleetBroadcast,
    LocationUpdate,
    WSClientType,
)
from ws_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Fleet Tracking"])


# ---------------------------------------------------------------------------
# Authentication helper
# ---------------------------------------------------------------------------


async def _authenticate(api_key: str, business_id: int) -> bool:
    """Return True if api_key belongs to the given business_id."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Business).where(
                Business.api_key == api_key,
                Business.id == business_id,
                Business.is_active == True,
            )
        )
        return result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _persist_location(
    driver_id: int,
    business_id: int,
    lat: float,
    lng: float,
    speed: float | None,
    heading: float | None,
    status: DriverStatus,
) -> None:
    """Write the driver's new location into the database."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Driver)
            .where(Driver.id == driver_id, Driver.business_id == business_id)
            .values(
                lat=lat,
                lng=lng,
                last_seen=datetime.now(timezone.utc),
                speed=speed,
                heading=heading,
                status=status,
            )
        )
        await db.commit()


# ---------------------------------------------------------------------------
# WebSocket entry point
# ---------------------------------------------------------------------------


@router.websocket("/ws/tracking/{business_id}")
async def tracking_websocket(
    websocket: WebSocket,
    business_id: int,
    api_key: str = Query(..., description="Business API key"),
    client_type: str = Query(..., description="'admin' or 'driver'"),
    driver_id: int | None = Query(None, description="Required when client_type=driver"),
):
    if not await _authenticate(api_key, business_id):
        await websocket.close(code=4003, reason="Forbidden: invalid API key or business_id")
        return

    if client_type not in (WSClientType.ADMIN, WSClientType.DRIVER):
        await websocket.close(code=4000, reason="client_type must be 'admin' or 'driver'")
        return

    if client_type == WSClientType.DRIVER and driver_id is None:
        await websocket.close(code=4000, reason="driver_id is required for driver connections")
        return

    if client_type == WSClientType.ADMIN:
        await _admin_loop(websocket, business_id)
    else:
        await _driver_loop(websocket, business_id, driver_id)


# ---------------------------------------------------------------------------
# Admin connection loop
# ---------------------------------------------------------------------------


async def _admin_loop(websocket: WebSocket, business_id: int) -> None:
    await manager.connect_admin(websocket, business_id)
    try:
        handshake = {
            "type": "connection_established",
            "client_type": "admin",
            "business_id": business_id,
            "active_driver_ids": manager.get_active_driver_ids(business_id),
        }
        await websocket.send_text(json.dumps(handshake))

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await manager.disconnect_admin(websocket, business_id)
    except Exception as exc:
        logger.error("Admin WebSocket error | business=%d | %s", business_id, exc)
        await manager.disconnect_admin(websocket, business_id)


# ---------------------------------------------------------------------------
# Driver connection loop
# ---------------------------------------------------------------------------


async def _driver_loop(websocket: WebSocket, business_id: int, driver_id: int) -> None:
    await manager.connect_driver(websocket, business_id, driver_id)

    await manager.broadcast_to_admins(
        business_id,
        json.dumps({
            "type": "driver_connected",
            "driver_id": driver_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }),
    )

    try:
        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "client_type": "driver",
                "driver_id": driver_id,
                "business_id": business_id,
            })
        )

        while True:
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": "Invalid JSON"})
                )
                continue

            msg_type = payload.get("type")

            if msg_type == "location_update":
                try:
                    update_msg = LocationUpdate(**payload)
                except Exception as exc:
                    await websocket.send_text(
                        json.dumps({"type": "error", "detail": str(exc)})
                    )
                    continue

                now = datetime.now(timezone.utc)

                await _persist_location(
                    driver_id=driver_id,
                    business_id=business_id,
                    lat=update_msg.lat,
                    lng=update_msg.lng,
                    speed=update_msg.speed,
                    heading=update_msg.heading,
                    status=update_msg.status,
                )

                broadcast = FleetBroadcast(
                    driver_id=driver_id,
                    lat=update_msg.lat,
                    lng=update_msg.lng,
                    speed=update_msg.speed,
                    heading=update_msg.heading,
                    status=update_msg.status,
                    timestamp=now,
                )
                await manager.broadcast_to_admins(business_id, broadcast.model_dump_json())

                await websocket.send_text(
                    json.dumps({"type": "ack", "driver_id": driver_id, "timestamp": now.isoformat()})
                )

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": f"Unknown message type: {msg_type}"})
                )

    except WebSocketDisconnect:
        await manager.disconnect_driver(business_id, driver_id)
        await manager.broadcast_to_admins(
            business_id,
            json.dumps({
                "type": "driver_disconnected",
                "driver_id": driver_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )
    except Exception as exc:
        logger.error("Driver WebSocket error | driver=%d | %s", driver_id, exc)
        await manager.disconnect_driver(business_id, driver_id)


# ---------------------------------------------------------------------------
# REST helpers
# ---------------------------------------------------------------------------


@router.get("/api/businesses/{business_id}/drivers", response_model=list[DriverResponse])
async def list_drivers(
    business_id: int,
    api_key: str = Query(...),
    active_only: bool = Query(True),
):
    """Return all drivers for a business."""
    if not await _authenticate(api_key, business_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    async with AsyncSessionLocal() as db:
        q = select(Driver).where(Driver.business_id == business_id)
        if active_only:
            q = q.where(Driver.is_active == True)
        result = await db.execute(q)
        drivers = result.scalars().all()

    return [
        DriverResponse(
            id=d.id,
            name=d.name,
            vehicle_type=d.vehicle_type,
            status=d.status,
            lat=d.lat,
            lng=d.lng,
            speed=float(d.speed) if d.speed is not None else None,
            heading=float(d.heading) if d.heading is not None else None,
            last_seen=d.last_seen,
            is_active=d.is_active,
        )
        for d in drivers
    ]


@router.get("/api/businesses/{business_id}/drivers/{driver_id}/orders", response_model=list)
async def get_driver_orders(
    business_id: int,
    driver_id: int,
    api_key: str = Query(...),
):
    """Return active orders assigned to a driver."""
    if not await _authenticate(api_key, business_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(
                Order.business_id == business_id,
                Order.driver_id == driver_id,
                Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.IN_TRANSIT]),
            )
        )
        orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "destination_address": o.destination_address,
            "status": o.status.value if hasattr(o.status, "value") else o.status,
            "weight": float(o.weight),
        }
        for o in orders
    ]


# ---------------------------------------------------------------------------
# Dashboard — KPI summary
# ---------------------------------------------------------------------------


@router.get("/api/businesses/{business_id}/dashboard")
async def get_dashboard(
    business_id: int,
    api_key: str = Query(...),
):
    if not await _authenticate(api_key, business_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    async with AsyncSessionLocal() as db:
        total_q = await db.execute(
            select(func.count(Driver.id)).where(
                Driver.business_id == business_id,
                Driver.is_active == True,
            )
        )
        total_drivers = total_q.scalar() or 0

        online_drivers = total_drivers  # All active drivers shown as online for now

        status_q = await db.execute(
            select(Order.status, func.count(Order.id)).where(
                Order.business_id == business_id,
            ).group_by(Order.status)
        )
        orders_by_status = {
            (row[0].value if hasattr(row[0], "value") else row[0]): row[1]
            for row in status_q
        }

        delivered_q = await db.execute(
            select(func.count(Order.id)).where(
                Order.business_id == business_id,
                Order.status == OrderStatus.DELIVERED,
            )
        )
        delivered_today = delivered_q.scalar() or 0

        recent_q = await db.execute(
            select(Order, Driver.name.label("driver_name")).outerjoin(
                Driver, Order.driver_id == Driver.id
            ).where(
                Order.business_id == business_id,
            ).order_by(Order.created_at.desc()).limit(8)
        )
        recent_rows = recent_q.all()

    recent_orders = [
        {
            "id": row.Order.id,
            "destination_address": row.Order.destination_address,
            "status": row.Order.status.value if hasattr(row.Order.status, "value") else row.Order.status,
            "weight": float(row.Order.weight),
            "driver_name": row.driver_name,
            "created_at": row.Order.created_at.isoformat() if row.Order.created_at else None,
        }
        for row in recent_rows
    ]

    return {
        "total_drivers": total_drivers,
        "online_drivers": online_drivers,
        "orders_by_status": orders_by_status,
        "delivered_today": delivered_today,
        "recent_orders": recent_orders,
    }


# ---------------------------------------------------------------------------
# Orders — full list
# ---------------------------------------------------------------------------


@router.get("/api/businesses/{business_id}/orders")
async def list_orders(
    business_id: int,
    api_key: str = Query(...),
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    if not await _authenticate(api_key, business_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    async with AsyncSessionLocal() as db:
        q = (
            select(Order, Driver.name.label("driver_name"))
            .outerjoin(Driver, Order.driver_id == Driver.id)
            .where(Order.business_id == business_id)
        )
        if status:
            try:
                q = q.where(Order.status == OrderStatus[status.upper()])
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        q = q.order_by(Order.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(q)
        rows = result.all()

    return [
        {
            "id": row.Order.id,
            "destination_address": row.Order.destination_address,
            "status": row.Order.status.value if hasattr(row.Order.status, "value") else row.Order.status,
            "weight": float(row.Order.weight),
            "driver_id": row.Order.driver_id,
            "driver_name": row.driver_name,
            "created_at": row.Order.created_at.isoformat() if row.Order.created_at else None,
            "updated_at": row.Order.updated_at.isoformat() if row.Order.updated_at else None,
        }
        for row in rows
    ]
