"""
CRUD Router — RESTful endpoints for Businesses, Drivers, and Orders.
====================================================================
All endpoints require `api_key` query-param for authentication.
"""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, update, func

from database import AsyncSessionLocal
from models import (
    Business,
    Driver,
    DriverStatus,
    Order,
    OrderStatus,
    SubscriptionTier,
)
from schemas import (
    BusinessCreateRequest,
    BusinessResponse,
    DriverCreateRequest,
    DriverUpdateRequest,
    DriverResponse,
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderFullResponse,
)

router = APIRouter(prefix="/api", tags=["CRUD"])


# ───────────────────────────────────────────────────────────────
# Auth helper
# ───────────────────────────────────────────────────────────────


async def _auth(api_key: str, business_id: int) -> Business:
    """Validate api_key belongs to the business; return Business or 403."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Business).where(
                Business.api_key == api_key,
                Business.id == business_id,
                Business.is_active == True,
            )
        )
        biz = result.scalar_one_or_none()
    if not biz:
        raise HTTPException(status_code=403, detail="Forbidden: invalid API key")
    return biz


# ═══════════════════════════════════════════════════════════════
# BUSINESS
# ═══════════════════════════════════════════════════════════════


@router.post("/businesses", response_model=BusinessResponse, status_code=201)
async def create_business(body: BusinessCreateRequest):
    """Create a new business tenant and generate an API key."""
    api_key = secrets.token_urlsafe(32)
    async with AsyncSessionLocal() as db:
        biz = Business(
            name=body.name,
            api_key=api_key,
            subscription_tier=SubscriptionTier[body.subscription_tier.upper()]
            if body.subscription_tier
            else SubscriptionTier.FREE,
        )
        db.add(biz)
        await db.commit()
        await db.refresh(biz)
        return BusinessResponse(
            id=biz.id,
            name=biz.name,
            api_key=biz.api_key,
            subscription_tier=biz.subscription_tier.value,
            is_active=biz.is_active,
            created_at=biz.created_at,
        )


@router.get("/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(business_id: int, api_key: str = Query(...)):
    """Retrieve details of a single business."""
    biz = await _auth(api_key, business_id)
    return BusinessResponse(
        id=biz.id,
        name=biz.name,
        api_key=biz.api_key,
        subscription_tier=biz.subscription_tier.value,
        is_active=biz.is_active,
        created_at=biz.created_at,
    )


# ═══════════════════════════════════════════════════════════════
# DRIVERS
# ═══════════════════════════════════════════════════════════════


@router.post(
    "/businesses/{business_id}/drivers",
    response_model=DriverResponse,
    status_code=201,
)
async def create_driver(
    business_id: int,
    body: DriverCreateRequest,
    api_key: str = Query(...),
):
    """Add a new driver to a business fleet."""
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        drv = Driver(
            business_id=business_id,
            name=body.name,
            vehicle_type=body.vehicle_type,
            lat=body.lat,
            lng=body.lng,
            status=DriverStatus[body.status.upper()] if body.status else DriverStatus.IDLE,
            is_active=True,
        )
        db.add(drv)
        await db.commit()
        await db.refresh(drv)

        return DriverResponse(
            id=drv.id,
            name=drv.name,
            vehicle_type=drv.vehicle_type,
            status=drv.status,
            lat=drv.lat,
            lng=drv.lng,
            speed=float(drv.speed) if drv.speed else None,
            heading=float(drv.heading) if drv.heading else None,
            last_seen=drv.last_seen,
            is_active=drv.is_active,
        )


@router.put(
    "/businesses/{business_id}/drivers/{driver_id}",
    response_model=DriverResponse,
)
async def update_driver(
    business_id: int,
    driver_id: int,
    body: DriverUpdateRequest,
    api_key: str = Query(...),
):
    """Update driver details (name, vehicle type, status)."""
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Driver).where(
                Driver.id == driver_id, Driver.business_id == business_id
            )
        )
        drv = result.scalar_one_or_none()
        if not drv:
            raise HTTPException(status_code=404, detail="Driver not found")

        if body.name is not None:
            drv.name = body.name
        if body.vehicle_type is not None:
            drv.vehicle_type = body.vehicle_type
        if body.status is not None:
            drv.status = DriverStatus[body.status.upper()]
        if body.is_active is not None:
            drv.is_active = body.is_active

        await db.commit()
        await db.refresh(drv)

        return DriverResponse(
            id=drv.id,
            name=drv.name,
            vehicle_type=drv.vehicle_type,
            status=drv.status,
            lat=drv.lat,
            lng=drv.lng,
            speed=float(drv.speed) if drv.speed else None,
            heading=float(drv.heading) if drv.heading else None,
            last_seen=drv.last_seen,
            is_active=drv.is_active,
        )


@router.delete("/businesses/{business_id}/drivers/{driver_id}", status_code=200)
async def delete_driver(
    business_id: int,
    driver_id: int,
    api_key: str = Query(...),
):
    """Soft-delete a driver (sets is_active=false)."""
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Driver).where(
                Driver.id == driver_id, Driver.business_id == business_id
            )
        )
        drv = result.scalar_one_or_none()
        if not drv:
            raise HTTPException(status_code=404, detail="Driver not found")
        drv.is_active = False
        await db.commit()

    return {"detail": f"Driver {driver_id} deactivated"}


# ═══════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════


@router.post(
    "/businesses/{business_id}/orders",
    response_model=OrderFullResponse,
    status_code=201,
)
async def create_order(
    business_id: int,
    body: OrderCreateRequest,
    api_key: str = Query(...),
):
    """Create a new delivery order."""
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        order = Order(
            business_id=business_id,
            driver_id=body.driver_id,
            destination_lat=body.lat,
            destination_lng=body.lng,
            destination_address=body.destination_address,
            status=OrderStatus[body.status.upper()] if body.status else OrderStatus.PENDING,
            weight=body.weight,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        return OrderFullResponse(
            id=order.id,
            business_id=order.business_id,
            driver_id=order.driver_id,
            destination_address=order.destination_address,
            status=order.status.value if hasattr(order.status, "value") else order.status,
            weight=float(order.weight),
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


@router.put(
    "/businesses/{business_id}/orders/{order_id}",
    response_model=OrderFullResponse,
)
async def update_order(
    business_id: int,
    order_id: int,
    body: OrderUpdateRequest,
    api_key: str = Query(...),
):
    """Update order status, driver assignment, etc."""
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(
                Order.id == order_id, Order.business_id == business_id
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if body.status is not None:
            order.status = OrderStatus[body.status.upper()]
        if body.driver_id is not None:
            order.driver_id = body.driver_id
        if body.destination_address is not None:
            order.destination_address = body.destination_address
        if body.weight is not None:
            order.weight = body.weight

        order.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(order)

        return OrderFullResponse(
            id=order.id,
            business_id=order.business_id,
            driver_id=order.driver_id,
            destination_address=order.destination_address,
            status=order.status.value if hasattr(order.status, "value") else order.status,
            weight=float(order.weight),
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


@router.delete("/businesses/{business_id}/orders/{order_id}", status_code=200)
async def delete_order(
    business_id: int,
    order_id: int,
    api_key: str = Query(...),
):
    """Cancel/delete an order (sets status to FAILED)."""
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(
                Order.id == order_id, Order.business_id == business_id
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.status = OrderStatus.FAILED
        order.updated_at = datetime.now(timezone.utc)
        await db.commit()

    return {"detail": f"Order {order_id} cancelled"}
