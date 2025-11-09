import socket
import json
import time
import argparse
import requests
import threading
import random
import os
import logging

# === LOGGING CONFIGURATION ===
LOG_FILE = "sensor_ack_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.info("🚀 Sensor Node started with Sliding Window + Logging")

# === DEFAULT SETTINGS ===
DEFAULT_HOST = "127.0.0.1"   # UDP destination (simulation listener)
DEFAULT_PORT = 5051          # Must match network_listener.py
FLASK_URL = "http://127.0.0.1:5055/counts"  # Simulation’s live data API
SLEEP_INTERVAL = 2.0         # Seconds between updates
MAX_ZERO_COUNT = 5           # Exit if all zero readings 5 times in a row

# === SLIDING WINDOW SETTINGS ===
WINDOW_SIZE = 4              # number of unacknowledged packets allowed
ACK_TIMEOUT = 2.0            # seconds before retransmission
MAX_RETRIES = 3              # maximum retransmission attempts per packet
PACKET_LOSS_PROB = 0.1       # 20% simulated packet loss

zero_streak = 0  # Track consecutive zero readings


# === FETCH LIVE VEHICLE DATA FROM FLASK ===
def fetch_vehicle_counts():
    """Fetch live vehicle counts and running flag from Flask API."""
    try:
        response = requests.get(FLASK_URL, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            if not data.get("running", True):
                print("🛑 Simulation stopped — shutting down sensor node.")
                logging.info("🛑 Simulation stopped — shutting down sensor node.")
                os._exit(0)
            return data.get("counts", {})
        else:
            print(f"⚠️ API returned status {response.status_code}")
            logging.warning(f"API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to fetch counts: {e}")
        logging.error(f"Failed to fetch counts: {e}")
    return {"right": 0, "down": 0, "left": 0, "up": 0}


# === ACK LISTENER THREAD ===
def ack_listener(sock, acked_packets):
    """Listen for ACKs from simulation."""
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            msg = json.loads(data.decode())
            ack_seq = msg.get("ack")
            if ack_seq is not None:
                acked_packets.add(ack_seq)
                print(f"✅ ACK received for seq={ack_seq}")
                logging.info(f"ACK received for seq={ack_seq}")
        except Exception:
            pass


# === SEND VEHICLE DATA (Sliding Window + Loss Simulation) ===
def send_vehicle_data(junction_id, host, port, interval):
    global zero_streak

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)

    directions = ["right", "down", "left", "up"]
    print(f"🚦 Reliable Sensor Node (Sliding Window + Packet Loss Simulation) started for Junction {junction_id} → {(host, port)}")
    logging.info(f"Sensor Node started for Junction {junction_id} → {(host, port)}")

    acked_packets = set()
    seq_number = 0

    # Performance counters
    stats = {"sent": 0, "acked": 0, "retransmitted": 0, "dropped": 0}

    # Start ACK listener thread
    threading.Thread(target=ack_listener, args=(sock, acked_packets), daemon=True).start()

    try:
        while True:
            counts = fetch_vehicle_counts()
            direction = directions[junction_id - 1] if 1 <= junction_id <= 4 else "right"
            vehicles_detected = counts.get(direction, 0)

            # Zero reading check
            if all(v == 0 for v in counts.values()):
                zero_streak += 1
                print(f"⚠️ Zero data detected ({zero_streak}/{MAX_ZERO_COUNT})")
                logging.warning(f"Zero data detected ({zero_streak}/{MAX_ZERO_COUNT})")
            else:
                zero_streak = 0

            if zero_streak >= MAX_ZERO_COUNT:
                print("🛑 No activity detected — simulation likely closed. Exiting sensor node.")
                logging.info("🛑 No activity detected — exiting sensor node.")
                break

            # Build window
            packets = []
            for i in range(WINDOW_SIZE):
                packets.append({
                    "seq": seq_number + i,
                    "junction_id": junction_id,
                    "vehicles_detected": vehicles_detected,
                    "timestamp": time.time()
                })

            base = seq_number
            retries = {p["seq"]: 0 for p in packets}
            total_packets = len(packets)

            print(f"\n🪟 Sending window: seq={base} → seq={base + total_packets - 1}")
            logging.info(f"Sending window: seq={base} → seq={base + total_packets - 1}")

            while base < seq_number + total_packets:
                for pkt in packets:
                    seq = pkt["seq"]

                    # Skip ACKed packets
                    if seq in acked_packets:
                        continue

                    # Simulate packet loss
                    if random.random() < PACKET_LOSS_PROB:
                        print(f"❌ Packet seq={seq} lost in transmission (simulated)")
                        logging.warning(f"Packet seq={seq} lost (simulated)")
                        stats["dropped"] += 1
                        continue

                    # Normal send
                    try:
                        sock.sendto(json.dumps(pkt).encode(), (host, port))
                        print(f"📤 Sent seq={seq} | {pkt['vehicles_detected']} vehicles")
                        logging.info(f"Sent seq={seq} | {pkt['vehicles_detected']} vehicles")
                        stats["sent"] += 1
                    except Exception as e:
                        print(f"⚠️ Send failed for seq={seq}: {e}")
                        logging.error(f"Send failed for seq={seq}: {e}")
                    retries[seq] += 1

                # Wait for ACKs
                time.sleep(ACK_TIMEOUT)

                # Slide window when ACKs come
                while base in acked_packets and base < seq_number + total_packets:
                    stats["acked"] += 1
                    base += 1

                # Retransmit unacked packets
                unacked = [p["seq"] for p in packets if p["seq"] not in acked_packets]
                if unacked:
                    print(f"🔁 Retransmitting lost packets: {unacked}")
                    logging.warning(f"Retransmitting lost packets: {unacked}")
                    stats["retransmitted"] += len(unacked)

                # Handle permanently lost packets
                for seq in unacked:
                    if retries[seq] >= MAX_RETRIES:
                        print(f"❌ Packet seq={seq} dropped permanently after {MAX_RETRIES} retries")
                        logging.warning(f"Packet seq={seq} dropped permanently after {MAX_RETRIES} retries")
                        acked_packets.add(seq)
                        stats["dropped"] += 1

                if base >= seq_number + total_packets:
                    break

            seq_number += total_packets
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Sensor node manually stopped by user.")
        logging.info("🛑 Sensor node manually stopped by user.")

    finally:
        # === Print summary ===
        print("\n📊 --- Transmission Summary ---")
        print(f"📦 Total packets sent:        {stats['sent']}")
        print(f"✅ Total packets ACKed:       {stats['acked']}")
        print(f"🔁 Total retransmissions:     {stats['retransmitted']}")
        print(f"❌ Packets permanently lost:  {stats['dropped']}")
        logging.info(f"SUMMARY: {stats}")
        sock.close()
        os._exit(0)


# === MAIN ENTRY ===
def main():
    parser = argparse.ArgumentParser(description="IoT Sensor Node - Reliable UDP (Sliding Window + Logging + Loss Simulation)")
    parser.add_argument("--junction", type=int, default=1, help="Junction ID (1–4)")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host IP where simulation.py is listening")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP port to send data")
    parser.add_argument("--interval", type=float, default=SLEEP_INTERVAL, help="Seconds between updates")
    args = parser.parse_args()

    send_vehicle_data(args.junction, args.host, args.port, args.interval)


if __name__ == "__main__":
    main()
