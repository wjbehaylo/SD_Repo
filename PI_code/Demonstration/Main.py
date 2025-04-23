# Purpose: this is a demonstrable file that should include the Pi's full functionality
# Contributors: Walter, Angela
# Sources: 
#   Other files
# Relevant files: 
#   UART_Comms.py contains the code for the UART system
#   Computer_vision.py contains the code used for the computer vision and camera capturing
#   ARD_Comms.py contains the functions used to write to and read from the Arduinos over I2C
#   FSM_Actual.py contains the states that are gone through
#   Generate_Status.py contains the function to generate status strings from status codes
#   camera_matrix.npy contains the numpy array for the camera's calibration matrix
#   distortion_coeffs.npy contains the numpy array for the caera's distortion coefficients
# Circuitry: 

'''UART
# use the HiLetgo CP2102 USB converter with free cable, and the raspberry pi 5, and the wires. 
# pin 1 (top left, consider usb ports to be bottom of board) is 3.3V, connect to 3.3V on converter (green)
# pin 6 (third down on right) is ground, connect to ground on converter (white)
# pin 8, (fourth down on right) is GPIO14, TXD. Connect to RXD on converter (purple)
# pin 10, (fifth down on right) is GPIO15, RXD. Connect to TXD on converter (blue)
'''

'''I2C
# There are two I2C devices to connect to
# These are both conected to the blue breadboard which serves as a shared bus
# essentially make sure that the white cables are all connected, the black cables are all connected, and the blue cables are all connected
# 
#   A4 is SDA on Arduino, second pin from top on left (03) is SDA on Pi, the blue cables need to connect
#   A5 is SCL on Arduino, third pin from top on left (05) is SCL on Pi, the white cables need to connect
#   GND on Arduino to fifth pin from top left (09) on Pi, the black cables need to connect
#   
#   Also note that both Arduinos need to be powered on, as does the Pi, when everything is connected, otherwise it won't detect the devices properly
#   You can run i2cdetect -y 1 on the pi's terminal, once everything is connected, and it should recognize devices at addresses 0x08 and 0x0f
# '''

'''Camera
# The camera just needs to plug into one of the USB ports on the Pi
'''

'''Power
# The Pi will be plugged into the White battery pack adjacent to it, via USB-C Cable
# The two arduinos should both be plugged into the black battery pack near them, via type B cables
# There are three battery packs, one for each of the motors, and they should each be charged and connected with their wires to the drivers, then velcrod in
'''

'''Arduinos
# For the Arduinos, follow the wiring outlines in Final_Lin_Comms.ino and Final_Rot_Comms.ino
'''


from smbus2 import SMBus #for I2C connection
from time import sleep #for debugging and timing management
from UART_Comms import UART #to get our UART Function
from ARD_Comms import * #importing all the ard functions
from Computer_Vision import * #importing the necessary computer vision functions
from Generate_Status import Generate_Status #for generating our status we will output
from FSM_Actual import * #for the functions used to change between the states
from globals import * #this declared the global variables that we will be using
#UART
import threading
import serial

#For CV
import cv2
import numpy as np
import time
from time import sleep
import threading
import math

#dictionairy of the names of each of the various states
state_machine={
    stateA:"Initializing",
    stateB:"UART_Wait",
    stateC:"Moving_Arm",
    stateD:"Rotating_Arm",
    stateE:"ARD_Wait",
    stateF:"Detecting_Object",
    stateQ:"Quitting"
}

'''CODE'''
#This is the code that will be running when the system is on
#It is abstracted from a variety of sources

def main():
    global global.SYS_running
    current_state = stateA
    
    #I think I might've been having an issue because the threads were initialized in stateA, rather than here, so they would've rapidly gone out of scope
    uart_thread = threading.Thread(target=UART, daemon = True)
    cam_thread = threading.Thread(target= capture_frame, daemon = True)
    cv_thread = threading.Thread(target = debris_detect, daemon = True)
    uart_thread.start()
    cam_thread.start()
    cv_thread.start()
    
    current_state_name = state_machine[current_state]
    print("[INFO] Starting main, FSM in state: ", current_state_name)
    
    while (SYS_running== True):
        #if we are in this state we should not be I think.
        if(current_state==stateQ):
            break
        #Each state function returns a function pointer to the next function that will be called and executed
        next_state = current_state()
        #debugging
        print(f"Transitioning from {state_machine[current_state]} to {state_machine[next_state]}")
        current_state=next_state #hopefully this just does the name and doesn't actually like call the function, but maybe it would/will
        #note that the state loops and waiting conditions and stuff happen within them, so there isn't any potential issue with it like going to the same state a ton of times
        
        #a bit concerning, but for some reason SYS_running getting set to false wasn't stopping the execution how it should've
        
    print("[INFO] Ending main, FSM in state: ", state_machine[current_state])
    return
    
if __name__ == "__main__":
    #debugging/status
    print("[INFO] Program beginning")
    main()
    print("[INFO] Program ending")
    
    






