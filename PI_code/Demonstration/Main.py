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


#Global Variables for UART

#this is a flag to signal if the program should stop, it won't often be set
program_quit=0
#this is a flag to signal that we should determine the object type, things that matter
detecting_object=0
#this is a flag to signal that the arms will be moving
moving_arm=0
#this is a flag, that is technically an integer, which will symbolize pair0(0) pair1(1) or both(2) pairs of arms being moved
pair_select=0
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
#this will be a flag to be set if there is new status during the process
new_status=0

#Variables for CV
#this will store the actual detected debris type
detected_debris_type=None
#this is a flag to signal between FSM_Actual and Computer_Vision that a new frame should be captured and object type determined
run_CV=0
#This is a lock so that the function capturing images and the one analyzing them don't have race issues
frame_lock= threading.Lock()
#This is where the image is sent when it is passed between the functions
color_frame = None


#Flag to control main loop
#If this gets set to false, everything will end
SYS_running = True
#This is a flag to signal that the UART is running
UART_running = False
#this is a flag to signal that the camera thread is running
CAM_running=False
#this is a flag to signal that the CV is running
CV_running=False

#Global variables for Arduino Communications
#establishes what bus to be communicated over
i2c_arduino=SMBus(1)
#establishes the address of each arduino
rot_ard_add=8
lin_ard_add=15

#dictionairy of the names of each of the various states
state_machine={
    "Initializing": stateA,
    "UART_Wait": stateB,
    "Moving_Arm": stateC,
    "Rotating_Arm": stateD,
    "ARD_Wait": stateE,
    "Detecting_Object": stateF,
    "Quit": stateQ
}

'''CODE'''
#This is the code that will be running when the system is on
#It is abstracted from a variety of sources

def main():
    global SYS_running
    current_state = stateA
    
    print("[INFO] Starting main, FSM in state: ", state_machine[current_state])
    
    while SYS_running:
        #Each state function returns a function pointer to the next function that will be called and executed
        next_state = current_state()
        #debugging
        print(f"Transitioning from {state_machine[current_state]} to {state_machine[next_state]}")
        current_state=next_state #hopefully this just does the name and doesn't actually like call the function, but maybe it would/will
        #note that the state loops and waiting conditions and stuff happen within them, so there isn't any potential issue with it like going to the same state a ton of times
    print("[INFO] Ending main, FSM in state: ", state_machine[current_state])
    return
    
if __name__ == "__main__":
    #debugging/status
    print("[INFO] Program beginning")
    main()
    print("[INFO] Program ending")
    
    






