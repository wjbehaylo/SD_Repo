# Purpose: just to test the functinoality of the rotational arduino communications, without needing to mess with the FSM
# Contributors: Walter, Angela
# Sources: 
#   Based on programming used in SEED_LAB for python state machine
#   ARD_Comms has the functions we need to send and receive from the arduino
#   Generate_Status prints out vectors from integer status codes being used
#   UART_Comms.py has the threaded functionality that lets the system communicate with UART
# Relevant files: 
#   UART_Comms.py contains the code for the UART system
#   ARD_Comms has the functions we need to send and receive from the arduino
#   Generate_Status prints out vectors from integer status codes being used
#   Rot_Comms.ino contains the Arduino code that will be running
# Circuitry: 
#   for the Pi, follow the circuitry outline in UART_Comms, and I2C_Arduino (exploration file)
#   For the Arduino, wire it to the pins and stuff as outlined in Rot_Comms.ino

#Arduino
from smbus2 import SMBus #this is to get the I2C connection functionality we want. We will need to run 
from time import sleep
from UART_Comms import UART #to get our UART Function
from ARD_Comms import * #importing all the ard functions
from Generate_Status import Generate_Status #for generating our status we will output

#Time of Flight, note that different I2C methods might be problematic, so this might just get cut out
'''
import board
import busio
import adafruit_vl53l0x
'''

#UART
import threading
import serial


#GLOBAL VARIABLES

#Global variables for Arduino Communications
#establishes what bus to be communicated over
i2c_arduino=SMBus(1)
#establishes the address of each arduino
rot_ard_add=8
lin_ard_add=15

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


'''ACTUAL TEST'''
#at this point, we should theoretically have the necessary global variables and flags for functionality

#So I'm gonna go ahead and do my best to Thread the UART function. TBH though I'm not sure how it will work with the function 



#I know that UART runs by itself, so what I'm gonna do right now is not yet thread it, but just try to have the Pi send to the Arduino the amount to rotate
while(True):
    command = input("Enter Y to start, or Q to quit: ")
    while(command != "Y" and command != "Q"):
        command = input("Enter Y to start, or Q to quit: ")
    if(command == "Q"):
        print("Entered Q, exiting test")
        break
    elif(command == "Y"):
        while(True):
            try:
                rotate_amount= float(input("Enter a number of degrees to rotate: "))
            except:
                print("Enter an actual number")
                continue
            break
            
        #now we need to tell the Arduino to move that far, and wait for it to move that far
        rot_ARD_Write(0, rotate_amount)
        result = rot_ARD_Read(0)
        #now that we've written to it and read from it, result should store the non '20' output
        #so we can use generate status function and continue with the loop
        message= Generate_Status(result)
        print(message)

#I think this should do all it is supposed to, it's pretty simple in general to be honest
        
