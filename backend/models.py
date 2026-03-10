"""
SQLAlchemy ORM models — SQLite compatible (no PostGIS dependency).
Lat/Lng stored as plain Float columns instead of PostGIS geometry.
"""

import enum
import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ---------------------------------------------------------------------------
# JSON column type that works on both SQLite and PostgreSQL
# ---------------------------------------------------------------------------

from sqlalchemy.types import TypeDecorator


class JSONType(TypeDecorator):
    """Platform-agnostic JSON column: uses TEXT with JSON serialization on SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SubscriptionTier(str, enum.Enum):
    FREE = "FREE"
    STARTER = "STARTER"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class DriverStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    DELAYED = "DELAYED"
    REROUTING = "REROUTING"
    IDLE = "IDLE"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class RouteStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    SUSPENDED = "SUSPENDED"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Business(Base):
    """A tenant business that owns drivers and orders."""

    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(SubscriptionTier, name="subscription_tier"),
        default=SubscriptionTier.FREE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    drivers: Mapped[list["Driver"]] = relationship("Driver", back_populates="business", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="business", cascade="all, delete-orphan")


class Driver(Base):
    """A delivery driver with lat/lng coordinates."""

    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Simple float columns instead of PostGIS geometry
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    speed: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    heading: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[DriverStatus] = mapped_column(
        SAEnum(DriverStatus, name="driver_status"),
        default=DriverStatus.IDLE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    business: Mapped["Business"] = relationship("Business", back_populates="drivers")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="driver")
    route_sessions: Mapped[list["RouteSession"]] = relationship("RouteSession", back_populates="driver")


class Order(Base):
    """A delivery order with destination coordinates."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)

    # Simple float columns instead of PostGIS geometry
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    destination_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    notes: Mapped[dict] = mapped_column(JSONType, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    business: Mapped["Business"] = relationship("Business", back_populates="orders")
    driver: Mapped["Driver | None"] = relationship("Driver", back_populates="orders")


class RouteSession(Base):
    """A live routing session with waypoints."""

    __tablename__ = "route_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Store path as JSON array of [lng, lat] pairs instead of PostGIS LINESTRING
    active_path: Mapped[list] = mapped_column(JSONType, default=list)
    waypoints: Mapped[list] = mapped_column(JSONType, default=list)

    status: Mapped[RouteStatus] = mapped_column(
        SAEnum(RouteStatus, name="route_status"),
        default=RouteStatus.ACTIVE,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    driver: Mapped["Driver"] = relationship("Driver", back_populates="route_sessions")


class InventoryItem(Base):
    """A stock/inventory item tracked by the business."""

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    supplier: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    business: Mapped["Business"] = relationship("Business")


class BusinessSettings(Base):
    """Persisted settings for a business (profile, alerts, AI config)."""

    __tablename__ = "business_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    settings_data: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    business: Mapped["Business"] = relationship("Business")
