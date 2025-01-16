#Purpose: 
# This explorative code is to set up a communication between the Pi and a laptop. It will hopefully let messages be sent between the two, through Putty on the computer and this program on the pi.

#Contributors: Walter
#Sources: 
# https://pyserial.readthedocs.io/en/latest/ Pi serial documentation
# https://pinout.ai/raspberry-pi-5 pinout on Pi 5
#Relevant files: this file does not depend on any others

#Circuitry: 
# use the HiLetgo CP2102 USB converter with free cable, and the raspberry pi 5, and the wires. 
# pin 1 (top left, consider usb ports to be bottom of board) is 3.3V, connect to 3.3V on converter
# pin 6 (third down on right) is ground, connect to ground on converter
# pin 8, (fourth down on right) is GPIO14, TXD. Connect to TXD on converter
# pin 10, (fifth down on right) is GPIO15, RXD. Connect to RXD on converter

#alternatively, if the wires aren't available, use a USB to USB-C cable, plugged into one of the USB ports


import serial
import time

ser = serial.Serial('/dev/ttyAMA0')#if there are other usb devices connected before this, you may have to replace 0 with 1, 2, or 3 I think. Otherwise just find which port it is. 
ser.baudrate=9600 #not sure of proper rate, but I know this is an option. It could probably be anything though, as long as putty matches it
print(ser.name) #print out information about the connection

#I don't know about how else I need to configure it in terms of stop bits and whatever, so I'll just go with the standard for now.


#.is_open() returns true or false
print(ser.is_open())
ser.write(b"Hello, computer!") #then this should print this to the putty
ser.close() #and close the connection