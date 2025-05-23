# Purpose: this is a functional file to set up the Raspberry Pi to Arduino I2C sending and receiving
# Contributors: Walter, Angela
# Sources: SEED_LAB repository for previous examples, install for SMBus2https://pypi.org/project/smbus2/ Documentation for smbus2 https://smbus2.readthedocs.io/en/latest/
# Relevant files: this file is related to the I2C_Pi file located in ARD_code.
# Circuitry: connect the following listed pins
#   A4 is SDA on Arduino, second pin from top on left (03) is SDA on Pi,
#   A5 is SCL on Arduino, third pin from top on left (05) is SCL on Pi,
#   GND on Arduino to fifth pin from top left (09) on Pi.

from smbus2 import SMBus #this is to get the I2C connection functionality we want. We will need to run 
from time import sleep
import numpy as np
from Generate_Status import Generate_Status #For the generation of status strings
import globals #this declared the global variables that we will be using

#the I2C connection will be established in the main function, and accessed globally here
#This function just writes a message to the Arduinos
#   ADDRESS is the address being written to over I2C, 8 for rotational, 15 for linear
#   OFFSET is the offset that will be written to on the Arduino
#   MESSAGE is the message that will be written over the line, assume that it is here in string form and will need to be encoded 

'''
This is a python file with the ARDUINO communication protocol written out. 
There are 4 functions, one for reading or writing to each arduino.
These functions are expected to read the value and return it, as well as output to the Python's stdout with print for debugging

For the purpose of generating the UART_status string, no two status values are the same.
This enables the value to be passed into a large if else function. 

Note that status is output only at the end of a function once it is called
Thus, there is no need for a default or anything, as there will always be a status when the function is called.

**Note that any message ending in 0 will mean that the state of ARD_Wait is remained in
**Ending in 5 will mean the command was unrecognized

'''

'''
LINEAR MESSAGES:
ADDRESS: lin_ard_add (15)

SENDING: things that will be written in the ARD_Write function, this is receiving on the arduino's side
OFFSET:
    **Note that for any of these, either arms movement will be stopped by its respective end stops being contacted, or the force sensors**
    0:
        move pair0 by the number of steps stored in move amount. Sends over in IEEE
    1:
        move pair1 by the number of steps stored in move amount. Sends over in IEEE
    2:
        move both of the arm pairs by the number of steps stored in move amount. Sends over in IEEE


REQUESTING: this will be the status communicated from the ARDUINO to the PI regarding linear movement.
Note that this function, lin_ARD_Read, returns a two element array.
OFFSET:
    3:
        This is just about pair0 movement
        Status:
            0:
                pair0 Still moving/completing task
            1:
                pair0 Movement complete, no end stops or force sensors
            2:
                pair0 Fully open end stop triggered
            3:
                pair0 Fully closed end stop triggered
            4:
                pair0 Force sensor triggered
            5:
                pair0 Unrecognized movement command, could be due to incomplete or corrupt data
                
    4:
        This is just about pair1 movement
        Status:
            10:
                pair1 Still moving/completing task
            11:
                pair1 Movement complete, no end stops or force sensors
            12:
                pair1 Fully open end stop triggered
            13:
                pair1 Fully closed end stop triggered
            14:
                pair1 Force sensor triggered
            15:
                pair1 Unrecognized movement command, could be due to incomplete or corrupt data

    5:
        This is for both arm movement. 
        Note that for this, each of the output bytes will be set to non-10 divisible values, meaning they will both contribute to UART status when checked
        
        the two different numbers representing the status of the pairs will be sent individually, and interpretted individually
        so there are technically 36 options (6 * 6 cause each has 6), but I'm not going to write them all here.
        On the Pi's side of the communication, there will have to be some thinking based on global flags to properly interpret the status
        Status:
            0:
                pair0 Still moving/completing task
            1:
                pair0 Movement complete, no end stops or force sensors
            2:
                pair0 Fully open end stop triggered
            3:
                pair0 Fully closed end stop triggered
            4:
                pair0 Force sensor triggered
            5:
                pair0 Unrecognized movement command, could be due to incomplete or corrupt data
            10:
                pair1 Still moving/completing task
            11:
                pair1 Movement complete, no end stops or force sensors
            12:
                pair1 Fully open end stop triggered
            13:
                pair1 Fully closed end stop triggered
            14:
                pair1 Force sensor triggered
            15:
                pair1 Unrecognized movement command, could be due to incomplete or corrupt data
'''
'''
Rotational Messages:
ADDRESS: rot_ard_add (8)

SENDING: these are things that will be written in the ARD_Write function. This happens in the Arduino's 'Receive' routine
OFFSET:
    0:
        rotate a number of degrees, specified in 'rotate_amount' global variable
        this could either be an integer number, or we could use IEEE encoding to send over an accurate float if necessary
    1:
        send it to = configuration
        so the content shouldn't matter
    2:
        send it to + configuration
        so the content shouldn't matter again
    
REQUESTING: every second or so, the Pi will try to read the arduino's register 0 to get the status. This is the arduino's 'Request' routine
OFFSET:
3:
    we decided offset 3 is for general status, and there is enough flexibility to get many messages. I think there is a problem with having this be 0 and the other too.
Status: 
    20:
        Rotating
    21:
        Rotation success
    22:
        configuration success
    23:
        (0) end stop hit
    24:
        (90) end stop hit      
    25:
        Unrecognized command, Arduino doesn't know how to respond  

'''



def Generate_IEEE_vector(value):   
    #np.float32(value) turns the value into a 32 bit numpy floating point 
    #.view("I") makes it interpretted as an unsigned integer
    #bin()[2:] converts the number into binary, and removes the 0b prefix
    #.zfill(32) makes sure it is 32 bits
    value_32_bits = bin(np.float32(value).view("I"))[2:].zfill(32)
    #splits up the 32 bits into 4 8 bit sections
    byte1 = value_32_bits[:8]
    byte2 = value_32_bits[8:16]
    byte3 = value_32_bits[16:24]
    byte4 = value_32_bits[24:]
    #turns each of the 4 8 bit sections into an integer, from binary
    byte1_val = int(byte1, 2) 
    byte2_val = int(byte2, 2) 
    byte3_val = int(byte3, 2)
    byte4_val = int(byte4, 2)
    
    #returns a vector of the 4 bytes to be written
    return [byte1_val, byte2_val, byte3_val, byte4_val]


#OFFSET determines which pair we are moving: 0 is pair0, 1 is pair1, 2 is both pairs. Passed in from global pair_select
#MESSAGE is just going to be passed from the value in the global variable move amount
#if this function returns a '-1', it means the data wasn't written
#if it returns a 0, it was successfully written
def lin_ARD_Write(OFFSET, MESSAGE):
    #here message will be an integer, and we need to convert it into an array of 4 binary bytes the arduino will then interpret
    linear_array=Generate_IEEE_vector(MESSAGE)
    #OFFSET=0 means we are writing to pair0, OFFSET=1 means we are writing to pair1, OFFSET=2 means we are writing to both pairs.
    #This will be passed as input to this function though
    try:
        with globals.i2c_lock:
            globals.i2c_arduino.write_i2c_block_data(globals.lin_ard_add, OFFSET, linear_array)
            #debugging. might be necessary though also
            sleep(0.1)
    except IOError:
        print("Could not write data to the Arduino")
        return -1
    return 0

#This function reads from the target offset of the Arduino
#It will return the status of the movement.
def lin_ARD_Read(OFFSET):
    
    status=[0,10] #first is status of pair0, second is status of pair1
    try:
        while True:
            #debugging
            #print("Trying to lin_ARD_Read again")
            #print(f"Offset is: {OFFSET}")
            
            #debugging, setting it to 10 for now so that there is a lesser chance of the timing issue
            sleep(1)
            
            #read block of data from arduino reg based on arduino's offset. Note that we will always read two bytes of data
            if (OFFSET == 5 or OFFSET == 4 or OFFSET == 3):
                #read 2 bytes,1 for each pair.
                #The return of the function here will be
                with globals.i2c_lock:
                    status = globals.i2c_arduino.read_i2c_block_data(globals.lin_ard_add, OFFSET, 2)
                
                
                
                # Break if the status of each pair is nonzero. Otherwise, one is still executing
                
                #based on the offset, different ones need to be nonzero to indicate completion
                if(OFFSET==5 and status[0] != 0 and status[1] != 10):
                    return status
                if(OFFSET==4 and status[1] != 10):
                    return status
                if(OFFSET==3 and status[0] != 0):
                    return status
                
                    
                
            else:
                print(f"Invalid OFFSET {OFFSET}")
                status[0] = -1
                status[1] = -1
                return status
            
    except IOError:
        print("Could not read from Arduino")
        status[0] = -1
        status[1] = -1
        return status


#The offset varies depending on a few global variables: rotating_arm, configuring_arm, arm_configuration
#If configuring_arm=0, offset=0
#if configuring_arm=1 and arm_configuration=0, offset=1
#if configuring_arm=1 and arm_configuration=1, offset=2

#if this returns a -1, it means data wasn't written
#if it returns a 0, data was written successfully
def rot_ARD_Write(OFFSET, MESSAGE):
    #first we need to convert the integer message
    rotational_array=Generate_IEEE_vector(MESSAGE)
    try:
        with globals.i2c_lock:
            globals.i2c_arduino.write_i2c_block_data(globals.rot_ard_add, OFFSET, rotational_array)
        sleep(0.1)
    except IOError:
        print("Could not write data to the Arduino")
        return -1
    return 0
    
    
#OFFSET will always be 0 here, if this works correctly
def rot_ARD_Read(OFFSET):
    try:
        while True:
            sleep(1)
            
            if(OFFSET==3):
                #debugging
                #print("Trying to read byte data")
                with globals.i2c_lock:
                    status=globals.i2c_arduino.read_byte(globals.rot_ard_add) #I don't think I needed the offset thing.
                
                #debugging
                #print("Successfully read byte data")
                #print(f"Status: {status}")
                if(status==20):
                    #debugging
                    #print("Still rotating")
                    continue
                #else:
                    #lowkey debugging? not super necessary
                    #print(Generate_Status(status))
                #if we get here, the movement has finished
                break
            else:
                print("Unknown offset")
                #-1 will be the status of failure I think.
                return -1
        return status
    except IOError:
        print("Could not read data from the Arduino")
        return -1
