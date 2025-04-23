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
#   This just has files in it


#   for the Pi, follow the circuitry outline in UART_Comms, VL53L0X-sensor-code, CameraCalibAndShapeDetection, and I2C_Arduino (exploration file)

#Arduino
from smbus2 import SMBus #this is to get the I2C connection functionality we want. We will need to run 
from time import sleep
from UART_Comms import UART #to get our UART Function
from ARD_Comms import * #importing all the ard functions
from Computer_Vision import * #importing the necessary computer vision functions
from Generate_Status import Generate_Status #for generating our status we will output
import globals

#UART
import threading
import serial

#These functions represent each of the states, with their transition logic present
#Note that in the state functions, all that matters is the transition logic, not the actual work.
#The actual work is done outside of this stuff, in the state machine

#Generally, when resetting you open first, then un rotate. When capturing, you rotate first, then close

#Initializing the system, this will start the camera and UART threads, after the start we won't actually go to this state though
def stateA():
    #starting UART thread. It is a daemon so that when this FSM program finishes executing it will be done to 
    
    #now make sure that all the threads are running properly
    sleep(30)
    
    if(globals.UART_running==False):
        print("UART thread not running")
        return stateQ
    if(globals.CV_running==False):
        print("CV thread not running")
        return stateQ
    if(globals.CAM_running==False):
        print("CAM thread not running")
        return stateQ
    
    #if all the threads are running, we should be good to start trying to run it
    print("Threads initialized")
    
    #I'm not sure what all we would want to make sure it is rotated to where it needs to be rotated to here
    #the threads should all be started
    return stateB

#UART_Wait
def stateB():
    
    #we want an infinite loop, as it waits on UART stuff to come through
    #theoretically only one of these should go to 1 in a single command
    # they should all properly be set to 0 after execution as well
    #does it matter if I have an infinite loop here instead of recursively calling this function again if none of the things are 0?
    while (True):
        #adding in sleep to avoid consuming all of CPU
        sleep(0.1)
        #the next state will be determined based on the set of variables in the UART module
        #generally, only one of these should be 1 when this statement comes up
        
        #we only want to try to access these when we can take uart_lock ourselves
        with globals.comms_lock:
            if(globals.moving_arm==1):
                return stateC #we are entering the moving arm state
            if(globals.rotating_arm==1):
                return stateD #we are rotating the arm by some amount
            if(globals.detecting_object==1):
                return stateF #we will be using CV to detect the object
            if(globals.program_quit==1):
                return stateQ #the program is exiting here
                
#Moving_Arm
#we either come here when initializing, capturing, moving an amount, opening, or closing
def stateC():
    
    #to start, I will create local copies of the important global variables
    with globals.comms_lock:
        my_pair_select=globals.pair_select
        my_move_amount=globals.move_amount
        
    OFFSET=my_pair_select
    #when we select O or C in UART we also set the move_amount
    lin_ARD_Write(OFFSET, my_move_amount)
    #moving arm is set to 1 in the UART thread, or the capture start or initialize, 
    
    #we are going to want to incldicate that we are going to move the arm, and in doing so update the status
    with globals.status_lock:
        globals.status_UART+=f"Moving arms\r\n\tpair_select={my_pair_select}\r\n"
        globals.new_status=1
    
    #we automatically go to the ARD_Wait state after this one
    return stateE

#Rotating_Arm
#we wither come here when initializing, capturing, rotating an amount, =, or + configuration
def stateD():
    #OFFSET is 0 when we are rotating a specific amount
    #OFFSET is 1 when we are going to = configuration
    #OFFSET is 2 when we are going to + configuration
    
    #these are temporary variables that will help so that I don't have to keep locking stuff
    #also note that at this point, these global things would've already been set in the UART_Comms thread
    with globals.comms_lock:
        my_configuring_arm = globals.configuring_arm
        my_arm_configuration=globals.arm_configuration
        my_rotate_amount=globals.rotate_amount
    #funny enough, configuring_arm + arm_configuration = OFFSET here.
    #these flags are all managed by the uart_lock
    OFFSET=0 + my_configuring_arm + my_arm_configuration
    
    #if we get here, we at least know that we are in the rotating_arm section
    rot_ARD_Write(OFFSET, my_rotate_amount)
    
    #we are going to indiciate that we are going to rotate the arm, and in doing so update the status
    with globals.status_lock:
        globals.status_UART+=f"Rotating arms"
        #add to it if we are actually configuring the arms
        if(my_configuring_arm==1):
            if(my_arm_configuration==0):
                globals.status_UART+=" to = configuration"
            elif(my_arm_configuration==1):
                globals.status_UART+=" to + configuration"
        globals.status_UART+="\r\n"
        globals.new_status=1

    #we will automatically go to ARD_Wait here.
    return stateE

#ARD_Wait
#this state is gone to after stateC (move) or stateD (rotate) or state_F (debris detect)
#we could go from here to UART_Wait, move, rotate, or detectDistance
def stateE():
   
    #we start off with getting local copies of the necessary variables
    with globals.comms_lock:
        my_moving_arm = globals.moving_arm
        my_rotating_arm = globals.rotating_arm
        my_pair_select = globals.pair_select
        
   
    #set the offsets that will be read from in either scenario
    MOVE_OFFSET=my_pair_select+3 #note that there is a +3 because when moving, our offset starts at 3, 4, 5 for pair0, pair1, pairboth, in terms of reading
    ROTATE_OFFSET=3 #we only read from the one location on the rotational one, so this is kinda unnecessary
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
    
    
    if(my_moving_arm==1):
        #remember that lin_ARD_Read returns an array of two integers
        move_status=lin_ARD_Read(MOVE_OFFSET)
        
        #In UART_Comms, we print out the status to UART, so we just need to update it based on what's returned
        #if pair0 and pair1 did stuff, we add that to the status_UART
        
        with globals.status_lock:
            if(move_status[0]!=0):
                globals.status_UART+=Generate_Status(move_status[0])+"\r\n"
            if(move_status[1]!=10):
                globals.status_UART+=Generate_Status(move_status[1])+"\r\n"
            globals.new_status=1
        
        #to make it so the other loop will exit
        with globals.comms_lock:            
            globals.moving_arm=0 #need to set this back to 0 so we don't come here again
        
        #if either status is -1 it is a fatal error so we will exit this program
        if(move_status[0]==-1 or move_status[1]==-1):
            return stateQ
        
        #if it didn't fail, we move back to UART_Wait
        return stateB
    
    elif(my_rotating_arm==1):
        #lets get this rotate status
        rotate_status=rot_ARD_Read(ROTATE_OFFSET)
        #If we get here, we know status isn't gonna just be 0. Add it to the status buffer
        with globals.status_lock:
            globals.status_UART+=Generate_Status(rotate_status)+"\r\n"
            globals.new_status=1 #we have new status
        #and get out of here
        with globals.comms_lock:
            globals.rotating_arm=0 #we are done rotating
            globals.configuring_arm=0 #we are done configuring
        #if it errors, we need to exit to stateQ
        if(rotate_status==-1):
            return stateQ
        #otherwise, we go back to UART_Wait
        return stateB
    else:
        #if we get here, we must've messed up somewhere with our flags being set.
        print("ERROR: Ard_Wait improperly called, not moving or rotating arms")
        with globals.status_lock:
            globals.status_UART+=Generate_Status(-1)+"\r\n"
            globals.new_status=1
    return stateQ
            

#Detecting_Object
#I believe we just either go here from UART_Wait or from ARD_Wait, ARD_Wait if we are in capture_start==1
#from cameraCalibAndShapeDetection import colorDetector #will have to move this over
def stateF(): 

    #we set this to 1 so that the CV will capture a frame and analyze it
    with globals.camera_lock:
        globals.run_CV = 1 
      
    #this loop just has us waiting here until the CV has been fully run  
    while(True):
        sleep(0.1)
        with globals.camera_lock:
            if(globals.run_CV!=1):
                break
        
    #when we exit this while loop, detected_debris_type should be set
    
    #at this point, detecting object should be true, so we want to resume/start the computer vision stuff
    #I will have a flag called CV_RUN that 
    # report back over UART
    if globals.detected_debris_type in ("CubeSat", "Starlink", "Minotaur"):
        globals.status_UART += f"Detected object: {globals.detected_debris_type}\r\n"
    else:
        globals.status_UART += "Detected object: UNKNOWN\r\n"
    
    globals.new_status = 1 #queue that message

    # set grip parameters based on the type
    #debugging, these aren't decided yet, might remove these
    if globals.detected_debris_type == "CubeSat":
        globals.pair_select = 0    # one claw only, unsure of amount
        globals.move_amount  = 13000
    elif globals.detected_debris_type == "Starlink":
        globals.pair_select = 2    # both claws, unsure of amount
        globals.move_amount  = 10000
    elif globals.detected_debris_type == "Minotaur":
        globals.pair_select = 2 #both claws, unsure of amount, 
        globals.move_amount = 10000
    
    #we are finished detecting the object
    globals.detecting_object = 0
    return stateB
    
    
    
def stateQ():
    print("Program terminated. Shutting down the system...")
    
    with globals.comms_lock:
        globals.program_quit = 0
        globals.SYS_running = False

        #close any open connections
        try:
            globals.i2c_arduino.close()
        except: 
            pass

    #function for stopping the camera?
    return stateQ
#At this point, we are actually in the program that will be running to execute it all.
