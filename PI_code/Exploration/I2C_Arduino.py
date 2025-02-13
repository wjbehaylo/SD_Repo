# Purpose: this is an exploration file to set up the Raspberry Pi to Arduino I2C sending and receiving
# Contributors: Walter
# Sources: SEED_LAB repository for previous examples, install for SMBus2https://pypi.org/project/smbus2/ Documentation for smbus2 https://smbus2.readthedocs.io/en/latest/
# Relevant files: this file is related to the I2C_Pi file located in ARD_code.
# Circuitry: connect the following listed pins
#   A4 is SDA on Arduino, second pin from top on left (03) is SDA on Pi,
#   A5 is SCL on Arduino, third pin from top on left (05) is SCL on Pi,
#   GND on Arduino to fifth pin from top left (09) on Pi.

from smbus2 import SMBus #this is to get the I2C connection functionality we want. We will need to run 
from time import sleep
# I2C address of the Arduino. I2C starts off by clarifying what is to be written to, then writing there.
ARD_ADDR = 8
# Initialize SMBus library with I2C bus 1. The Pi has 2 I2C busses it can connect, this is just saying we are using the first I believe.
i2c_arduino = SMBus(1)

#offset represents which register will be written to on the arduino. Different registers might store different things based on mode of operation.
#for instance, register 16 might be the I2C message pertaining to the rotation that should be gone to, whereas register 15 might have the amount to close the arms and register 14 might signify that capture is going
#for now, we are just testing sending one message and we want to experiment with where to send it.
write_offset=int(input("Enter an offset to write to. 1 to write pin, 2 to write string: "))

#this is the actual message that will be sent. 32 characters or less because 32 bytes send in one block.
# if writing the led pin, send a 0 for off, send a 1 for on
write_string=input("Enter a string of 32 characters or less: ")

#this is just a sanity check on what is trying to be sent
#Also, I'm pretty sure that the '+' sign makes its own space, but I might have to add one in.
print("sending "+ write_string)

#the 'ord' function takes in a byte in the form of a character or length 1 string, and returns the unicode value
#obviously, we are sending these in byte packages so we need to send them as their unicode values. 
#the [] around the value of the message variable signifies that it will be an array, with an element for each character in the string being sent
#this could be different types of things if we wanted to send pure numbers, in which case the byte values would be configured accordingly
write_message= [ord(character) for character in write_string]

#here we actually try to send the data over the line.
#note that we threw it in a try except statement to indicate if the sending was successful from the Pi side of it
try:
    i2c_arduino.write_i2c_block_data(ARD_ADDR, write_offset, write_message)
except IOError:
    print("Could not write to the Arduino")

#sanity check
print("sending complete")

#it would be easy to extend this to send bytes, all we would need to do is make message an integer input, potentially -128 - 127 to be sent with a byte
#then, we would just use 'i2c_arduino.write_byte_data(ARD_ADDR, offset, command)'

#this is just waiting for the user to try to get a message from the arduino side of things
#For simplicity, this will just be a byte
#note that this is not wrapped in a 'try-except' block, but it could be if that is deemed necessary and easy enough. It will be actually, just not right now.

#now that we know the length of the message, which I'm still not sure if we needed or not, but is still useful. We now need where the message starts
read_message_offset=int(input("Enter an offset to read from:"))
read_message=i2c_arduino.read_byte_data(ARD_ADDR,read_message_offset)

#now we will print the length and location of the message, following by the message itself
print("We read a byte from offset "+str(read_message_offset)+" of the Arduino:")
print(read_message)

#closing message
print("This program is finished running now")
i2c_arduino.close() #probably best practice
