import socket
import json
import threading
import random
import time
import logging

# === CONFIGURATION ===
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5051
BUFFER_SIZE = 2048

# Simulate unreliable network conditions
ACK_LOSS_PROB = 0.15      # 15% chance ACKs are "lost"
ACK_DELAY_RANGE = (0.1, 1.2)  # ACKs delayed between 100ms–1.2s

# === LOGGING CONFIGURATION ===
LOG_FILE = "listener_ack_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.info("🛰️ Network Listener started with ACK loss/delay simulation")


def start_udp_listener(on_data_callback, host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Start a UDP listener in a daemon thread.
    on_data_callback(payload: dict) will be called for each received JSON message.
    """

    def listen():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind((host, port))
            print(f"🔊 UDP listener started on {host}:{port}")
            logging.info(f"UDP listener started on {host}:{port}")
        except OSError as e:
            print(f"⚠️ Port {port} busy ({e}). Trying alternate port...")
            port_alt = port + 1
            sock.bind((host, port_alt))
            print(f"✅ Bound to alternate port {port_alt}")
            logging.info(f"Bound to alternate port {port_alt}")

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                try:
                    payload = json.loads(data.decode())
                    seq = payload.get("seq", None)
                except Exception as e:
                    print("⚠️ Received non-JSON or decode error:", e)
                    continue

                # --- Handle incoming payload ---
                print(f"📩 Received packet seq={seq} from {addr}")
                logging.info(f"Received packet seq={seq} from {addr}")

                try:
                    on_data_callback(payload)
                except Exception as e:
                    print(f"⚠️ Error in on_data_callback: {e}")
                    logging.error(f"Error in callback for seq={seq}: {e}")

                # --- Simulate ACK behavior ---
                # Drop ACK randomly
                if random.random() < ACK_LOSS_PROB:
                    print(f"💀 ACK for seq={seq} lost (simulated)")
                    logging.warning(f"ACK for seq={seq} lost (simulated)")
                    continue

                # Random delay before ACK
                delay = random.uniform(*ACK_DELAY_RANGE)
                threading.Timer(delay, send_ack, args=(sock, addr, seq)).start()

            except Exception as e:
                print("⚠️ UDP listener error:", e)
                logging.error(f"UDP listener error: {e}")
                break

        sock.close()

    def send_ack(sock, addr, seq):
        """Send ACK with optional delay."""
        ack_msg = json.dumps({"ack": seq}).encode()
        sock.sendto(ack_msg, addr)
        print(f"✅ Sent ACK for seq={seq} (after {round(random.uniform(*ACK_DELAY_RANGE), 2)}s delay)")
        logging.info(f"Sent ACK for seq={seq}")

    thread = threading.Thread(target=listen, daemon=True, name="udp-listener")
    thread.start()
    return thread
