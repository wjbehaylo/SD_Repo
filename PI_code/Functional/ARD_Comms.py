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

#the I2C connection will be established in the main function, and accessed globally here
#This function just writes a message to the Arduinos
#   ADDRESS is the address being written to over I2C, 8 for rotational, 15 for linear
#   OFFSET is the offset that will be written to on the Arduino
#   MESSAGE is the message that will be written over the line, assume that it is here in string form and will need to be encoded 

'''
This is a python file with the ARDUINO communication protocol written out. One function writes the rotational number of degrees to the Arduino and the linear

**Note that any message of 0 or 10 will mean that the state of ARD_Wait is remained in
**Any message of 5 or 15 will mean the command was unrecognized, so the quit state would be gone to (or maybe UART_Wait if we want another chance)

'''

'''
Rotational Messages:
ADDRESS: rot_ard_add (8)

SENDING: these are things that will be written in the ARD_Write function. This happens in the Arduino's 'Receive' routine
OFFSET:
    0:
        rotate a number of degrees, specified in 'rotate_amount' global variable
        this could either be an integer number, or we could use IEEE 754 encoding to send over an accurate float if necessary
    1:
        send it to = configuration
        so the content shouldn't matter
    2:
        send it to + configuration
        so the content shouldn't matter again
    
REQUESTING: every second or so, the Pi will try to read the arduino's register 0 to get the status. This is the arduino's 'Request' routine
OFFSET:
0:
    we decided offset 0 is for general status, and there is enough flexibility to get many messages
Messages: These will communicate the status of the current operation, from Arduino to PI
    0:
        ARD still executing, no new status
        this will keep the read going
    1:
        rotation success
    2:
        configuration success
    3:
        (0) end stop hit
    4:
        (90) end stop hit      
    5:
        Unrecognized command, Arduino doesn't know how to respond  

'''

'''
LINEAR MESSAGES:
ADDRESS: lin_ard_add (15)

SENDING: things that will be written in the ARD_Write function, this is receiving on the arduino's side
OFFSET:
    **Note that for any of these, either arms movement will be stopped by its respective end stops being contacted, or the force sensors**
    0:
        move pair0 by the number of steps stored in move amount. Sends over in IEEE754
    1:
        move pair1 by the number of steps stored in move amount. Sends over in IEEE754
    2:
        move both of the arm pairs by the number of steps stored in move amount. Sends over in IEEE754


REQUESTING: this will be the messages communicated from the ARDUINO to the PI regarding linear movement.

Note if the message is 5 or 15, regardless of offset, that the FSM will be moving out of ARD_WAIT and
OFFSET:
    0:
        This is just about pair0 movement
        Messages:
            0:
                Still moving/completing task
            1:
                Movement complete, no end stops or force sensors
            2:
                Fully open end stop triggered
            3:
                Fully closed end stop triggered
            4:
                Force sensor triggered
            5:
                Unrecognized movement command, could be due to incomplete or corrupt data
                
    1:
        This is just about pair1 movement
        Messages:
            0:
                Still moving/completing task
            1:
                Movement complete, no end stops or force sensors
            2:
                Fully open end stop triggered
            3:
                Fully closed end stop triggered
            4:
                Force sensor triggered
            5:
                Unrecognized movement command, could be due to incomplete or corrupt data

    2:
        This is for both arm movement. I based these messages on a combination of the ones for individual pairs, hence the out of order nature.
        Note that for this, It needs to wait for both arms to be finished in one way or another to continue.
        Also note that there are force sensors for each pair, likely on one arm because of their parallel closure.
        I think that I will just have the system waiting on two bytes for this offset, one byte for the message from each motor.
        The bytes will be interpretted as separate integers. 
        These messages are per byte, so we would theoretically not be getting both a sub10 one (pair0) and a larger than 10 one (pair1)
        Messages:
            0:
                Pair 0 Still moving/completing task
            1:
                Pair 0 Movement complete, no end stops or force sensors
            2:
                Pair 0 Fully open end stop triggered
            3:
                Pair 0 Fully closed end stop triggered
            4:
                Pair 0 Force sensor triggered
            5:
                Pair 0 Unrecognized movement command. 
                
            10:
                Pair 1 Still moving/completing task
            11:
                Pair 1 Movement complete, no end stops or force sensors
            12:
                Pair 1 Fully open end stop triggered
            13:
                Pair 1 Fully closed end stop triggered
            14:
                Pair 1 Force sensor triggered
            15:
                Pair 1 unrecognized movement command
                
    
'''

i2c_arduino=SMBus(1)
pair_select=0
rot_ard_add = 8
lin_ard_add = 15

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
#if this function returns a -1, it means the data wasn't written
#if it returns a 0, it was successfully written
def lin_ARD_Write(OFFSET, MESSAGE):
    #here message will be an integer, and we need to convert it into an array of 4 binary bytes the arduino will then interpret
    linear_array=Generate_IEEE_vector(MESSAGE)
    #OFFSET=0 means we are writing to pair0, OFFSET=1 means we are writing to pair1, OFFSET=2 means we are writing to both pairs.
    #This will be passed as input to this function though
    try:
        i2c_arduino.write_i2c_block_data(lin_ard_add, OFFSET, linear_array)
        sleep(0.1)
    except IOError:
        print("Could not write data to the Arduino")
        return -1
    return 0

def lin_ARD_Read(OFFSET):
    while True:
        try:
            #read block of data from arduino reg based on arduino's offset
            sleep(1)
            if OFFSET == 0 or OFFSET == 1:
                status = i2c_arduino.read_byte_data(lin_ard_add, OFFSET)
                print(f"Pair {OFFSET} Status: {status}")

                #interpret the status 
                #note that this is just for debugging, the function will return the actual value
                if status == 0:
                    print(f"Pair {OFFSET} Still moving/completing task")
                    continue
                elif status == 1:
                    print(f"Pair {OFFSET} Movement complete, no end stops or force sensors")
                elif status == 2:
                    print(f"Pair {OFFSET} Fully open, end stop triggered")
                elif status == 3:
                    print(f"Pair {OFFSET} Fully closed, end stop triggered")
                elif status == 4:
                    print(f"Pair {OFFSET} Force sensor triggered")
                elif status == 5:
                    print(f"Pair {OFFSET} Unrecognized movement command")
                else:
                    print(f"Pair {OFFSET} Unknown status")
                #if we get to this point we haven't continued so we have the status
                break
            elif OFFSET ==2:
                status = i2c_arduino.read_block_data(lin_ard_add, OFFSET, 2)
                #status 0 
        except IOError:
            print("Could not read from Arduino")
            
        
        except IOError:
            
                


    return


#The offset varies depending on a few global variables: rotating_arm, configuring_arm, arm_configuration
#If configuring_arm=0, offset=0
#if configuring_arm=1 and arm_configuration=0, offset=1
#if configuring_arm=1 and arm_configuration=1, offset=2

#if this returns a 1, it means data wasn't written
#if it returns a 0, data was written successfully
def rot_ARD_Write(OFFSET, MESSAGE):
    #first we need to convert the integer message
    rotational_array=Generate_IEEE_vector(MESSAGE)
    try:
        i2c_arduino.write_i2c_block_data(rot_ard_add, OFFSET, rotational_array)
        sleep(0.1)
    except IOError:
        print("Could not write data to the Arduino")
        return -1
    return 0
    
    
#OFFSET here will always be 0, since there weren't enough other locations to warant it
#This returns -1 on failure, 0 on success
def rot_ARD_Read(OFFSET):
    try:
        while True:
            sleep(1)
            if(OFFSET==0):
                status=i2c_arduino.read_byte_data(rot_ard_add, OFFSET)
                print(f"Status: {status}")
                if(status==0):
                    print("Still rotating")
                    continue
                elif(status==1):
                    print("Rotation success")
                elif(status==2):
                    print("Configuration success")
                elif(status==3):
                    print("0 degrees, endstop triggered")
                elif(status==4):
                    print("90 degrees, endstop triggered")
                elif(status==5):
                    print("Unrecognized command")
                else:
                    print("Unknown status")
                #if we get here, the movement has finished
                break
            else:
                print("Unknown offset")
                break
        return status
    except IOError:
        print("Could not read data from the Arduino")
        return -1

        

def main():
    OFFSET = 0  # reading the general status (OFFSET 0)
    global i2c_arduino
    i2c_arduino=SMBus(1)
    while True:
        linear_result = lin_ARD_Read(OFFSET)
        if ieee_vector:
            print(f"IEEE Vector: {ieee_vector}")
        
        # Wait 1 second before trying again
        sleep(1)

if __name__ == '__main__':
    main()

