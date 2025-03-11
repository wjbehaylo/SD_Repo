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
#this will be a flag to be set if there is new status to be output
new_status=0


#Global variables for Arduino Communications
#establishes what bus to be communicated over
i2c_arduino=SMBus(1)
#establishes the address of each arduino
rot_ard_add=8
lin_ard_add=15



#This threaded function, which may later be separated so that it isn't had here, contains the UART functionality
def UART():
    #global variables
    global capture_start
    global initialize
    global program_quit
    global detecting_distance
    global detecting_object
    global moving_arm
    global move_amount
    global rotating_arm
    global rotate_amount
    global configuring_arm
    global arm_configuration
    
    global status_UART
    global new_status
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
                
                ser.write(b"    (S): Start, begins the standard capture process\r\n") #note that there isn't a state for this, since it just sets the capture_start flag to be 1 then goes to resetting
                ser.write(b"    (I): Initialize, resets the system to default configuration\r\n")
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
                    #this if statement is just so that each state can still communicate through, even though the UART is doing what it is actively.
                    if(new_status==1):
                        ser.write(status_UART.encode("utf-8")+b"\r\n")
                        new_status=0
                ser.write(b"Capture process finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
                    
            case 'I':
                #this case corresponds to the system being reset to its default, theoretically after a capture or on start up
                ser.write(b"Initializing system\r\n")
                initialize=1
                while(initialize==1):
                    sleep(0.1)
                    if(new_status==1):
                        ser.write(status_UART.encode("utf-8")+b"\r\n")
                        new_status=0
                ser.write(b"Intialization process finished\r\n")
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
            case _:
                ser.write(b"Command "+message_bytes+b" not supported.\r\n Please make a valid selection ('?' for help)\r\n")
        
        message_bytes=ser.readline(1)
        message=message_bytes.decode('utf-8')
        print(message)
        ser.write(message_bytes+b"\r\n")
    ser.close()
    
#This function will be called when it is desired that information is written to the Arduino(s)
def ARD_Write(ADDRESS, OFFSET, MESSAGE):
    print("Writing to Arduino")

#This function will be called when it is desired that information (like status) is read from the Arduinos
def ARD_Read(ADDRESS, OFFSET):
    print("Reading from Arduino")
    MESSAGE=""
    return MESSAGE

#These functions represent each of the states, with their transition logic present
#Note that in the state functions, all that matters is the transition logic, not the actual work.
#The actual work is done outside of this stuff, in the state machine
#Initializing
def stateA():
    global moving_arm
    global move_amount
    global configuring_arm
    global arm_configuration
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
def stateC():
    global lin_ard_add
    global move_amount
    OFFSET=0 #undetermined for now, theoretically it could relate to which pair of arms is moving
    ARD_Write(lin_ard_add, OFFSET, move_amount)
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