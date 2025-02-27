# Purpose: this is a functional file to set up the Raspberry Pi to Vilros time of flight sensor
# Contributors: Walter, Angela
# Sources: 
#   https://github.com/adafruit/Adafruit_CircuitPython_VL53L0X python usage
#   https://cdn-learn.adafruit.com/downloads/pdf/adafruit-vl53l0x-micro-lidar-distance-sensor-breakout.pdf sensor datasheet
# Relevant files: 
# Circuitry: connect the following listed pins
#   top left pin on pi is 3.3V, connect to Vin, as is 9th from top left
#   second pin from top on left (03) is SDA on Pi, (blue cable)
#   third pin from top on left (05) is SCL on Pi, (white cable)
#   fifth pin from top left (09) is ground on Pi.
#   sensor has a voltage regulator, so Vin can be 5V-3V and it will work

#   Must install the Adafruit Circuit Python VL53L0X, ensure latest version of Adafruit Circuit Python is running
#   Ensure adafruit_vl53l0x.mpy and adafruit_bus_device libraries installed
#   run sudo pip3 install adafruit-circuitpython-vl53l0x from command line

import time

import board
import busio

import adafruit_vl53l0x

# Initialize I2C bus and sensor.
#Note that the I2C address will be default 0x29, or 41
i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

# Optionally adjust the measurement timing budget to change speed and accuracy.
# See the example here for more details:
#   https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino
# For example a higher speed but less accurate timing budget of 20ms. It seems to be off by about 15mm
# vl53.measurement_timing_budget = 20000
# Or a slower but more accurate timing budget of 500ms:
vl53.measurement_timing_budget = 500000
# The default timing budget is 33ms, a good compromise of speed and accuracy.
# it seems like there is a constant offset of being too high by about 35mm, or 3.5cm,
# from the bottom of the breadboard it is about a centimeter, so we will do 25mm
#   data-(35mm-10mm for breadboard base)
#   this makes us short by about 10mm still, so we will go with 15.
#   at 100mm, we get between 92 and 96
# this makes short measurements accurate, but what about longer ones?
#   at 282 mm range, we get 285
# with the -15 to the measured value, we get to be within 3% error
#   This is the accuracy listed on the sensor data sheet, so it is alright
#   Sensor data sheet requires diameter of the object at half the range 
while True:
    raw_distance=vl53.range
    calibrated_distance=raw_distance-15
    print("Range: {0}mm".format(calibrated_distance))
    time.sleep(1.0)
