import random
import math
import time
import threading
import pygame
import sys
import os
import signal
from flask import Flask, jsonify


# === DEFAULT CONFIGURATION ===
defaultRed = 150
defaultYellow = 5
defaultGreen = 20
defaultMinimum = 10
defaultMaximum = 60

signals = []
noOfSignals = 4
simTime = 300
timeElapsed = 0

currentGreen = 0
nextGreen = (currentGreen + 1) % noOfSignals
currentYellow = 0

# === VEHICLE TIMING AND SPEED ===
carTime = 2
bikeTime = 1
rickshawTime = 2.25
busTime = 2.5
truckTime = 2.5
noOfCars = noOfBikes = noOfBuses = noOfTrucks = noOfRickshaws = 0
noOfLanes = 2
detectionTime = 5
speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'rickshaw': 2, 'bike': 2.5}

# === PATH HANDLING ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images")

# === COORDINATES ===
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}
vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0},
            'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0},
            'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'rickshaw', 4: 'bike'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]
vehicleCountCoods = [(480, 210), (880, 210), (880, 550), (480, 550)]
vehicleCountTexts = ["0", "0", "0", "0"]
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stops = {'right': [580, 580, 580], 'down': [320, 320, 320],
         'left': [810, 810, 810], 'up': [545, 545, 545]}
mid = {'right': {'x': 705, 'y': 445}, 'down': {'x': 695, 'y': 450},
       'left': {'x': 695, 'y': 425}, 'up': {'x': 695, 'y': 400}}
rotationAngle = 3
gap = 15
gap2 = 15

pygame.init()
simulation = pygame.sprite.Group()


# === SIGNAL CLASS ===
class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "30"
        self.totalGreenTime = 0


# === VEHICLE CLASS ===
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1

        path = os.path.join(IMG_DIR, direction, f"{vehicleClass}.png")
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        # STOP LOGIC
        if direction == 'right':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].currentImage.get_rect().width - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] -= temp
            stops[direction][lane] -= temp

        elif direction == 'left':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] += temp
            stops[direction][lane] += temp

        elif direction == 'down':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] -= temp
            stops[direction][lane] -= temp

        elif direction == 'up':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] += temp
            stops[direction][lane] += temp

        simulation.add(self)

    def render(self, screen):
        screen.blit(self.currentImage, (self.x, self.y))

    def move(self):
        if self.direction == 'right':
            if self.crossed == 0 and self.x + self.currentImage.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if self.willTurn == 1:
                if self.crossed == 0 or self.x + self.currentImage.get_rect().width < mid[self.direction]['x']:
                    if ((self.x + self.currentImage.get_rect().width <= self.stop or (currentGreen == 0 and currentYellow == 0) or self.crossed == 1)
                        and (self.index == 0 or self.x + self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - gap2)
                             or vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.x += self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if (self.index == 0 or
                                self.y + self.currentImage.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - gap2) or
                                self.x + self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - gap2)):
                            self.y += self.speed
            else:
                if ((self.x + self.currentImage.get_rect().width <= self.stop or self.crossed == 1 or (currentGreen == 0 and currentYellow == 0))
                        and (self.index == 0 or
                             self.x + self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - gap2) or
                             vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                    self.x += self.speed

        elif self.direction == 'down':
            if self.crossed == 0 and self.y + self.currentImage.get_rect().height > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if self.willTurn == 1:
                if self.crossed == 0 or self.y + self.currentImage.get_rect().height < mid[self.direction]['y']:
                    if ((self.y + self.currentImage.get_rect().height <= self.stop or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1)
                            and (self.index == 0 or
                                 self.y + self.currentImage.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - gap2) or
                                 vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.y += self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if (self.index == 0 or
                                self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width + gap2)
                                or self.y < (vehicles[self.direction][self.lane][self.index - 1].y - gap2)):
                            self.x -= self.speed
            else:
                if ((self.y + self.currentImage.get_rect().height <= self.stop or self.crossed == 1 or (currentGreen == 1 and currentYellow == 0))
                        and (self.index == 0 or
                             self.y + self.currentImage.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - gap2) or
                             vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                    self.y += self.speed

        elif self.direction == 'left':
            if self.crossed == 0 and self.x < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if self.willTurn == 1:
                if self.crossed == 0 or self.x > mid[self.direction]['x']:
                    if ((self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1)
                            and (self.index == 0 or
                                 self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width + gap2)
                                 or vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.x -= self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if (self.index == 0 or
                                self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().height + gap2) or
                                self.x > (vehicles[self.direction][self.lane][self.index - 1].x + gap2)):
                            self.y -= self.speed
            else:
                if ((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0))
                        and (self.index == 0 or
                             self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width + gap2)
                             or vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                    self.x -= self.speed

        elif self.direction == 'up':
            if self.crossed == 0 and self.y < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if self.willTurn == 1:
                if self.crossed == 0 or self.y > mid[self.direction]['y']:
                    if ((self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1)
                            and (self.index == 0 or
                                 self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().height + gap2)
                                 or vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.y -= self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if (self.index == 0 or
                                self.x < (vehicles[self.direction][self.lane][self.index - 1].x - vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width - gap2)
                                or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + gap2)):
                            self.x += self.speed
            else:
                if ((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0))
                        and (self.index == 0 or
                             self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().height + gap2)
                             or vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                    self.y -= self.speed


# === INITIALIZATION ===
# === INITIALIZATION ===
def initialize():
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts3)
    signals.append(ts4)
    repeat()


def repeat():
    global currentGreen, currentYellow, nextGreen
    while signals[currentGreen].green > 0:
        updateValues()
        time.sleep(1)
    currentYellow = 1
    for i in range(3):
        stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while signals[currentGreen].yellow > 0:
        updateValues()
        time.sleep(1)
    currentYellow = 0
    signals[currentGreen].green = defaultGreen
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
    currentGreen = nextGreen
    nextGreen = (currentGreen + 1) % noOfSignals
    signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green
    repeat()


def updateValues():
    # first, apply any pending sensor readings in a synchronized way
    with pending_lock:
        # iterate through keys to apply adjustments
        for jid, vehicles in pending_sensor_readings.items():
            if 1 <= jid <= len(signals):
                idx = jid - 1
                # do not override the currently green junction
                if idx == currentGreen:
                    continue
                mapped_green = int(GREEN_MIN + (vehicles / 60.0) * (GREEN_MAX - GREEN_MIN))
                mapped_green = max(GREEN_MIN, min(GREEN_MAX, mapped_green))
                signals[idx].green = mapped_green
                # Optionally adjust red timers for others to maintain relative timing:
                # signals[(idx+1)%noOfSignals].red = signals[idx].yellow + signals[idx].green
                # ...or implement any policy you want
        # clear after applying
        pending_sensor_readings.clear()

    # existing logic (unchanged)
    for i in range(noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
                signals[i].totalGreenTime += 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1


def generateVehicles():
    while True:
        vehicle_type = random.randint(0, 4)
        lane_number = 0 if vehicle_type == 4 else random.randint(0, 1) + 1
        will_turn = 1 if lane_number == 2 and random.randint(0, 4) <= 2 else 0
        direction_number = random.randint(0, 3)
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(0.75)

def get_vehicle_counts():
    """
    Counts how many vehicles are waiting (not crossed) at each direction.
    Returns a dict like: {'right': 12, 'down': 8, 'left': 15, 'up': 10}
    """
    global vehicles, directionNumbers
    counts = {}
    for direction in directionNumbers.values():
        waiting = 0
        for lane in range(3):  # 3 lanes per direction
            waiting += sum(1 for v in vehicles[direction][lane] if v.crossed == 0)
        counts[direction] = waiting
    return counts


import json
import socket

def send_simulated_sensor_data(host="127.0.0.1", port=5051, interval=2):
    """Send realistic sensor data based on current vehicle queues."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        counts = get_vehicle_counts()
        for idx, direction in directionNumbers.items():
            payload = {
                "junction_id": idx + 1,
                "vehicles_detected": counts[direction],
                "timestamp": time.time()
            }
            sock.sendto(json.dumps(payload).encode(), (host, port))
            print(f"📡 Sent sensor for {direction.upper()} (Junction {idx+1}): {counts[direction]} vehicles")
        time.sleep(interval)

def simulationTime():
    global timeElapsed
    while True:
        timeElapsed += 1
        time.sleep(1)
        if timeElapsed == simTime:
            totalVehicles = sum(vehicles[d]['crossed'] for d in directionNumbers.values())
            print("Total vehicles passed:", totalVehicles)
            pygame.quit()
            sys.exit()

# --- NETWORK INTEGRATION SNIPPET (fixed) ---
try:
    # network_listener should be a module in the same `Code` package or alongside this file.
    from network_listener import start_udp_listener
except Exception:
    start_udp_listener = None
    print("⚠️ network_listener not found; UDP listener disabled.")

# Thread-safe storage for latest readings from sensors
pending_lock = threading.Lock()
pending_sensor_readings = {}  # maps junction_id -> last vehicles_detected

# min/max green times (same as defaults used in your simulation)
GREEN_MIN = defaultMinimum
GREEN_MAX = defaultMaximum

def handle_sensor_data(payload):
    """
    payload expected: {"junction_id": int, "vehicles_detected": int, "timestamp": float}
    We'll store latest reading and attempt to adjust signal green time if signals exist.
    """
    try:
        jid = int(payload.get("junction_id", 0))
        vehicles_count = int(payload.get("vehicles_detected", 0))
    except Exception:
        print("⚠️ Invalid sensor payload:", payload)
        return

    with pending_lock:
        pending_sensor_readings[jid] = vehicles_count

    # Try to apply immediately if signals are initialized
    try:
        if len(signals) >= jid >= 1:
            idx = jid - 1
            # Only adjust if the junction is NOT currently green
            if idx != currentGreen:
                # Simple linear mapping: more vehicles -> more green time
                mapped_green = int(GREEN_MIN + (vehicles_count / 60.0) * (GREEN_MAX - GREEN_MIN))
                mapped_green = max(GREEN_MIN, min(GREEN_MAX, mapped_green))
                signals[idx].green = mapped_green
                print(f"⚙️ Updated junction {jid}: vehicles={vehicles_count} -> new green={mapped_green}")
            else:
                print(f"⏸️ Junction {jid} is currently GREEN. Update postponed until next cycle.")
    except Exception as e:
        print("⚠️ handle_sensor_data error:", e)

if start_udp_listener:
    try:
        start_udp_listener(handle_sensor_data)
    except Exception as e:
        print("⚠️ Failed to start UDP listener:", e)
# --- END SNIPPET ---

# === FLASK SERVER FOR REAL-TIME VEHICLE DATA ===
app = Flask(__name__)
simulation_running = True  # Shared flag to tell nodes if sim is active
@app.route("/counts", methods=["GET"])
def get_counts_api():
    """Return live vehicle counts as JSON."""
    try:
        counts = get_vehicle_counts()
        return jsonify(counts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def start_flask_server():
    """Run Flask server in a background thread."""
    # You can change host to "0.0.0.0" if you want to access it from another PC on your network
    app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False)


def run_simulation():
    """Start the traffic simulation and visualization."""
    thread4 = threading.Thread(name="simulationTime", target=simulationTime, daemon=True)
    thread4.start()

    thread2 = threading.Thread(name="initialization", target=initialize, daemon=True)
    thread2.start()

    black, white = (0, 0, 0), (255, 255, 255)
    screenWidth, screenHeight = 1400, 800
    background = pygame.image.load(os.path.join(IMG_DIR, 'mod_int.png'))
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    pygame.display.set_caption("SIMULATION")

    redSignal = pygame.image.load(os.path.join(IMG_DIR, "signals", "red.png"))
    yellowSignal = pygame.image.load(os.path.join(IMG_DIR, "signals", "yellow.png"))
    greenSignal = pygame.image.load(os.path.join(IMG_DIR, "signals", "green.png"))
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(name="generateVehicles", target=generateVehicles, daemon=True)
    thread3.start()

    thread5 = threading.Thread(
        name="sensorSimulator",
        target=send_simulated_sensor_data,
        daemon=True
    )
    thread5.start()

    # Start Flask server in background
    thread_flask = threading.Thread(name="flaskServer", target=start_flask_server, daemon=True)
    thread_flask.start()
    print("🌐 Flask server running at http://127.0.0.1:5055/counts")

    # --- Graceful shutdown handler ---
    def handle_exit(*args):
        global simulation_running
        print("🛑 Simulation window closed — notifying all sensor nodes to stop.")
        simulation_running = False
        time.sleep(1)
        pygame.quit()
        os._exit(0)

    # Register SIGINT and SIGTERM for clean shutdowns
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # --- Main Simulation Loop ---
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                handle_exit()

        screen.blit(background, (0, 0))

        for i in range(noOfSignals):
            if i == currentGreen:
                if currentYellow == 1:
                    if signals[i].yellow == 0:
                        signals[i].signalText = "STOP"
                    else:
                        signals[i].signalText = str(signals[i].yellow)
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    if signals[i].green == 0:
                        signals[i].signalText = "SLOW"
                    else:
                        signals[i].signalText = str(signals[i].green)
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if signals[i].red <= 10:
                    if signals[i].red == 0:
                        signals[i].signalText = "GO"
                    else:
                        signals[i].signalText = str(signals[i].red)
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])

        for i in range(noOfSignals):
            signalTextSurface = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTextSurface, signalTimerCoods[i])
            displayText = vehicles[directionNumbers[i]]['crossed']
            vehicleCountSurface = font.render(str(displayText), True, black, white)
            screen.blit(vehicleCountSurface, vehicleCountCoods[i])

        timeElapsedSurface = font.render("Time Elapsed: " + str(timeElapsed), True, black, white)
        screen.blit(timeElapsedSurface, (1100, 50))

        for vehicle in simulation:
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()

        pygame.display.update()


# === FLASK SERVER FOR REAL-TIME VEHICLE DATA ===
app = Flask(__name__)

@app.route("/counts", methods=["GET"])
def get_counts_api():
    """Return live vehicle counts as JSON."""
    try:
        counts = get_vehicle_counts()
        return jsonify({"running": simulation_running, "counts": counts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def start_flask_server():
    """Run Flask server in a background thread."""
    app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_simulation()
