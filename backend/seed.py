"""
Seed Script — Populate the database with initial data.
Run:  python seed.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Ensure local imports work when running as standalone script
sys.path.insert(0, os.path.dirname(__file__))

from database import AsyncSessionLocal, engine, Base  # noqa: E402
from models import (  # noqa: E402
    Business,
    BusinessSettings,
    Driver,
    DriverStatus,
    InventoryItem,
    Order,
    OrderStatus,
    RouteSession,
    RouteStatus,
    SubscriptionTier,
)
from sqlalchemy import select  # noqa: E402


# ───────────────────────────────────────────────────────────────
# Seed data — Colombo, Sri Lanka
# ───────────────────────────────────────────────────────────────

DEMO_BUSINESS = {
    "name": "Demo Distributor",
    "api_key": "demo-key",
    "subscription_tier": SubscriptionTier.PRO,
    "is_active": True,
}

DEMO_DRIVERS = [
    {"name": "Kasun Perera",          "vehicle_type": "van",   "lat": 6.9271, "lng": 79.8612, "status": DriverStatus.ON_TRACK,  "speed": 42, "heading": 90},
    {"name": "Nimal Silva",           "vehicle_type": "truck", "lat": 6.9150, "lng": 79.8480, "status": DriverStatus.ON_TRACK,  "speed": 38, "heading": 180},
    {"name": "Chaminda Jayawardena",  "vehicle_type": "bike",  "lat": 6.9350, "lng": 79.8750, "status": DriverStatus.DELAYED,   "speed": 12, "heading": 270},
    {"name": "Ruwan Fernando",        "vehicle_type": "van",   "lat": 6.9050, "lng": 79.8900, "status": DriverStatus.ON_TRACK,  "speed": 55, "heading": 45},
    {"name": "Dinesh Kumara",         "vehicle_type": "truck", "lat": 6.9400, "lng": 79.8400, "status": DriverStatus.REROUTING, "speed": 28, "heading": 135},
    {"name": "Suresh Bandara",        "vehicle_type": "van",   "lat": 6.9180, "lng": 79.8700, "status": DriverStatus.ON_TRACK,  "speed": 47, "heading": 0},
    {"name": "Priyantha Wijesinghe",  "vehicle_type": "bike",  "lat": 6.9300, "lng": 79.8550, "status": DriverStatus.ON_TRACK,  "speed": 33, "heading": 225},
    {"name": "Amal Dissanayake",      "vehicle_type": "truck", "lat": 6.9220, "lng": 79.8350, "status": DriverStatus.IDLE,      "speed": 0,  "heading": 0},
]

DEMO_ORDERS = [
    {"driver_idx": 0, "lat": 6.9120, "lng": 79.8550, "address": "42 Galle Road, Colombo 03",       "status": OrderStatus.IN_TRANSIT, "weight": 24.5},
    {"driver_idx": 0, "lat": 6.8950, "lng": 79.8560, "address": "15 Marine Drive, Colombo 04",     "status": OrderStatus.ASSIGNED,   "weight": 8.2},
    {"driver_idx": 1, "lat": 6.8980, "lng": 79.8720, "address": "78 Havelock Road, Colombo 05",    "status": OrderStatus.IN_TRANSIT, "weight": 45.0},
    {"driver_idx": 1, "lat": 6.9100, "lng": 79.8530, "address": "23 Duplication Road, Colombo 03", "status": OrderStatus.ASSIGNED,   "weight": 12.3},
    {"driver_idx": 2, "lat": 6.9170, "lng": 79.8460, "address": "5 Park Street, Colombo 02",       "status": OrderStatus.IN_TRANSIT, "weight": 3.7},
    {"driver_idx": 3, "lat": 6.9320, "lng": 79.8830, "address": "90 Baseline Road, Colombo 09",    "status": OrderStatus.IN_TRANSIT, "weight": 18.9},
    {"driver_idx": 3, "lat": 6.9250, "lng": 79.8510, "address": "12 Beira Lake Rd, Colombo 02",    "status": OrderStatus.ASSIGNED,   "weight": 7.5},
    {"driver_idx": 4, "lat": 6.9195, "lng": 79.8485, "address": "65 Union Place, Colombo 02",      "status": OrderStatus.IN_TRANSIT, "weight": 55.0},
    {"driver_idx": 5, "lat": 6.9080, "lng": 79.8630, "address": "33 Ward Place, Colombo 07",       "status": OrderStatus.IN_TRANSIT, "weight": 22.1},
    {"driver_idx": 5, "lat": 6.9060, "lng": 79.8680, "address": "8 Gregory's Road, Colombo 07",    "status": OrderStatus.ASSIGNED,   "weight": 14.6},
    {"driver_idx": 6, "lat": 6.9110, "lng": 79.8650, "address": "17 Flower Road, Colombo 07",      "status": OrderStatus.IN_TRANSIT, "weight": 5.2},
    {"driver_idx": 6, "lat": 6.9000, "lng": 79.8790, "address": "45 Torrington Ave, Colombo 07",   "status": OrderStatus.ASSIGNED,   "weight": 2.8},
]

INVENTORY = [
    {"name": "Basmati Rice 5kg",    "sku": "GR-001", "category": "Grains",     "stock": 180, "reorder": 50,  "unit": "bags",    "cost": 850,  "supplier": "Lanka Rice Mills"},
    {"name": "Red Lentils 1kg",     "sku": "LG-001", "category": "Legumes",    "stock": 120, "reorder": 40,  "unit": "packs",   "cost": 320,  "supplier": "Eastern Traders"},
    {"name": "Coconut Oil 1L",      "sku": "OL-001", "category": "Oils",       "stock": 75,  "reorder": 30,  "unit": "bottles", "cost": 480,  "supplier": "CoCo Products"},
    {"name": "Canned Tuna 185g",    "sku": "CN-001", "category": "Canned",     "stock": 200, "reorder": 60,  "unit": "cans",    "cost": 220,  "supplier": "Seafood Lanka"},
    {"name": "Full Cream Milk 1L",  "sku": "DY-001", "category": "Dairy",      "stock": 45,  "reorder": 40,  "unit": "cartons", "cost": 390,  "supplier": "Milco Pvt Ltd"},
    {"name": "Chickpeas 500g",      "sku": "LG-002", "category": "Legumes",    "stock": 90,  "reorder": 30,  "unit": "packs",   "cost": 260,  "supplier": "Eastern Traders"},
    {"name": "Sunflower Oil 2L",    "sku": "OL-002", "category": "Oils",       "stock": 25,  "reorder": 25,  "unit": "bottles", "cost": 920,  "supplier": "Global Oils"},
    {"name": "Tomato Paste 400g",   "sku": "CD-001", "category": "Condiments", "stock": 110, "reorder": 35,  "unit": "cans",    "cost": 180,  "supplier": "Fresh Foods Co"},
    {"name": "Turmeric Powder 100g","sku": "SP-001", "category": "Spices",     "stock": 65,  "reorder": 20,  "unit": "packs",   "cost": 150,  "supplier": "Spice Island"},
    {"name": "Cinnamon Sticks 50g", "sku": "SP-002", "category": "Spices",     "stock": 40,  "reorder": 15,  "unit": "packs",   "cost": 280,  "supplier": "Spice Island"},
    {"name": "Black Tea 200g",      "sku": "BV-001", "category": "Beverages",  "stock": 95,  "reorder": 30,  "unit": "boxes",   "cost": 340,  "supplier": "Ceylon Tea Estates"},
    {"name": "Sugar 1kg",           "sku": "GR-002", "category": "Grains",     "stock": 150, "reorder": 50,  "unit": "packs",   "cost": 190,  "supplier": "Lanka Sugar"},
    {"name": "Sardines 155g",       "sku": "CN-002", "category": "Canned",     "stock": 8,   "reorder": 40,  "unit": "cans",    "cost": 160,  "supplier": "Seafood Lanka"},
    {"name": "Dish Soap 500ml",     "sku": "HH-001", "category": "Household",  "stock": 60,  "reorder": 20,  "unit": "bottles", "cost": 210,  "supplier": "Clean Home Ltd"},
    {"name": "Soy Sauce 250ml",     "sku": "CD-002", "category": "Condiments", "stock": 55,  "reorder": 20,  "unit": "bottles", "cost": 120,  "supplier": "Orient Foods"},
    {"name": "Wheat Flour 1kg",     "sku": "GR-003", "category": "Grains",     "stock": 0,   "reorder": 30,  "unit": "bags",    "cost": 165,  "supplier": "Lanka Mills"},
    {"name": "Butter 250g",         "sku": "DY-002", "category": "Dairy",      "stock": 30,  "reorder": 15,  "unit": "packs",   "cost": 520,  "supplier": "Milco Pvt Ltd"},
    {"name": "Olive Oil 500ml",     "sku": "OL-003", "category": "Oils",       "stock": 18,  "reorder": 10,  "unit": "bottles", "cost": 1250, "supplier": "Global Oils"},
    {"name": "Chili Powder 100g",   "sku": "SP-003", "category": "Spices",     "stock": 70,  "reorder": 25,  "unit": "packs",   "cost": 140,  "supplier": "Spice Island"},
    {"name": "Baked Beans 400g",    "sku": "CN-003", "category": "Canned",     "stock": 85,  "reorder": 30,  "unit": "cans",    "cost": 195,  "supplier": "Fresh Foods Co"},
]


async def seed():
    """Insert business, drivers, orders, inventory, and settings."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # --- Business ---
        result = await db.execute(
            select(Business).where(Business.api_key == DEMO_BUSINESS["api_key"])
        )
        biz = result.scalar_one_or_none()
        if not biz:
            biz = Business(**DEMO_BUSINESS)
            db.add(biz)
            await db.flush()
            print(f"✓ Created business: {biz.name} (id={biz.id})")
        else:
            print(f"· Business already exists: {biz.name} (id={biz.id})")

        business_id = biz.id

        # --- Drivers ---
        result = await db.execute(
            select(Driver).where(Driver.business_id == business_id)
        )
        existing_drivers = result.scalars().all()

        if existing_drivers:
            print(f"· {len(existing_drivers)} drivers already exist — skipping")
            driver_ids = [d.id for d in existing_drivers]
        else:
            driver_ids = []
            for dd in DEMO_DRIVERS:
                drv = Driver(
                    business_id=business_id,
                    name=dd["name"],
                    vehicle_type=dd["vehicle_type"],
                    lat=dd["lat"],
                    lng=dd["lng"],
                    speed=dd["speed"],
                    heading=dd["heading"],
                    status=dd["status"],
                    is_active=True,
                )
                db.add(drv)
                await db.flush()
                driver_ids.append(drv.id)
                print(f"  ✓ Driver: {drv.name} (id={drv.id})")

        # --- Orders ---
        result = await db.execute(
            select(Order).where(Order.business_id == business_id)
        )
        existing_orders = result.scalars().all()

        if existing_orders:
            print(f"· {len(existing_orders)} orders already exist — skipping")
        else:
            for od in DEMO_ORDERS:
                driver_id = driver_ids[od["driver_idx"]] if od["driver_idx"] < len(driver_ids) else None
                order = Order(
                    business_id=business_id,
                    driver_id=driver_id,
                    destination_lat=od["lat"],
                    destination_lng=od["lng"],
                    destination_address=od["address"],
                    status=od["status"],
                    weight=od["weight"],
                )
                db.add(order)
                await db.flush()
                print(f"  ✓ Order #{order.id}: {od['address'][:40]}")

        # --- Route Sessions ---
        if len(driver_ids) >= 2:
            result = await db.execute(
                select(RouteSession).where(
                    RouteSession.driver_id.in_(driver_ids[:2])
                )
            )
            existing_routes = result.scalars().all()

            if existing_routes:
                print("· Route sessions already exist — skipping")
            else:
                rs1 = RouteSession(
                    driver_id=driver_ids[0],
                    active_path=[[79.8612, 6.9271], [79.8580, 6.9200], [79.8555, 6.9120], [79.8550, 6.9050], [79.8560, 6.8950]],
                    waypoints=[
                        {"lat": 6.9120, "lng": 79.8550, "order_id": 1, "eta": "10 min"},
                        {"lat": 6.8950, "lng": 79.8560, "order_id": 2, "eta": "22 min"},
                    ],
                    status=RouteStatus.ACTIVE,
                )
                db.add(rs1)

                rs2 = RouteSession(
                    driver_id=driver_ids[1],
                    active_path=[[79.8480, 6.9150], [79.8550, 6.9100], [79.8650, 6.9020], [79.8720, 6.8980]],
                    waypoints=[
                        {"lat": 6.8980, "lng": 79.8720, "order_id": 3, "eta": "15 min"},
                        {"lat": 6.9100, "lng": 79.8530, "order_id": 4, "eta": "28 min"},
                    ],
                    status=RouteStatus.ACTIVE,
                )
                db.add(rs2)
                print("  ✓ Created 2 route sessions")

        await db.commit()

        # --- Inventory ---
        result = await db.execute(
            select(InventoryItem).where(InventoryItem.business_id == business_id)
        )
        existing_inv = result.scalars().all()

        if existing_inv:
            print(f"· {len(existing_inv)} inventory items exist — skipping")
        else:
            for inv in INVENTORY:
                item = InventoryItem(
                    business_id=business_id,
                    name=inv["name"],
                    sku=inv["sku"],
                    category=inv["category"],
                    stock=inv["stock"],
                    reorder_point=inv["reorder"],
                    unit=inv["unit"],
                    unit_cost=inv["cost"],
                    supplier=inv["supplier"],
                )
                db.add(item)
            await db.flush()
            print(f"  ✓ Created {len(INVENTORY)} inventory items")

        # --- Business Settings ---
        result = await db.execute(
            select(BusinessSettings).where(BusinessSettings.business_id == business_id)
        )
        existing_settings = result.scalar_one_or_none()

        if existing_settings:
            print("· Settings already exist — skipping")
        else:
            settings = BusinessSettings(
                business_id=business_id,
                settings_data={
                    "profile": {"name": "Demo Distributor", "address": "123 Galle Face, Colombo 03", "email": "ops@demodistributor.lk", "phone": "+94 11 234 5678", "tier": "PRO"},
                    "alerts": {"delayThreshold": 15, "speedLimit": 80, "lowStock": True, "driverOffline": True, "orderFailed": True, "dailyReport": False},
                    "ai": {"optimizeInterval": "10 minutes", "trafficSource": "Mapbox Traffic", "model": "GPT-4o (Recommended)", "autonomousRerouting": False},
                },
            )
            db.add(settings)
            print("  ✓ Created default settings")

        await db.commit()

    print("\n🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
