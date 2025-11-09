🚦 Adaptive Traffic Signal Timer with IoT Integration & CN Reliability Layer
🧠 Overview

This project simulates an IoT-based Adaptive Traffic Signal System that dynamically adjusts green light durations based on real-time traffic density.
It uses the SCOOT (Split Cycle Offset Optimization Technique) for adaptive control and implements a Sliding Window Protocol for reliable UDP communication between IoT sensor nodes and the simulation server.

🌍 System Architecture
🔸 Components:

Simulation (Flask + Pygame)

Runs a full traffic intersection simulation using pygame.

Calculates live vehicle counts and adjusts signal timings via SCOOT Optimization.

Hosts a Flask API (/counts) to broadcast real-time traffic data.

IoT Sensor Nodes (UDP-based)

Represent the edge devices placed at each junction arm.

Fetch live data from Flask API.

Transmit vehicle counts to the simulation backend using UDP with a Sliding Window Protocol for reliability.

Network Listener (UDP Receiver)

Receives packets from all sensor nodes.

Acknowledges each packet (ACKs) to ensure reliable delivery even over UDP.

Logs transmission reliability data (sent, retransmitted, dropped packets).

🧩 Key Features
Feature	Description
🧮 SCOOT Algorithm (Level 2)	Dynamically adjusts each signal’s green time proportional to real-time vehicle density, using damped scaling to avoid overreaction.
🪟 Sliding Window Protocol	Ensures reliable UDP communication between IoT nodes and the simulation.
💀 Simulated Packet Loss & Retransmission	Demonstrates real-world CN reliability concepts (lost packets are retransmitted until acknowledged).
📊 Logging System	Logs ACKs, retransmissions, and lost packets to sensor_ack_log.txt.
⚙️ Auto Shutdown	Sensor nodes automatically close when the simulation stops or detects inactivity.
🧾 Flask API Endpoint	http://127.0.0.1:5055/counts provides live traffic density JSON to all IoT nodes.
⚙️ Technologies Used
Layer	Technology
Frontend (Simulation UI)	pygame
Backend API	Flask
IoT Node Communication	UDP (socket)
Reliability Protocol	Sliding Window + ACK
Algorithmic Control	SCOOT (Adaptive Signal Timing)
Data Fetching	requests
Logging	logging module
Visualization	matplotlib (optional)
📦 Installation
Step 1: Clone the Repository
git clone https://github.com/<your-username>/Adaptive-Traffic-Signal-Timer.git
cd Adaptive-Traffic-Signal-Timer

Step 2: Create a Virtual Environment
python -m venv venv
venv\Scripts\activate         # on Windows
# OR
source venv/bin/activate      # on macOS/Linux

Step 3: Install Dependencies
pip install -r requirements.txt

🚀 Running the Simulation
🧩 Step 1: Start the Traffic Simulation
python Code/simulation.py


✅ This will:

Launch the GUI simulation (using pygame).

Start the Flask server at:
👉 http://127.0.0.1:5055/counts

Begin adaptive signal control using SCOOT logic.

🛰️ Step 2: Run IoT Sensor Nodes

In separate terminals, run:

python iot_nodes/sensor_node.py --junction 1
python iot_nodes/sensor_node.py --junction 2
python iot_nodes/sensor_node.py --junction 3
python iot_nodes/sensor_node.py --junction 4


Each node:

Fetches live counts via Flask API.

Sends them using UDP + Sliding Window.

Handles packet loss, retransmissions, and ACKs automatically.

Logs everything into sensor_ack_log.txt.

🌐 Step 3: Network Listener

This runs automatically inside simulation.py and:

Listens on 0.0.0.0:5051

Receives UDP packets from sensor nodes.

Sends ACKs back for successful deliveries.

🧮 Example Console Output

Sensor Node Output:

🪟 Sending window: seq=20 → seq=23
📤 Sent seq=20 | 12 vehicles
📤 Sent seq=21 | 12 vehicles
❌ Packet seq=22 lost in transmission (simulated)
🔁 Retransmitting lost packets: [22]
✅ ACK received for seq=20
✅ ACK received for seq=21
✅ ACK received for seq=22


Simulation Output:

📡 Received packet from Junction 1: 12 vehicles
✅ Sent ACK for seq=22
🧮 SCOOT Optimization applied at 11:13:24
  • Junction 1: 12 vehicles → 28s green
  • Junction 2: 8 vehicles → 18s green


At Shutdown:

📊 --- Transmission Summary ---
📦 Total packets sent:        40
✅ Total packets ACKed:       40
🔁 Total retransmissions:     8
❌ Packets permanently lost:  0

📁 Project Structure
Adaptive-Traffic-Signal-Timer/
│
├── Code/
│   ├── simulation.py          # Main adaptive traffic simulation
│   ├── network_listener.py    # UDP listener & ACK sender
│   └── images/                # Assets for signals and vehicles
│
├── iot_nodes/
│   └── sensor_node.py         # IoT sensor script (UDP + Sliding Window)
│
├── requirements.txt
├── sensor_ack_log.txt         # Log file for ACKs and retransmissions
└── README.md

🧠 Understanding the CN Concepts Used
1. Sliding Window Protocol

Ensures reliable packet delivery over UDP.

Each packet has a unique seq number.

The receiver sends an ACK for each received packet.

Lost packets are retransmitted up to MAX_RETRIES.

2. SCOOT Algorithm (Adaptive Signal Control)

Each junction’s green time = base + weighted share of total cycle.

The weights are calculated using √vehicle_count to smooth sudden spikes.

Ensures fairness and efficiency in multi-junction control.

📊 Findings & Observations
Parameter	Description
✅ Adaptive Response	The SCOOT system adjusts green durations dynamically per density.
🪟 Reliable Transmission	Even with simulated 20% packet loss, all packets eventually reach using retransmission.
💾 Data Logging	Every packet’s status (sent, acked, lost, retransmitted) is logged for CN analysis.
🧮 Efficiency	Reduced average waiting time per lane using adaptive cycle distribution.