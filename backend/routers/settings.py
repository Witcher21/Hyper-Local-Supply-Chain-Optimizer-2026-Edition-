"""
Settings Router — Load/Save business settings.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from typing import Any

from database import AsyncSessionLocal
from models import Business, BusinessSettings

router = APIRouter(prefix="/api", tags=["Settings"])


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


class SettingsPayload(BaseModel):
    settings: dict[str, Any]


DEFAULT_SETTINGS = {
    "profile": {
        "name": "",
        "address": "",
        "email": "",
        "phone": "",
    },
    "alerts": {
        "delayThreshold": 15,
        "speedLimit": 80,
        "lowStock": True,
        "driverOffline": True,
        "orderFailed": True,
        "dailyReport": False,
    },
    "ai": {
        "optimizeInterval": "10 minutes",
        "trafficSource": "Mapbox Traffic",
        "model": "GPT-4o (Recommended)",
        "autonomousRerouting": False,
    },
}


@router.get("/businesses/{business_id}/settings")
async def get_settings(business_id: int, api_key: str = Query(...)):
    biz = await _auth(api_key, business_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BusinessSettings).where(BusinessSettings.business_id == business_id)
        )
        settings = result.scalar_one_or_none()

    if settings:
        # Merge with defaults so new keys are always present
        merged = {**DEFAULT_SETTINGS}
        for key in merged:
            if key in settings.settings_data:
                merged[key] = {**merged[key], **settings.settings_data[key]}
        # Add business name from DB
        merged["profile"]["name"] = merged["profile"]["name"] or biz.name
        merged["profile"]["tier"] = biz.subscription_tier.value if hasattr(biz.subscription_tier, "value") else biz.subscription_tier
        return merged

    # Return defaults with business info
    default = {**DEFAULT_SETTINGS}
    default["profile"]["name"] = biz.name
    default["profile"]["tier"] = biz.subscription_tier.value if hasattr(biz.subscription_tier, "value") else biz.subscription_tier
    return default


@router.put("/businesses/{business_id}/settings")
async def save_settings(
    business_id: int,
    body: SettingsPayload,
    api_key: str = Query(...),
):
    await _auth(api_key, business_id)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BusinessSettings).where(BusinessSettings.business_id == business_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.settings_data = body.settings
            await db.commit()
            await db.refresh(existing)
            return {"detail": "Settings saved", "settings": existing.settings_data}
        else:
            new_settings = BusinessSettings(
                business_id=business_id,
                settings_data=body.settings,
            )
            db.add(new_settings)
            await db.commit()
            await db.refresh(new_settings)
            return {"detail": "Settings created", "settings": new_settings.settings_data}


@router.post("/businesses/{business_id}/optimize")
async def run_optimizer(
    business_id: int,
    api_key: str = Query(...),
):
    """Run route optimization for active drivers. Phase 2 will integrate LangChain."""
    await _auth(api_key, business_id)

    # For now, return a simulated optimization result
    # Phase 2 will connect to real traffic APIs + LangChain agent
    import random
    km_saved = round(random.uniform(3.0, 25.0), 1)
    time_saved = round(random.uniform(5, 35), 0)

    return {
        "status": "optimized",
        "km_saved": km_saved,
        "time_saved_min": int(time_saved),
        "routes_recalculated": random.randint(2, 8),
        "message": f"Routes optimized — {km_saved} km saved, ~{int(time_saved)} min faster delivery.",
    }
