"""
GPS Driver Simulator — WebSocket Client
========================================
Connects as 8 simulated drivers and streams realistic GPS location
updates to the backend, allowing the admin Live Map to show moving
vehicles without needing the Flutter mobile app.

Run:  python simulate_driver.py
"""

import asyncio
import json
import math
import os
import random
import sys
from datetime import datetime, timezone

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

# ───────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────

WS_HOST = os.getenv("WS_HOST", "localhost:8000")
BUSINESS_ID = int(os.getenv("BUSINESS_ID", "1"))
API_KEY = os.getenv("API_KEY", "demo-key")
TICK_INTERVAL = 1.2  # seconds between GPS updates

# Driver seed data — Colombo, Sri Lanka
DRIVERS = [
    {"id": 1, "lat": 6.9271, "lng": 79.8612, "speed": 42, "heading": 90,  "status": "ON_TRACK"},
    {"id": 2, "lat": 6.9150, "lng": 79.8480, "speed": 38, "heading": 180, "status": "ON_TRACK"},
    {"id": 3, "lat": 6.9350, "lng": 79.8750, "speed": 12, "heading": 270, "status": "DELAYED"},
    {"id": 4, "lat": 6.9050, "lng": 79.8900, "speed": 55, "heading": 45,  "status": "ON_TRACK"},
    {"id": 5, "lat": 6.9400, "lng": 79.8400, "speed": 28, "heading": 135, "status": "REROUTING"},
    {"id": 6, "lat": 6.9180, "lng": 79.8700, "speed": 47, "heading": 0,   "status": "ON_TRACK"},
    {"id": 7, "lat": 6.9300, "lng": 79.8550, "speed": 33, "heading": 225, "status": "ON_TRACK"},
    {"id": 8, "lat": 6.9220, "lng": 79.8350, "speed": 0,  "heading": 0,   "status": "IDLE"},
]

STATUSES = ["ON_TRACK", "ON_TRACK", "ON_TRACK", "ON_TRACK", "DELAYED", "REROUTING"]

# Colombo bounding box
LAT_MIN, LAT_MAX = 6.88, 6.97
LNG_MIN, LNG_MAX = 79.82, 79.92


def tick_driver(d: dict) -> None:
    """Advance a single driver's position by one tick."""
    if d["status"] == "IDLE":
        if random.random() < 0.05:
            d["status"] = "ON_TRACK"
            d["speed"] = 20 + random.random() * 30
        return

    # Speed jitter
    d["speed"] = max(0, d["speed"] + (random.random() - 0.5) * 8)
    d["speed"] = round(d["speed"], 1)

    # Heading drift
    d["heading"] = (d["heading"] + (random.random() - 0.5) * 30 + 360) % 360
    d["heading"] = round(d["heading"], 1)

    # Move
    rad = math.radians(d["heading"])
    dist = (d["speed"] / 40) * 0.00012
    d["lat"] += math.cos(rad) * dist
    d["lng"] += math.sin(rad) * dist

    # Bounce off Colombo boundaries
    if d["lat"] < LAT_MIN or d["lat"] > LAT_MAX:
        d["heading"] = (180 - d["heading"] + 360) % 360
    if d["lng"] < LNG_MIN or d["lng"] > LNG_MAX:
        d["heading"] = (360 - d["heading"]) % 360
    d["lat"] = max(LAT_MIN, min(LAT_MAX, d["lat"]))
    d["lng"] = max(LNG_MIN, min(LNG_MAX, d["lng"]))

    # Occasional status change
    if random.random() < 0.008:
        d["status"] = random.choice(STATUSES)


async def simulate_single_driver(driver: dict):
    """Connect one simulated driver and loop GPS updates."""
    driver_id = driver["id"]
    url = (
        f"ws://{WS_HOST}/ws/tracking/{BUSINESS_ID}"
        f"?api_key={API_KEY}&client_type=driver&driver_id={driver_id}"
    )

    while True:
        try:
            async with websockets.connect(url) as ws:
                # Wait for connection_established
                resp = await ws.recv()
                data = json.loads(resp)
                if data.get("type") == "connection_established":
                    print(f"  ✓ Driver {driver_id} connected")

                while True:
                    tick_driver(driver)

                    payload = {
                        "type": "location_update",
                        "driver_id": driver_id,
                        "lat": round(driver["lat"], 6),
                        "lng": round(driver["lng"], 6),
                        "speed": driver["speed"],
                        "heading": driver["heading"],
                        "status": driver["status"],
                    }

                    await ws.send(json.dumps(payload))

                    # Read ACK (non-blocking timeout)
                    try:
                        ack = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        ack_data = json.loads(ack)
                        if ack_data.get("type") == "ack":
                            ts = ack_data.get("timestamp", "")
                            print(
                                f"  Driver {driver_id}: "
                                f"({driver['lat']:.4f}, {driver['lng']:.4f}) "
                                f"@ {driver['speed']} km/h — ACK {ts[-8:]}"
                            )
                    except asyncio.TimeoutError:
                        pass

                    await asyncio.sleep(TICK_INTERVAL)

        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"  ✗ Driver {driver_id} disconnected ({e}), retrying in 5s…")
            await asyncio.sleep(5)


async def main():
    print("═" * 60)
    print("  GPS Driver Simulator — Hyper-Local Supply Chain Optimizer")
    print(f"  Target: ws://{WS_HOST}/ws/tracking/{BUSINESS_ID}")
    print(f"  Drivers: {len(DRIVERS)}")
    print("═" * 60)
    print()

    tasks = [simulate_single_driver(dict(d)) for d in DRIVERS]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹ Simulation stopped.")
