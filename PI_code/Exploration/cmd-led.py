# Purpose: build a basic circuit that will run using the pi. It will require the user to press a button in one circuit, and turn on a LED in a different circuit.
# Contributors: Walter
# Sources: using GPIO zero library, at https://gpiozero.readthedocs.io/
# Relevant files: if this draws from other code, or other code draws from this, please cite the relevant file
# Circuitry: Pin 1 is at the top left, with USB ports at bottom left. Format is left to right.
#1,2
#3,4
# connect an LED and a resistor in series, with one end connecting to pin 11, other end connecting to 6 (GND)

import gpiozero
from time import sleep


#if the circuit is connected to GPIO17, specify the pin as 17 (not 11)
led=gpiozero.LED(17)

led.on()
print("program starting")
sleep(0.5)
led.off()
sleep(0.1)

enable = False

while True: 
    sleep(1) #start off with waiting a second. The decided upon task will execute until a new one is entered
    cmd = input("enter \'ON\', \'OFF\', \'STROBE\', or \'DONE\': ")
    match cmd:
        case "ON":
            led.on()
        case "OFF":
            led.off()
        case "STROBE":
            led.on()
            sleep(1)
            led.off()
            sleep(1)
            led.on()
            sleep(1)
            led.off()
        case "DONE":
            break
