# Purpose: this is a functional file to define functions related to UART communication
# Contributors: Walter
#Sources: 
# https://pyserial.readthedocs.io/en/latest/ Pi serial documentation
# https://pinout.ai/raspberry-pi-5 pinout on Pi 5
# Relevant files: 
# Exploration, UART_exploration.py
#Circuitry: 
# use the HiLetgo CP2102 USB converter with free cable, and the raspberry pi 5, and the wires. 
# pin 1 (top left, consider usb ports to be bottom of board) is 3.3V, connect to 3.3V on converter
# pin 6 (third down on right) is ground, connect to ground on converter
# pin 8, (fourth down on right) is GPIO14, TXD. Connect to RXD on converter
# pin 10, (fifth down on right) is GPIO15, RXD. Connect to TXD on converter

#note that to properly run UART there is a specific TBD order that the pi and putty must be opened

import serial
import threading #for threaded UART connection
import time
from time import sleep

#Global Variables

#we have a mutex here for filling vs reading the UART buffer
#it is initialized to 1, implying that it is currently open
#when a program uses it, they will need to wait for it to be 1 (not 0), and then set it to be 0 while it is in use.
UART_Mutex=1
UART_Comms=''

# def UART():

#if there are other usb devices connected before this, you may have to replace 0 with 1, 2, or 3 I think. Otherwise just find which port it is. 
ser = serial.Serial('/dev/ttyAMA0')

#9600 would work theoretically, maybe if this doesn't we use that.
ser.baudrate=115200
#debugging print(ser.name)
ser.timeout = None #keeps reading line of communication as open until the message is received

#I don't know about how else I need to configure it in terms of stop bits and whatever, so I'll just go with the standard for now.

#debugging
if(ser.is_open):
    print("It is open")
    
#we only want messages of one bit at a time. We will have switch statement and output the confirmed message based on the input
message=ser.readline(1)
while(message != 'Q'):
    match message:
        case '?':
            ser.write(b"Usage Guidelines:\nThe following is a list of possible one character messages that can be sent\n")
            ser.write(b"    (?): Help, prints out the Usage Guidelines\n\n")
            
            ser.write(b"    (S): Start, begins the standard capture process\n")
            ser.write(b"    (P): Pause, pauses the system's current execution\n")
            ser.write(b"    (Q): Quit, terminates the serial connection\n\n")

            ser.write(b"    (D): Distance, output distance to the debris\n")
            ser.write(b"    (T): Type, output type of debris detected\n\n")
            
            ser.write(b"    (M): Move, followed by a value, instructs the claw to close\n")
            ser.write(b"    (O): Open, fully open the claw\n")
            ser.write(b"    (C): Close, fully close the claw\n\n")
            
            ser.write(b"    (R): Rotate, followed by a value, instructs the claw to rotate\n")
            ser.write(b"    (=): Equals, rotates the claw into = configuration\n")
            ser.write(b"    (+): Plus, rotates the claw into the plus configuration\n\n")
ser.write(b"Quit option selected, closing UART connection\n")
ser.close()