# Purpose: this is a demonstrable file that has the currently up to data code on the FSM contained within it
# Contributors: Walter, Angela
# Sources: 
#   Based on programming used in SEED_LAB for python state machine
# Relevant files: 
#   UART_Comms.py contains the code for the UART system
#   CameraCalibAndShapeDetection.py contains the code used for the computer vision
#   VL53L0X-sensor-code.py contains the code that indicates how the VL53L0X time of flight sensor works
#   FSM_Outline contains the relevant states that are being used
# Circuitry: 
#   for the Pi, follow the circuitry outline in UART_Comms, VL53L0X-sensor-code, CameraCalibAndShapeDetection, and I2C_Arduino (exploration file)

#Arduino
from smbus2 import SMBus #this is to get the I2C connection functionality we want. We will need to run 
from time import sleep
from UART_Comms import UART #to get our UART Function
from ARD_Comms import * #importing all the ard functions
from Generate_Status import Generate_Status #for generating our status we will output

#Time of Flight, note that different I2C methods might be problematic
import board
import busio
import adafruit_vl53l0x

#UART
import threading
import serial

#Global Variables for UART

#this is a flag to signal if capture is going on
capture_start=0
#this is a flag to signal that the system should be reset
initialize=0
#this is a flag to signal if the program should stop, it won't often be set
program_quit=0
#this is a flag to signal that we should read the time of flight sensor
detecting_distance=0
#this is a flag to signal that we should determine the object type
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
#this will be a flag to be set if there is new status during the capture process.
#so when going through the states, if capture_start==1, then they will set 'new_status'=1 to signal that something needs to be sent out.
#after it is sent out over the ser_write stuff, new_status will be set back to 0
new_status=0

#Flag to control main loop
is_running = True



#Global variables for Arduino Communications
#establishes what bus to be communicated over
i2c_arduino=SMBus(1)
#establishes the address of each arduino
rot_ard_add=8
lin_ard_add=15

#These functions represent each of the states, with their transition logic present
#Note that in the state functions, all that matters is the transition logic, not the actual work.
#The actual work is done outside of this stuff, in the state machine

#Generally, when resetting you open first, then un rotate. When capturing, you rotate first, then close

#Initializing
def stateA():
    global moving_arm
    global pair_select
    global move_amount
    global configuring_arm
    global arm_configuration
    pair_select=2 #opening both pairs of arms
    moving_arm=1 #moving arm
    move_amount=1000000 #all the way open
    configuring_arm=1 #configuring arm
    arm_configuration=0 #= configuration
    
    #I'm not sure what all we would want to make sure is open here
    return stateC

#UART_Wait
def stateB():
    # we need all of the UART related global flag variables
    global capture_start
    global initialize
    global program_quit
    global detecting_distance
    global detecting_object
    global moving_arm
    global rotating_arm
    
    #we want an infinite loop, as it waits on UART stuff to come through
    #theoretically only one of these should go to 1 in a single command
    # they should all properly be set to 0 after execution as well
    #does it matter if I have an infinite loop here instead of recursively calling this function again if none of the things are 0?
    while (True):
        #the next state will be determined based on the set of variables in the UART module
        if(capture_start==1):
            initialize=1
            return stateA #first step in capturing is resetting the arms
        if(initialize==1):
            return stateA #in this case, we are just resetting
        if(moving_arm==1):
            return stateC
        if(rotating_arm==1):
            return stateD
        if(detecting_distance==1):
            return stateF
        if(detecting_object==1):
            return stateG
        if(program_quit==1):
            return stateQ
    
#Moving_Arm
#we either come here when initializing, capturing, or just moving the arm.
def stateC():
    #when initializing, we need to move both arms, pair_select is set to 2 previously
    #otherwise, if capturing, pair select will be updated in the data analysis
    #final option is deciding via UART< in which case pair select is still set
    
    lin_ARD_Write(lin_ard_add, pair_select, move_amount)
    
    #we automatically go to the ARD_Wait state after this one
    return stateE

#Rotating_Arm
def stateD():
    global rot_ard_add
    global rotate_amount
    OFFSET=0 #this doesn't/won't really matter I think, maybe it could be offsets for + vs = vs moveamount configuration
    ARD_Write(rot_ard_add, OFFSET, rotate_amount)
    return stateE

#ARD_Wait
def stateE():
    #here, what happens is based on whether we are rotating or moving the arm
    #note that when opening, moving comes before rotating
    #but when closing, rotating comes before moving
    
    #first, we need to check if we are initializing
    global initialize
    global lin_ard_add
    global rot_ard_add
    global moving_arm
    global rotating_arm
    global configuring_arm
    
    if(initialize==1):
        
        
    
#At this point, we are actually in the program that will be running to execute it all.

#state transition dictionary
#note that the flags corresponding to the states are lowercase with underscores, while the states are uppercase with underscores
state_machine={
    "Initializing": stateA,
    "UART_Wait": stateB,
    "Moving_Arm": stateC,
    "Rotating_Arm": stateD,
    "ARD_Wait": stateE,
    "Detecting_Distance": stateF,
    "Detecting_Object": stateG,
    "Data_Analysis": stateH,
    "Quit": stateQ
}

#note that how I am implementing it, the state's actions will happen within the state,
#and in the general system's while loop it will just call for one state to become the next

while(state!=stateQ):
    state=next_state()