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

SENDING: these are things that will be written in the ARD_Write function
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
    
REQUESTING: every second or so, the Pi will try to read the arduino's register 0 to get the status
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

SENDING: things that will be written in the ARD_Write function
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

rot_ard_add = 8
lin_ard_add = 15

OFFSET = 

def ARD_Write(ADDRESS, OFFSET, MESSAGE):
    return
    
def ARD_Read(ADDRESS, OFFSET):
    MESSAGE=""
    return MESSAGE