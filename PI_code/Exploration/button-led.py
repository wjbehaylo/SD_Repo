# Purpose: build a basic circuit that will run using the pi. It will require the user to press a button in one circuit, and turn on a LED in a different circuit.
# Contributors: Walter
# Sources: using GPIO zero library, at https://gpiozero.readthedocs.io/
# Relevant files: if this draws from other code, or other code draws from this, please cite the relevant file
# Circuitry: Pin 1 is at the top left, with USB ports at bottom left. Format is left to right.
#1,2
#3,4
# connect an LED and a resistor in series, with one end connecting to pin 11, other end connecting to 6 (GND)
#connect a button between pins 1 and 7, so that when pressed pin 7 will get the 3.3V from pin 1

import gpiozero
from time import sleep


#if the circuit is connected to GPIO17, specify the pin as 17 (not 11)
led=gpiozero.LED(17)
button=gpiozero.Button(7)
start = False


#In theory, this loop should run indefinitely. The button acts as an on-off toggle. 
while True:
    
    if button.is_pressed:
        start=not start
        print(start)

    if start:
        led.on()
        sleep(0.5)
        led.off()
        sleep(0.5)



    