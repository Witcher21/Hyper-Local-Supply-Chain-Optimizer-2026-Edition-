"""
Inventory Router — CRUD endpoints for stock/inventory management.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from typing import Optional

from database import AsyncSessionLocal
from models import Business, InventoryItem

router = APIRouter(prefix="/api", tags=["Inventory"])


# ── Auth ──
async def _auth(api_key: str, business_id: int):
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
        raise HTTPException(status_code=403, detail="Forbidden")
    return biz


# ── Schemas ──
class InventoryItemResponse(BaseModel):
    id: int
    name: str
    sku: str
    category: str
    stock: int
    reorder_point: int
    unit: str
    unit_cost: float
    supplier: Optional[str] = None
    stock_status: str = ""
    value: float = 0

    model_config = {"from_attributes": True}


class InventoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=50)
    category: str = Field(..., min_length=1, max_length=100)
    stock: int = Field(0, ge=0)
    reorder_point: int = Field(0, ge=0)
    unit: str = Field(..., min_length=1, max_length=50)
    unit_cost: float = Field(..., gt=0)
    supplier: Optional[str] = None


class InventoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = None
    unit_cost: Optional[float] = Field(None, gt=0)
    supplier: Optional[str] = None


def _compute_status(stock: int, reorder_point: int) -> str:
    if stock == 0:
        return "Out of Stock"
    if stock <= reorder_point:
        return "Low Stock"
    if stock <= reorder_point * 1.5:
        return "Watch"
    return "In Stock"


def _enrich(item: InventoryItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "sku": item.sku,
        "category": item.category,
        "stock": item.stock,
        "reorder_point": item.reorder_point,
        "unit": item.unit,
        "unit_cost": float(item.unit_cost),
        "supplier": item.supplier,
        "stock_status": _compute_status(item.stock, item.reorder_point),
        "value": round(item.stock * float(item.unit_cost)),
    }


# ── Endpoints ──

@router.get("/businesses/{business_id}/inventory")
async def list_inventory(
    business_id: int,
    api_key: str = Query(...),
    category: Optional[str] = Query(None),
):
    await _auth(api_key, business_id)
    async with AsyncSessionLocal() as db:
        q = select(InventoryItem).where(InventoryItem.business_id == business_id)
        if category:
            q = q.where(InventoryItem.category == category)
        q = q.order_by(InventoryItem.name)
        result = await db.execute(q)
        items = result.scalars().all()
    return [_enrich(i) for i in items]


@router.post("/businesses/{business_id}/inventory", status_code=201)
async def create_inventory_item(
    business_id: int,
    body: InventoryCreateRequest,
    api_key: str = Query(...),
):
    await _auth(api_key, business_id)
    async with AsyncSessionLocal() as db:
        item = InventoryItem(
            business_id=business_id,
            name=body.name,
            sku=body.sku,
            category=body.category,
            stock=body.stock,
            reorder_point=body.reorder_point,
            unit=body.unit,
            unit_cost=body.unit_cost,
            supplier=body.supplier,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return _enrich(item)


@router.put("/businesses/{business_id}/inventory/{item_id}")
async def update_inventory_item(
    business_id: int,
    item_id: int,
    body: InventoryUpdateRequest,
    api_key: str = Query(...),
):
    await _auth(api_key, business_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.business_id == business_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if body.name is not None:
            item.name = body.name
        if body.sku is not None:
            item.sku = body.sku
        if body.category is not None:
            item.category = body.category
        if body.stock is not None:
            item.stock = body.stock
        if body.reorder_point is not None:
            item.reorder_point = body.reorder_point
        if body.unit is not None:
            item.unit = body.unit
        if body.unit_cost is not None:
            item.unit_cost = body.unit_cost
        if body.supplier is not None:
            item.supplier = body.supplier

        await db.commit()
        await db.refresh(item)
        return _enrich(item)


@router.delete("/businesses/{business_id}/inventory/{item_id}", status_code=200)
async def delete_inventory_item(
    business_id: int,
    item_id: int,
    api_key: str = Query(...),
):
    await _auth(api_key, business_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.business_id == business_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        await db.delete(item)
        await db.commit()
    return {"detail": f"Item {item_id} deleted"}
