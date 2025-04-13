"""
send_angle_distance.py
-----------------------
This script sends two bytes to two separate Arduinos over a shared I2C bus:
    - Byte 1: angle_byte (0–255) → mapped to 0–180° rotation
    - Byte 2: distance_byte (0–255) → mapped to vertical lift height

Hardware Setup:
---------------
Raspberry Pi I2C bus (typically /dev/i2c-1) is connected to two Arduinos:
  - Arduino A (Linear Control) at address 0x08
      - Receives both bytes, uses only distance_byte
  - Arduino B (Rotation Control) at address 0x09
      - Receives only angle_byte

Wiring (shared I2C):
  - Pi SDA  → Arduino A4 (both Arduinos)
  - Pi SCL  → Arduino A5 (both Arduinos)
  - Pi GND  → Arduino GND (shared)
  - Pull-up resistors (4.7kΩ) recommended on SDA and SCL

Usage:
------
1. Enable I2C on Raspberry Pi:
    $ sudo raspi-config   → Interfacing Options → Enable I2C
2. Install smbus2:
    $ pip install smbus2
3. Run the script:
    $ python3 send_angle_distance.py

Adjust angle_deg and distance_m to test different positions.
"""

from smbus2 import SMBus
import time

# I2C addresses
LINEAR_ADDR = 0x08       # Arduino A: linear lift
ROTATION_ADDR = 0x09     # Arduino B: rotation

# Convert physical units to byte values
def encode_angle(degrees):
    return max(0, min(255, int((degrees / 180.0) * 255)))

def encode_distance(meters, max_m=1.0):
    return max(0, min(255, int((meters / max_m) * 255)))

# Example test values
angle_deg = 90          # degrees (0–180)
distance_m = 0.5        # meters (0–1.0)

# Convert to byte values
angle_byte = encode_angle(angle_deg)
distance_byte = encode_distance(distance_m)

# Send bytes over I2C
with SMBus(1) as bus:
    try:
        # Send to linear Arduino
        bus.write_i2c_block_data(LINEAR_ADDR, 0, [angle_byte, distance_byte])
        print(f"Sent to Linear Arduino (0x08): angle={angle_byte}, distance={distance_byte}")
    except Exception as e:
        print(f"Error sending to Linear Arduino: {e}")

    time.sleep(0.1)  # short delay between transmissions

    try:
        # Send to rotation Arduino
        bus.write_i2c_block_data(ROTATION_ADDR, 0, [angle_byte])
        print(f"Sent to Rotation Arduino (0x09): angle={angle_byte}")
    except Exception as e:
        print(f"Error sending to Rotation Arduino: {e}")
