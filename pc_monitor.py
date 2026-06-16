"""
PC Monitor — Temperature Serial Reader + MQTT Publisher
Candidate: Wihogora Florence

Install dependencies once:
    pip install pyserial paho-mqtt

Usage:
    python pc_monitor.py
"""

import sys
import time
import serial
import paho.mqtt.client as mqtt
from datetime import datetime

# ── Serial port settings ─────────────────────────────────────────────────────
# Windows:  "COM3"  (check Device Manager → Ports)
# Linux  :  "/dev/ttyUSB0"  or  "/dev/ttyACM0"
# macOS  :  "/dev/cu.usbmodem..."
SERIAL_PORT = "COM3"         # ← change to your port
BAUD_RATE   = 9600

# ── MQTT broker settings ──────────────────────────────────────────────────────
MQTT_BROKER   = "157.173.101.159"    # ← paste your VPS IP here, e.g. "192.168.1.100"
MQTT_PORT     = 1883             # ← default MQTT port (change if yours differs)
MQTT_TOPIC    = "spe/temperature"
MQTT_CLIENT_ID = "wihogora_florence_monitor"

# Optional credentials (leave empty strings if broker has no auth)
MQTT_USERNAME = ""
MQTT_PASSWORD = ""

# ─────────────────────────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    codes = {
        0: "Connected successfully",
        1: "Bad protocol version",
        2: "Client ID rejected",
        3: "Broker unavailable",
        4: "Bad username/password",
        5: "Not authorised",
    }
    status = codes.get(rc, f"Unknown code {rc}")
    if rc == 0:
        print(f"[MQTT] {status} → broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"[MQTT] Publishing to topic: {MQTT_TOPIC}\n")
    else:
        print(f"[MQTT] Connection failed — {status}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[MQTT] Unexpected disconnection (code {rc}). Retrying...")

def on_publish(client, userdata, mid):
    pass   # silent; we print in the main loop instead

# ─────────────────────────────────────────────────────────────────────────────
def build_mqtt_client():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish    = on_publish
    return client

# ─────────────────────────────────────────────────────────────────────────────
def open_serial(port, baud, timeout=5):
    try:
        ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2)            # let Arduino reset after serial open
        ser.flushInput()
        print(f"[Serial] Opened {port} at {baud} baud\n")
        return ser
    except serial.SerialException as e:
        print(f"[Serial] Cannot open {port}: {e}")
        print("  Check: correct port? Arduino plugged in? Driver installed?")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
def parse_temperature(line: str):
    """
    Expected format from Arduino:  TEMP:23.5
    Returns float or None on parse failure.
    """
    line = line.strip()
    if line.startswith("TEMP:"):
        try:
            return float(line[5:])
        except ValueError:
            pass
    return None

# ─────────────────────────────────────────────────────────────────────────────
def print_header():
    print("=" * 52)
    print("  Temperature Monitor — Wihogora Florence")
    print(f"  Serial : {SERIAL_PORT}  |  Baud: {BAUD_RATE}")
    print(f"  Broker : {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Topic  : {MQTT_TOPIC}")
    print("=" * 52)
    print(f"  {'Timestamp':<22}  {'Temp (°C)':>10}  {'MQTT':>8}")
    print("-" * 52)

def print_reading(temp_c, mqtt_ok):
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✓ sent" if mqtt_ok else "✗ fail"
    print(f"  {ts:<22}  {temp_c:>9.1f}°  {status:>8}")

# ─────────────────────────────────────────────────────────────────────────────
def main():
    print_header()

    # Connect serial
    ser = open_serial(SERIAL_PORT, BAUD_RATE)

    # Connect MQTT
    client = build_mqtt_client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        print(f"[MQTT] Connection error: {e}")
        print("  Check: broker IP correct? Port open? Network reachable?")
        sys.exit(1)

    client.loop_start()   # background thread handles MQTT network loop

    print("\n[Monitor] Running — press Ctrl+C to stop\n")

    try:
        while True:
            # Read one line from Arduino
            try:
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore")
            except serial.SerialException as e:
                print(f"\n[Serial] Read error: {e}")
                break

            temp = parse_temperature(line)
            if temp is None:
                continue    # skip non-temperature lines / debug noise

            # Publish to MQTT
            payload  = f"{temp:.1f}"
            result   = client.publish(MQTT_TOPIC, payload, qos=1, retain=False)
            mqtt_ok  = (result.rc == mqtt.MQTT_ERR_SUCCESS)

            # Display in real time
            print_reading(temp, mqtt_ok)

    except KeyboardInterrupt:
        print("\n\n[Monitor] Stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()
        ser.close()
        print("[Monitor] Serial and MQTT connections closed.")

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
