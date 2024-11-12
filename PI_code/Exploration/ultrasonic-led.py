# Purpose: utilize real time clocking and ultrasonic sensors to detect distance using a raspberry pi
# Contributors: Walter
# Sources: using GPIO zero library, at https://gpiozero.readthedocs.io/
# Relevant files: if this draws from other code, or other code draws from this, please cite the relevant file
# Circuitry: Pin 1 is at the top left, with USB ports at bottom left. Format is left to right.
#1,2
#3,4
# for this, a breadboard will be necessary
#connect pin 6 to GND
#connect pin 2 to VCC (5V)
#connect pin 18 (GPIO 24, trig) to trig
#on the breadboard,
# resistor connecting GND and pin 16 (GPIO 23, echo)
# resistor connecting ECHO and pin 16 (GPIO 23)

#connect pin 11 (GPIO 17) to an LED in series with a resistor connected to ground (pin6)

import gpiozero


#essentially with US sensors, trigger is applied and has the US send out a value
#Then, echo is set high when it comes back. Based on the time it takes he US wave to travel and return, the distance to the object is calculated

#the first parameter to distance sensor is the pin corresponding to echo,
#trig is the second one, 
# max_distance, which sets the maximum distance in the range (m)
# threshold_distance, the close side of the range (m)
ultrasonic_1=gpiozero.DistanceSensor(23, 24)

pwm_led=gpiozero.PWMLED(17)

while True:
    print('Distance to nearest object is', ultrasonic_1.distance, 'm')
    pwm_led.value=1-ultrasonic_1.distance #set the pwm value to be 1- the detected distace. so at 1m it will be off, at 0.1 it will be almost bright

