# Temperature Display and MQTT Monitor
**Candidate:** Wihogora Florence  
**Trade Code:** SPE – Embedded Systems Software Integration

---

## System Overview

```
Analog Temp Sensor (S/+/-)
        │ A0
        ▼
   Arduino Uno  ──── I2C ────► 16×2 LCD
        │                    (row 1: scrolling name)
        │ USB Serial          (row 2: temperature °C)
        ▼
   PC Python Program
   (pc_monitor.py)
        │ TCP/IP (MQTT)
        ▼
   MQTT Broker (VPS)
   topic: spe/temperature
```

---

## Hardware Wiring

### Temperature Sensor (3-pin: S / + / -)
| Sensor pin | Arduino pin |
|-----------|-------------|
| S (signal) | A0 |
| + (VCC) | 5V |
| - (GND) | GND |

### 16×2 LCD with I2C backpack
| LCD pin | Arduino pin |
|---------|-------------|
| VCC | 5V |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

> **Note:** I2C address is usually `0x27` or `0x3F`. Change the address in the sketch if the LCD does not light up.

---

## Files

| File | Description |
|------|-------------|
| `temp_monitor.ino` | Arduino sketch — reads sensor, drives LCD, sends serial |
| `pc_monitor.py` | Python PC program — reads serial, publishes MQTT, displays live |
| `README.md` | This file |

---

## Part 1 — Arduino Sketch (`temp_monitor.ino`)

### What it does
- Reads an analog temperature sensor on pin A0
- Displays temperature on row 2 of the 16×2 LCD every second
- Displays candidate name on row 1 — **scrolls horizontally** if the name is longer than 16 characters ("Wihogora Florence" = 17 chars, so it scrolls)
- Sends temperature to the PC via Serial in the format `TEMP:23.5`

### Library required
Install via **Arduino IDE → Tools → Manage Libraries**:
- `LiquidCrystal_I2C` by Frank de Brabander

### Temperature formula
The default formula is for **LM35 / KY-013** style sensors:
```
Temp(°C) = (analogRead(A0) × 5.0 / 1023.0) × 100
```
If you have a **TMP36**, change the formula inside `readTemperatureCelsius()` to:
```
Temp(°C) = (voltage - 0.5) × 100
```

---

## Part 2 — PC Monitor (`pc_monitor.py`)

### Requirements
```bash
pip install pyserial paho-mqtt
```

### Configuration (edit top of file)
```python
SERIAL_PORT  = "COM3"           # Windows: COM3 / Linux: /dev/ttyUSB0
MQTT_BROKER  = "157.173.101.159"   # ← paste your VPS IP
MQTT_PORT    = 1883
MQTT_TOPIC   = "spe/temperature"
```

### Run
```bash
python pc_monitor.py
```

### Live output example
```
====================================================
  Temperature Monitor — Wihogora Florence
  Serial : COM3  |  Baud: 9600
  Broker : 192.168.1.100:1883
  Topic  : spe/temperature
====================================================
  Timestamp               Temp (°C)      MQTT
----------------------------------------------------
  2025-06-15 10:32:01        27.3°    ✓ sent
  2025-06-15 10:32:02        27.4°    ✓ sent
```

---

## Communication Details

| Link | Protocol | Details |
|------|----------|---------|
| Arduino → PC | UART Serial | 9600 baud, format: `TEMP:xx.x\n` |
| PC → MQTT broker | MQTT over TCP | Port 1883, QoS 1 |
| MQTT topic | — | `spe/temperature` |

---

## How to Subscribe and Verify (on any device)

```bash
mosquitto_sub -h 157.173.101.159 -p 1883 -t "spe/temperature"
```

---

## Screenshots
*(Add screenshots of the running system here before submission)*

---

## Dashboard

Open `dashboard.html` in any browser — it connects to the MQTT broker via WebSocket and shows:
- Live current temperature with colour coding (normal / warm / hot)
- Min / max / total readings
- Live scrolling line chart (last 40 readings)
- Raw MQTT message log

> **Requirement:** The Mosquitto broker on the VPS must have WebSocket listener enabled on port 9001. See hosting guide below.

---

## Hosting the Dashboard (GitHub Pages)

1. Push the repo to GitHub
2. Go to repo **Settings → Pages → Source → main branch / root**
3. Your dashboard will be live at `https://<your-username>.github.io/<repo-name>/dashboard.html`

Paste that URL into the Google Form as the dashboard link.

---

## VPS Broker Setup (Mosquitto with WebSocket)

SSH into your VPS then run:

```bash
sudo apt update && sudo apt install -y mosquitto mosquitto-clients

sudo nano /etc/mosquitto/conf.d/default.conf
```

Paste this into the file:
```
listener 1883
allow_anonymous true

listener 9001
protocol websockets
allow_anonymous true
```

Then restart:
```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

Test from another terminal:
```bash
mosquitto_sub -h 157.173.101.159 -p 1883 -t "spe/temperature"
```
