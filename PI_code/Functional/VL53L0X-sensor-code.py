# Purpose: this is a functional file to set up the Raspberry Pi to Vilros time of flight sensor
# Contributors: Walter, Angela
# Sources: 
#   https://github.com/adafruit/Adafruit_CircuitPython_VL53L0X python usage
#   https://cdn-learn.adafruit.com/downloads/pdf/adafruit-vl53l0x-micro-lidar-distance-sensor-breakout.pdf sensor datasheet
# Relevant files: 
# Circuitry: connect the following listed pins
#   top left pin on pi is 3.3V, connect to Vin
#   second pin from top on left (03) is SDA on Pi,
#   third pin from top on left (05) is SCL on Pi,
#   fifth pin from top left (09) is ground on Pi.
#   sensor has a voltage regulator, so Vin can be 5V-3V and it will work

# must launch the virtual environment using this command:
#   source circuitpython-env/bin/activate
#   to run this, any I suppose any later programs, run them through the command line using 'python3 VL53L0X-sensor-code.py' or similar command
# Must install the Adafruit Circuit Python VL53L0X, ensure latest version of Adafruit Circuit Python is running
#   Ensure adafruit_vl53l0x.mpy and adafruit_bus_device libraries installed
#   run sudo pip3 install adafruit-circuitpython-vl53l0x from command line

import time

import board
import busio

import adafruit_vl53l0x

# Initialize I2C bus and sensor.
#Note that the I2C address will be 0x29, or 41
i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

# Optionally adjust the measurement timing budget to change speed and accuracy.
# See the example here for more details:
#   https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino
# For example a higher speed but less accurate timing budget of 20ms:
vl53.measurement_timing_budget = 20000
# Or a slower but more accurate timing budget of 200ms:
# vl53.measurement_timing_budget = 200000
# The default timing budget is 33ms, a good compromise of speed and accuracy.

# Main loop will read the range and print it every second.
while True:
    print("Range: {0}mm".format(vl53.range))
    time.sleep(1.0)