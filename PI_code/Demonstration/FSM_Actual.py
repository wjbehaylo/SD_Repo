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

#Initializing the system, this will go into moving arm then rotating arm
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
        #generally, only one of these should be 1 when this statement comes up
        if(capture_start==1):
            initialize=1
            detecting_distance=1
            detecting_object=1
            return stateA #first step in capturing is resetting the arms
        if(initialize==1):
            return stateA #in this case, we are just resetting
        if(moving_arm==1):
            return stateC #we are entering the moving arm state
        if(rotating_arm==1):
            return stateD #we are rotating the arm by some amount
        if(detecting_distance==1):
            return stateF #we are going to be detecting the distance
        if(detecting_object==1):
            return stateG #we will be using CV to detect the object
        if(program_quit==1):
            return stateQ #the program is exiting
    
#Moving_Arm
#we either come here when initializing, capturing, moving an amount, opening, or closing
def stateC():
    global new_status
    global status_UART
    #when initializing, we need to move both arms, pair_select is set to 2 previously
    #otherwise, if capturing, pair select will be updated in the data analysis
    #final option is deciding via UART in which case pair select is still set
    OFFSET=pair_select
    #when we select O or C in UART we also set the move_amount
    lin_ARD_Write(lin_ard_add, OFFSET, move_amount)
    #moving arm is set to 1 in the UART thread, or the capture start or initialize, 
    
    #we are going to want to incldicate that we are going to move the arm, and in doing so update the status
    status_UART+=f"Moving arms\r\n\tpair_select={pair_select}\r\n"
    new_status=1
    
    
    #we automatically go to the ARD_Wait state after this one
    return stateE

#Rotating_Arm
#we wither come here when initializing, capturing, rotating an amount, =, or + configuration
def stateD():
    global new_status
    global status_UART
    #OFFSET is 0 when we are rotating a specific amount
    #OFFSET is 1 when we are going to = configuration
    #OFFSET is 2 when we are going to + configuration
    
    #funny enough, configuring_arm + arm_configuration = OFFSET here.
    OFFSET=0 + configuring_arm + arm_configuration
    
    #if we get here, we at least know that we are in the rotating_arm section
    rot_ARD_Write(rot_ard_add, OFFSET, rotate_amount)
    
    #we are going to indiciate that we are going to rotate the arm, and in doing so update the status
    status_UART+=f"Rotating arms"
    #add to it if we are actually configuring the arms
    if(configuring_arm==1):
        if(arm_configuration==0):
            status_UART+=" to = configuration"
        elif(arm_configuration==1):
            status_UART+=" to + configuration"
    status_UART+="\r\n"
    new_status=1

    #we will automatically go to ARD_Wait here.
    return stateE

#ARD_Wait
#this state is gone to after stateC (move) or stateD (rotate)
#we could go from here to UART_Wait, move, rotate, or detectDistance
def stateE():
    #global variables that will be modified:
    global moving_arm
    global rotating_arm
    global configuring_arm
    global new_status
    global status_UART
    global initialize
    global capture_start
    #set the offsets that will be read from in either scenario
    MOVE_OFFSET=pair_select
    ROTATE_OFFSET=0+configuring_arm+arm_configuration
    #I think we need to consider initializing, then capturing, then pure movement
    '''
    Initializing:
        The entire system starts with initializing, as does the capture start
        We could be here after the move (first) or the rotate (second)
            If moving_arm==1, we are still moving, so we are reading linear and waiting on lin_ARD_read
            Because we move, then rotate, moving takes priority. 
                After this, we need to set moving_arm=0
            If moving_arm==0, we must just be waiting on the rotating.
                If rotating_arm==1, we wait on rot_ARD_read
                    After this, we set rotating_arm=0, same with configuring arm
                    Then, we move onto UART_wait
    '''
    '''
    Capturing:
        If we move here and initializing is 0 but capturing is 1, rotation takes priority over moving
        if rotating_arm==1 we wait on rot_ARD_read, move rotating_arm to 0 after. Same with configuring_arm=0.
        If rotating_arm==0, we are moving
            If moving_arm==1, we wait on lin_ARD_read, setting moving_arm to 0 after
                After this, we will have finished our capture.
                Theoretically here, what state we move to next will be based on the status returned from lin_ARD_read,
                    This is because whats next depends on why stopped stopped (unknown command, end stops, force sensors(preferred))    
    '''
    '''
    Pure Linear:
        If moving_arm==1 and initializing==0 and capture_start==0, we are just moving
        So we wait on lin_ARD_read(), setting the outputs status and whatnot, as well as setting moving_arm=0 after
    Pure Rotational:
        If rotating_arm==1 and intializing==0 and capture_start==0, we are just rotating
        This might be capturing, which effects what's being sent. 
            Based on the return status, it effects our output
    '''
    
    if(initialize==1):
        if(moving_arm==1):
            #remember that lin_ARD_Read returns an array of two integers
            move_status=lin_ARD_Read(MOVE_OFFSET)
            
            #In UART_Comms, we print out the status to UART, so we just need to update it based on what's returned
            #if pair0 and pair1 did stuff, we add that to the status_UART
            if(move_status[0]!=0):
                status_UART+=Generate_Status(move_status[0])+"\r\n"
            if(move_status[1]!=0):
                status_UART+=Generate_Status(move_status[1])+"\r\n"
            new_status=1            
            moving_arm=0 #need to set this back to 0 so we don't come here again
            
            #if either status is -1 it is a fatal error so we will exit this program
            if(move_status[0]==-1 or move_status[1]==-1):
                return stateQ
            
            #if it didn't fail, we move into the rotating state
            return stateD
        #if we get here, we must be rotating the arm
        elif(rotating_arm==1):
            rotate_status=rot_ARD_Read(ROTATE_OFFSET)
            #If we get here, we know status isn't gonna just be 0. Add it to the status buffer
            status_UART+=Generate_Status(rotate_status)+"\r\n"
            new_status=1 #we have new status
            rotating_arm=0 #we are done rotating
            configuring_arm=0 #we are done configuring
            initialize=0 #we are done intiializing
            #if it errors, we need to exit to stateQ
            if(rotate_status==-1):
                return stateQ
            #if we are capturing, it's time to start analyzing the debris
            if(capture_start==1):
                #so we go to the distance detection
                return stateF
            #if we aren't capturing, we must be plain initializing 
            else:
                #so we are good to move on to UART_Wait
                return stateB
        else:
            print("Initialization failure in stateE: ARD_Wait")
            return stateQ
    elif(capture_start==1):
        #in the capture sequence, we first rotate, then close. So that is the priority
        if(rotating_arm==1):
            rotate_status=rot_ARD_Read(ROTATE_OFFSET)
            #If we get here, we know status isn't gonna just be 0. Add it to the status buffer
            status_UART+=Generate_Status(rotate_status)+"\r\n"
            new_status=1 #we have new status
            rotating_arm=0 #we are done rotating
            configuring_arm=0 #we are done configuring
            #if it errors, we need to exit to stateQ
            if(rotate_status==-1):
                return stateQ
            #if we are capturing, we now need to close the claw
            return stateC
        elif(moving_arm==1):
            #remember that lin_ARD_Read returns an array of two integers
            move_status=lin_ARD_Read(MOVE_OFFSET)
            
            #In UART_Comms, we print out the status to UART, so we just need to update it based on what's returned
            #if pair0 and pair1 did stuff, we add that to the status_UART
            if(move_status[0]!=0):
                status_UART+=Generate_Status(move_status[0])+"\r\n"
            if(move_status[1]!=0):
                status_UART+=Generate_Status(move_status[1])+"\r\n"
            new_status=1            
            moving_arm=0 #need to set this back to 0 so we don't come here again
            capture_start=0 #we are done capturing!
            #if either status is -1 it is a fatal error so we will exit this program
            if(move_status[0]==-1 or move_status[1]==-1):
                return stateQ
            
            #if it didn't fail, we should've successfully captured the thing and we should be done, moving into UART_Wait
            return stateB
        else:
            print("Failure during capture in stateE: ARD_Wait")
            return stateQ
    elif(moving_arm==1):
        #remember that lin_ARD_Read returns an array of two integers
        move_status=lin_ARD_Read(MOVE_OFFSET)
        
        #In UART_Comms, we print out the status to UART, so we just need to update it based on what's returned
        #if pair0 and pair1 did stuff, we add that to the status_UART
        if(move_status[0]!=0):
            status_UART+=Generate_Status(move_status[0])+"\r\n"
        if(move_status[1]!=0):
            status_UART+=Generate_Status(move_status[1])+"\r\n"
        new_status=1            
        moving_arm=0 #need to set this back to 0 so we don't come here again
        
        #if either status is -1 it is a fatal error so we will exit this program
        if(move_status[0]==-1 or move_status[1]==-1):
            return stateQ
        
        #if it didn't fail, we move back to UART_Wait
        return stateB
    elif(rotating_arm==1):
        #lets get this rotate status
        rotate_status=rot_ARD_Read(ROTATE_OFFSET)
        #If we get here, we know status isn't gonna just be 0. Add it to the status buffer
        status_UART+=Generate_Status(rotate_status)+"\r\n"
        new_status=1 #we have new status
        rotating_arm=0 #we are done rotating
        configuring_arm=0 #we are done configuring
        #if it errors, we need to exit to stateQ
        if(rotate_status==-1):
            return stateQ
        #otherwise, we go back to UART_Wait
        return stateB
    else:
        #if we get here, we must've messed up somewhere with our flags being set.
        print("ERROR: Ard_Wait failed if elif statements")
        status_UART+=Generate_Status(-1)+"\r\n"
        new_status=1
    return stateQ
            

#Detecting_Distance
#I believe we just either go here from UART_Wait or from ARD_Wait, ARD_Wait if we are in capture_start==1
def stateF():        
    global detecting_distance
    
    if(capture_start==1):
        return stateG
    else:
        return stateB    

#Detecting_Object
        
    
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