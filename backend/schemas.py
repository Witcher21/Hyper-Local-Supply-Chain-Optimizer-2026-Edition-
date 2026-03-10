"""
Pydantic schemas for request validation and response serialization.
"""

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enumerations (mirror models.py, kept separate from SQLAlchemy enums)
# ---------------------------------------------------------------------------


class DriverStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    DELAYED = "DELAYED"
    REROUTING = "REROUTING"
    IDLE = "IDLE"


class WSClientType(str, enum.Enum):
    DRIVER = "driver"
    ADMIN = "admin"


# ---------------------------------------------------------------------------
# WebSocket message schemas
# ---------------------------------------------------------------------------


class LocationUpdate(BaseModel):
    """Incoming GPS payload from a driver client."""

    type: str = "location_update"
    driver_id: int = Field(..., gt=0)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    speed: Optional[float] = Field(None, ge=0, le=500)   # km/h
    heading: Optional[float] = Field(None, ge=0, le=360)  # degrees
    status: DriverStatus = DriverStatus.ON_TRACK

    @field_validator("type")
    @classmethod
    def must_be_location_update(cls, v: str) -> str:
        if v != "location_update":
            raise ValueError("type must be 'location_update'")
        return v


class FleetBroadcast(BaseModel):
    """Outgoing broadcast sent to all connected admin dashboards."""

    type: str = "fleet_update"
    driver_id: int
    lat: float
    lng: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    status: DriverStatus
    timestamp: datetime


class DriverDisconnectBroadcast(BaseModel):
    type: str = "driver_disconnected"
    driver_id: int
    timestamp: datetime


class ConnectionEstablishedPayload(BaseModel):
    type: str = "connection_established"
    client_type: WSClientType
    business_id: int
    active_driver_ids: list[int] = []


# ---------------------------------------------------------------------------
# REST API schemas — Responses
# ---------------------------------------------------------------------------


class DriverResponse(BaseModel):
    id: int
    name: str
    vehicle_type: str
    status: DriverStatus
    lat: Optional[float] = None
    lng: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    last_seen: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    destination_address: Optional[str] = None
    status: str
    weight: float
    driver_id: Optional[int] = None

    model_config = {"from_attributes": True}


class OrderFullResponse(BaseModel):
    id: int
    business_id: int
    driver_id: Optional[int] = None
    destination_address: Optional[str] = None
    status: str
    weight: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BusinessResponse(BaseModel):
    id: int
    name: str
    api_key: str
    subscription_tier: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# REST API schemas — Requests
# ---------------------------------------------------------------------------


class BusinessCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    subscription_tier: Optional[str] = Field("FREE", description="FREE | STARTER | PRO | ENTERPRISE")


class DriverCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    vehicle_type: str = Field(..., min_length=1, max_length=100, description="e.g. van, truck, bike")
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    status: Optional[str] = Field("IDLE", description="ON_TRACK | DELAYED | REROUTING | IDLE")


class DriverUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    vehicle_type: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, description="ON_TRACK | DELAYED | REROUTING | IDLE")
    is_active: Optional[bool] = None


class OrderCreateRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    destination_address: Optional[str] = Field(None, max_length=500)
    weight: float = Field(..., gt=0, description="Weight in kg")
    driver_id: Optional[int] = None
    status: Optional[str] = Field("PENDING", description="PENDING | ASSIGNED | IN_TRANSIT | DELIVERED | FAILED")


class OrderUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="PENDING | ASSIGNED | IN_TRANSIT | DELIVERED | FAILED")
    driver_id: Optional[int] = None
    destination_address: Optional[str] = Field(None, max_length=500)
    weight: Optional[float] = Field(None, gt=0)
