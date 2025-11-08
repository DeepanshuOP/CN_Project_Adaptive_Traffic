import socket
import json
import threading

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5051
BUFFER_SIZE = 2048

def start_udp_listener(on_data_callback, host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Start a UDP listener in a daemon thread.
    on_data_callback(payload: dict) will be called for each received JSON message.
    """

    def listen():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # ✅ Allow port reuse immediately after exit
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # ✅ Try binding; if port busy, auto-increment
        try:
            sock.bind((host, port))
        except OSError as e:
            print(f"⚠️  Port {port} is busy ({e}). Trying alternate port...")
            port_alt = port + 1
            sock.bind((host, port_alt))
            print(f"✅  Bound to alternate port {port_alt}")
        else:
            print(f"🔊 UDP listener started on {host}:{port}")

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                try:
                    payload = json.loads(data.decode())
                except Exception as e:
                    print("⚠️  Received non-JSON or decode error:", e)
                    continue

                try:
                    on_data_callback(payload)
                except Exception as e:
                    print("⚠️  Error in on_data_callback:", e)

            except Exception as e:
                print("⚠️  UDP listener error:", e)
                break

        sock.close()

    thread = threading.Thread(target=listen, daemon=True, name="udp-listener")
    thread.start()
    return thread
