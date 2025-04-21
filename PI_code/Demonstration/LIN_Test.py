# Purpose: just to test the functinoality of the linear arduino communications, without needing to mess with the FSM
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
#   Lin_Comms.ino contains the Arduino code that will be running
# Circuitry: 
#   for the Pi, follow the circuitry outline in UART_Comms, and I2C_Arduino (exploration file)
#   For the Arduino, wire it to the pins and stuff as outlined in Lin_Comms.ino

#Arduino
from smbus2 import SMBus 
from time import sleep
from UART_Comms import UART #to get our UART Function
from ARD_Comms import * #importing all the lin ard functions
from Generate_Status import Generate_Status #for generating our status we will output

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
move_amount=0 #number of steps to move
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

#variable offset to be set based on user input
offset = 0


'''ACTUAL TEST'''

valid_commands = ("Y", "Q")

print("=== Linear Arduino Test ===")

while True:
    command= input("\nEnter 'Y' to move an arbitrary amount of steps or 'Q' to quit: ")
    while command not in valid_commands:
        command = input("Invalid. Please enter 'Y' or 'Q': ")
    if(command == "Q"):
        print("Entered Q, exiting linear test")
        break
    elif(command == "Y"):
        #select which pairs(s) to move
        while(True):
            try:
                sel= int(input("Select pair (0=pair0, 1=pair1, 2=both): "))
                if sel in (0, 1, 2):
                    pair_select = sel
                    break
            except:
                print("Please enter a 0, 1, 2")
                continue
            break
        #next we will have the user enter in how many steps to move
        while(True):
            try: 
                amount = int(input("Enter the number of steps to move (+/- integer): "))
                move_amount = amount
                break
            except:
                print("Please enter a valid integer.")
                continue
        #send to linear arduino
        lin_ARD_Write(pair_select, move_amount)
        print(f"Sent to Arduino: pair={pair_select}, steps={move_amount}")
        
    #debugging
    print("Wrote offset: "+ str(pair_select) + " and move_amount: " + str(move_amount) + " to Arduino")
    sleep(5)
    result=[0,0] #This is just so it is initialized properly
    result = lin_ARD_Read(3+pair_select)
    status_msg = Generate_Status(result[0])
    status_msg +=Generate_Status(result[1])
    print(" Arduino stats:", status_msg)

        
