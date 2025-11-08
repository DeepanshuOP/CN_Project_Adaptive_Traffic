import socket
import json
import time
import argparse
import requests
import os

# === DEFAULT SETTINGS ===
DEFAULT_HOST = "127.0.0.1"   # UDP destination (simulation listener)
DEFAULT_PORT = 5051          # Must match network_listener.py
FLASK_URL = "http://127.0.0.1:5055/counts"  # Simulation’s live data API
SLEEP_INTERVAL = 2.0         # Seconds between updates
MAX_ZERO_COUNT = 5           # Exit if all zero readings 5 times in a row

zero_streak = 0  # Track consecutive zero readings


def fetch_vehicle_counts():
    """Fetch live vehicle counts and running flag from Flask API."""
    try:
        response = requests.get(FLASK_URL, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            if not data.get("running", True):
                print("🛑 Simulation stopped — shutting down sensor node.")
                os._exit(0)
            return data.get("counts", {})
        else:
            print(f"⚠️ API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to fetch counts: {e}")
    return {"right": 0, "down": 0, "left": 0, "up": 0}


def send_vehicle_data(junction_id, host, port, interval):
    """Send the count for the given junction (1–4) over UDP to the simulation listener."""
    global zero_streak

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    directions = ["right", "down", "left", "up"]
    print(f"🚦 Sensor Node started for Junction {junction_id} → {(host, port)}")

    while True:
        counts = fetch_vehicle_counts()
        direction = directions[junction_id - 1] if 1 <= junction_id <= 4 else "right"
        vehicles_detected = counts.get(direction, 0)

        # Count all directions; if all are zero, increment zero_streak
        if all(v == 0 for v in counts.values()):
            zero_streak += 1
            print(f"⚠️ Zero data detected ({zero_streak}/{MAX_ZERO_COUNT})")
        else:
            zero_streak = 0

        # If 5 consecutive zero readings, shut down
        if zero_streak >= MAX_ZERO_COUNT:
            print("🛑 No activity detected — simulation likely closed. Exiting sensor node.")
            os._exit(0)

        payload = {
            "junction_id": junction_id,
            "vehicles_detected": vehicles_detected,
            "timestamp": time.time()
        }

        try:
            sock.sendto(json.dumps(payload).encode(), (host, port))
            print(f"📡 Sent from Junction {junction_id} ({direction.upper()}): {vehicles_detected} vehicles")
        except Exception as e:
            print(f"⚠️ Send failed: {e}")

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="IoT Sensor Node - Flask-integrated version with auto shutdown")
    parser.add_argument("--junction", type=int, default=1, help="Junction ID (1–4)")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host IP where simulation.py is listening")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP port to send data")
    parser.add_argument("--interval", type=float, default=SLEEP_INTERVAL, help="Seconds between updates")
    args = parser.parse_args()

    send_vehicle_data(args.junction, args.host, args.port, args.interval)

if __name__ == "__main__":
    main()
