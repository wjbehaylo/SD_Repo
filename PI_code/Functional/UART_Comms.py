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

#this is a flag to signal if capture is going on
capture_start=0
#this is a flag to signal if the program should stop, it won't often be set
program_quit=0
#this is a flag to signal that we should read the time of flight sensor
detecting_distance=0
#this is a flag to signal that we should determine the object type
detecting_object=0
#this is a flag to signal that the arms will be moving
moving_arm=0
#this is a value to write how many steps the arms will be moving
move_amount=0
#this is a flag to signal if arms are rotating
rotating_arm=0
#this is a flag to signal whether we want to configure arm or not
configuring_arm=0
#this is a flag to signal what configuration we want = configuration is 0, + configuration is 1
arm_configuration=0
#this is a value to signal how many degrees the arms will be rotating
rotate_amount=0
#this is going to be a string of the status of whatever thing just happened
status_UART="" 

def UART():
    #global variables
    global capture_start
    global program_quit
    global detecting_distance
    global detecting_object
    global moving_arm
    global move_amount
    global rotating_arm
    global rotate_amount
    global configuring_arm
    global arm_configuration
    global rotating_arm
    
    global status_UART
    #if there are other usb devices connected before this, you may have to replace 0 with 1, 2, or 3 I think. Otherwise just find which port it is. 
    ser = serial.Serial('/dev/ttyAMA0')

    #9600 would work theoretically, maybe if this doesn't we use that.
    ser.baudrate=9600
    #debugging print(ser.name)
    ser.timeout = None #keeps reading line of communication as open until the message is received

    #I don't know about how else I need to configure it in terms of stop bits and whatever, so I'll just go with the standard for now.

    #debugging
    if(ser.is_open):
        print("It is open")
    ser.write(b"Connection Established\r\n")
    #we only want messages of one bit at a time. We will have switch statement and output the confirmed message based on the input
    #We need the message in bytes, the message reinterpretted, and to send the message back
    message_bytes=ser.readline(1)
    message=message_bytes.decode('utf-8')
    ser.write(message_bytes+b"\r\n")

    print(message)
    while(message != 'Q'):
        match message:
            case '?':
                ser.write(b"Usage Guidelines:\r\nThe following is a list of possible one character messages that can be sent\r\n")
                ser.write(b"    (?): Help, prints out the Usage Guidelines\r\n\n")
                
                ser.write(b"    (S): Start, begins the standard capture process\r\n")
                ser.write(b"    (Q): Quit, terminates the serial connection\r\n\n")

                ser.write(b"    (D): Distance, output distance to the debris\r\n")
                ser.write(b"    (T): Type, output type of debris detected\r\n\n")
                
                ser.write(b"    (M): Move, followed by a value, actuate X steps (+ is TBD, - is TBD)\r\n")
                ser.write(b"    (O): Open, fully open the claw\r\n")
                ser.write(b"    (C): Close, fully close the claw\r\n\n")
                
                ser.write(b"    (R): Rotate, followed by a value, rotate X degrees (+ is TBH, - is TBD\r\n") #degrees to steps conversion will be determined
                ser.write(b"    (=): Equals, rotates the claw into = configuration\r\n")
                ser.write(b"    (+): Plus, rotates the claw into the plus configuration\r\n\n")
            case 'S':
                #this case corresponds to the general capture process
                ser.write(b"Starting capture process\r\n")
                #this is a global flag that will be established, so that the other threaded process will know to start the process
                capture_start=1
                #it will be set back to 0 once capture is complete, at which point this while loop will stop
                while(capture_start==1):
                    sleep(0.1)
                ser.write(b"Capture process finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
                    
            case 'Q':
                #this state, however infrequenctly used, will be to termiante the program's functionality and end the while loops
                ser.write(b"Quitting\r\n")
                program_quit=1
                #we want to exit this while loop, so that the connection gets closed
                break
            case 'D':
                #this state gets the distance reading from the time of flight sensor
                ser.write(b"Detecting distance\r\n")
                detecting_distance=1
                while(detecting_distance==1):
                    sleep(0.1)
                ser.write(b"Distance detection finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'T':
                #this state has the CV detect the type of the object 
                ser.write(b"Detecting object\r\n")
                detecting_object=1
                while(detecting_object==1):
                    sleep(0.1)
                ser.write(b"Object detection finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'M':
                #this state has the motor move by a certain amount
                ser.write(b"Input an integer to specify number of steps (+ is TBD, - is TBD)\r\n")
                x=ser.read_until(b"\n") #read until a newline character
                ser.write(b"Moving "+x+b" steps\r\n")
                x_int=int(x.decode('utf-8'))
                moving_arm=1
                move_amount=x_int
                while(moving_arm==1):
                    sleep(0.1)
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'O':
                #this state is just to fully open the arms
                ser.write(b"Opening claw\r\n")
                #note that this number will be positive or negative because of how we want to send it.
                #TBD pos or negative
                moving_arm=1
                move_amount=1000000 #undetermined positive or negative
                while(moving_arm==1):
                    sleep(0.1)
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'C':
                #this state is just to fully open the arms
                ser.write(b"Closing claw\r\n")
                #note that this number will be positive or negative because of how we want to send it.
                #TBD pos or negative
                moving_arm=1
                move_amount=-1000000 #undetermined positive or negative
                while(moving_arm==1):
                    sleep(0.1)
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'R':
                #this state has the motor move by a certain amount
                ser.write(b"Input an integer to specify number of degrees (+ is TBD, - is TBD)\r\n")
                x=ser.read_until(b"\n") #read until a newline character
                ser.write(b"Rotating "+x+b" degrees\r\n")
                x_int=int(x.decode('utf-8'))
                rotating_arm=1
                rotate_amount=x_int
                while(rotating_arm==1):
                    sleep(0.1)
                ser.write(b"Arm rotation finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case '=':
                ser.write(b"Rotating arm into = configuration\r\n")
                configuring_arm=1
                arm_configuration=0
                while(configuring_arm==1):
                    sleep(0.1)
                ser.write(b"Arm configuration finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case '+':
                ser.write(b"Rotating arm into + configuration\r\n")
                configuring_arm=1
                arm_configuration=1
                while(configuring_arm==1):
                    sleep(0.1)
                ser.write(b"Arm configuration finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            
        message_bytes=ser.readline(1)
        message=message_bytes.decode('utf-8')
        print(message)
        ser.write(message_bytes+b"\r\n")
    ser.close()
