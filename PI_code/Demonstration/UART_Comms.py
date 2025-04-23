# Purpose: this is a functional file to define functions related to UART communication
# Contributors: Walter
#Sources: 
# https://pyserial.readthedocs.io/en/latest/ Pi serial documentation
# https://pinout.ai/raspberry-pi-5 pinout on Pi 5
# Relevant files: 
# Exploration, UART_exploration.py
#Circuitry: 
# use the HiLetgo CP2102 USB converter with free cable, and the raspberry pi 5, and the wires. 
# pin 1 (top left, consider usb ports to be bottom of board) is 3.3V, connect to 3.3V on converter green
# pin 6 (third down on right) is ground, connect to ground on converter white
# pin 8, (fourth down on right) is GPIO14, TXD. Connect to RXD on converter purple
# pin 10, (fifth down on right) is GPIO15, RXD. Connect to TXD on converter blue

'''
Status: in this part I'll have information about the current status of the UART_Comms.py file

I think if the user tries to input a message longer than '1' into ser.readline(1) it breaks. I would go through and replace all of these then with the solution.
    maybe I need to use 'ser.read_until(b"\n") to just get the whole thing, 
    Then I could have it try and maybe fail to recognize the message, like multiple input characters just goes to the default case
    Or letters when I'm trying to do numbers would throw some type of exception that would require new input 
    I don't think this would be too complex, and could be a useful/good thing to do honestly, if it doesn't take too long. Not a priority though
    
I haven't made this threaded yet, and I know that I can send and receive the '?' message, but I haven't tried out the other ones.
    To test this, just remove the flags being set high and waiting to be set low, like the while loops.

Supposedly, ser.readline(1) isn't a real thing, and readline just takes in a line until the \n character is encountered
    I think it could be nice if every character that is read is printed out as it is typed, rather than relying on the \n to see what you've sent
    Maybe I could read each character one at a time, and continue while the character is not '\n'
    I am also unsure of what exactly my 'enter' key being pressed sends. It could be \r\n, or just \n. Because I'm on windows I think its \r\n
'''


#note that to properly run UART there is a specific TBD order that the pi and putty must be opened

import serial
import threading #for threaded UART connection
import time
from time import sleep
import globals #this declared the global variables that we will be using

def UART():
    #if there are other usb devices connected before this, you may have to replace 0 with 1, 2, or 3 I think. Otherwise just find which port it is. 
    ser = serial.Serial('/dev/ttyAMA0')

    #9600 would work theoretically, maybe if this doesn't we use that.
    ser.baudrate=9600
    #debugging print(ser.name)
    ser.timeout = None #keeps reading line of communication as open until the message is received

    #I don't know about how else I need to configure it in terms of stop bits and whatever, so I'll just go with the standard for now.

    #debugging
    if(ser.is_open):
        print("UART connection is open")
    else:
        print("Failure to open UART, exiting\r\n")
        return
    
    #this is for our stateA
    with globals.running_lock:
        globals.UART_running = True
        
        
    ser.write(b"Connection Established\r\n")
    #we only want messages of one bit at a time. We will have switch statement and output the confirmed message based on the input
    #We need the message in bytes, the message reinterpretted, and to send the message back
    message_bytes=ser.readline(1)
    message=message_bytes.decode('utf-8')
    ser.write(message_bytes+b"\r\n")

    print(message)
    #I had to change this from 'while message !=Q' to True, because when message = Q it will break out anyways, and otherwise we weren't getting what we needed
    while(True):
        match message:
            case '?':
                ser.write(b"Usage Guidelines:\r\nThe following is a list of possible one character messages that can be sent\r\n")
                ser.write(b"    (?): Help, prints out the Usage Guidelines\r\n\n")
                
                ser.write(b"    (M): Move, followed by a value, actuate X steps (+ is closing, - is opening)\r\n")
                ser.write(b"    (O): Open, fully open the claw\r\n")
                ser.write(b"    (C): Close, fully close the claw\r\n\n")
                
                ser.write(b"    (R): Rotate, followed by a value, rotate X degrees\r\n") #degrees to steps conversion will be determined
                ser.write(b"    (=): Equals, rotates the claw into = configuration\r\n")
                ser.write(b"    (+): Plus, rotates the claw into the plus configuration\r\n\n")
                
                ser.write(b"    (T): Type, output type of debris detected\r\n\n")
                ser.write(b"    (Q): Quit, terminates the serial connection\r\n\n")

            case 'Q':
                #this state, however infrequenctly used, will be to termiante the program's functionality and end the while loops
                ser.write(b"Quitting\r\n")
                
                #I'm pretty sure that this is just like a mutex: when uart_lock is available, we can execute the code, and it would update our variable
                with globals.comms_lock:
                    globals.program_quit=1
                #we want to exit this while loop, so that the connection gets closed
                sleep(1)
                break
            
            case 'T':
                #this state has the CV detect the type of the object 
                ser.write(b"Detecting object\r\n")
                #letting FSM know that we will be detecting object
                with globals.comms_lock:
                    globals.detecting_object=1
                    
                #waiting for detecting object to be completed
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        #if we are no longer rotating the arm, we can move on
                        if(globals.detecting_object != 1): 
                            break
                
                ser.write(b"Object detection finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                
                #status outputting
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status=0
                
            case 'M':
                #this state has the motor move by a certain amount
                
                #here, we get which motors to move
                while(True):
                    ser.write(b"Input which pair of arms you would like to move (0 is pair 0, 1 is pair 1, 2 is both pairs)\r\n")
                    arm_sel_bytes=ser.readline(1)
                    arm_sel=arm_sel_bytes.decode('utf-8')
                    ser.write(arm_sel_bytes+b"\r\n")
                    if(arm_sel!="0" and arm_sel!="1" and arm_sel!="2"):
                        ser.write(b"Invalid input\r\n")
                        continue
                    #if we are here, we know we have a valid selection and we can convert it to integer and move on
                    with globals.comms_lock:
                        globals.pair_select=int(arm_sel)
                    break
            
                #here, we get how much to move them by.
                #I decided they will move the same, so you can't move each motor a different amount simultaneously.
                while (True):
                    ser.write(b"Input an integer to specify number of steps (+ is closing, - is opening)\r\n")
                    move_message=""
                    x_bytes=ser.readline(1)
                    x=x_bytes.decode('utf-8')
                    ser.write(x_bytes)
                    print(x,end='')
                    
                    while(x!="\r"):
                        move_message+=x
                        x_bytes=ser.readline(1)
                        x=x_bytes.decode('utf-8')
                        ser.write(x_bytes)
                        print(x,end='')
                    #for newline
                    ser.write(b"\r\n")
                    print()

                    try:
                        x_int = int(move_message)  # Convert input to integer   
                        #that line was where the error would be, so at this point we know it was a proper thing
                        ser.write(b"Moving " + move_message.encode('utf-8') + b" steps\r\n")
                        with globals.comms_lock:
                            globals.moving_arm = 1
                            globals.move_amount = x_int
                        break
                    except ValueError:
                        #if we couldn't convert to int, we gotta do it again
                        ser.write(b"Invalid input. Please enter an integer.\r\n")
                #now we need to wait
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        #if we are no longer rotating the arm, we can move on
                        if(globals.moving_arm != 1): 
                            break
                
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                
                #now for the status part
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status = 0
                
            case 'O':
                #this state is just to fully open the arms
                
                #here, we get which motors to move
                while(True):
                    ser.write(b"Input which pair of arms you would like to open (0 is pair 0, 1 is pair 1, 2 is both pairs)\r\n")
                    arm_sel_bytes=ser.readline(1)
                    arm_sel=arm_sel_bytes.decode('utf-8')
                    ser.write(arm_sel_bytes+b"\r\n")
                    if(arm_sel!="0" and arm_sel!="1" and arm_sel!="2"):
                        ser.write(b"Invalid input\r\n")
                        continue
                    #if we are here, we know we have a valid selection and we can convert it to integer and move on
                    with globals.comms_lock:
                        globals.pair_select=int(arm_sel)
                    break
                
                ser.write(b"Opening claw\r\n")
                #note that this number will be positive or negative because of how we want to send it.
                #TBD pos or negative
                with globals.comms_lock:
                    globals.moving_arm=1
                    globals.move_amount=-16000 #undetermined positive or negative
                
                #now we wait for the movement to be done
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        #if we are no longer rotating the arm, we can move on
                        if(globals.moving_arm != 1): 
                            break
                
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status = 0
                
            case 'C':
                #this state is just to fully open the arms
                #here, we get which motors to move
                while(True):
                    ser.write(b"Input which pair of arms you would like to close (0 is pair 0, 1 is pair 1, 2 is both pairs)\r\n")
                    arm_sel_bytes=ser.readline(1)
                    arm_sel=arm_sel_bytes.decode('utf-8')
                    ser.write(arm_sel_bytes+b"\r\n")
                    if(arm_sel!="0" and arm_sel!="1" and arm_sel!="2"):
                        ser.write(b"Invalid input\r\n")
                        continue
                    #if we are here, we know we have a valid selection and we can convert it to integer and move on
                    with globals.comms_lock:
                        globals.pair_select=int(arm_sel)
                    break
                
                ser.write(b"Closing claw\r\n")
                #set the global flag
                with globals.comms_lock:
                    globals.moving_arm=1
                    globals.move_amount=16000 #undetermined positive or negative
                    
                #now we wait for that to be done
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        #if we are no longer rotating the arm, we can move on
                        if(globals.moving_arm != 1): 
                            break

                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status=0
                
            case 'R':
                #this state has the motor rotate by a certain amount
                #this while loop is for while we don't have a complete messsage
                while(True):
                    ser.write(b"Input an integer to specify number of degrees\r\n")
                    degree_message=""
                    r_bytes=ser.readline(1)
                    r=r_bytes.decode('utf-8')
                    ser.write(r_bytes)
                    print(r,end='')
                    
                    while(r!="\r"):
                        degree_message+=r
                        r_bytes=ser.readline(1)
                        r=r_bytes.decode('utf-8')
                        ser.write(r_bytes)
                        print(r,end='')
                    #for newline
                    ser.write(b"\r\n")
                    print()

                    try:
                        r_int = int(degree_message)  # Convert input to integer   
                        #that line was where the error would be, so at this point we know it was a proper thing
                        ser.write(b"Rotating " + degree_message.encode('utf-8') + b" degrees\r\n")
                        #need to make sure that the mutex is applied
                        with globals.comms_lock:
                            globals.rotating_arm = 1
                            globals.rotate_amount = r_int
                        # Exit loop since we got a valid integer
                        break
                    except ValueError:
                        #if we couldn't convert to int, we gotta do it again
                        ser.write(b"Invalid input. Please enter an integer.\r\n")
                
                #now we wait for it to no longer be rotating
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        #if we are no longer rotating the arm, we can move on
                        if(globals.rotating_arm != 1): 
                            break
                    
                ser.write(b"Claw rotation finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status=0
                
            case '=':
                ser.write(b"Rotating claw into = configuration\r\n")
                #First, we have to signal that we want to rotate
                with globals.comms_lock:
                    globals.rotating_arm=1
                    globals.configuring_arm=1
                    globals.arm_configuration=0 #this is the configuration for the =
                    
                #now, we need to wait for that rotation to be done
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        if(globals.rotating_arm != 1):
                            break
                
                ser.write(b"Claw configuration finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status = 0
                
            case '+':
                ser.write(b"Rotating claw into + configuration\r\n")
                #first, we need to get the mutex for uart communication setting these flags
                with globals.comms_lock:
                    globals.rotating_arm=1
                    globals.configuring_arm=1
                    globals.arm_configuration=1 #this is the configuration for the +
                    
                #then, we need to get the i2c mutex so that we can properly access the information
                while(True):
                    sleep(0.1)
                    with globals.comms_lock:
                        if(globals.rotating_arm != 1):
                            break    
                
                ser.write(b"Claw configuration finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it
                
                #now we need to get the mutex for the status so we can run it
                with globals.status_lock:
                    ser.write(globals.status_UART.encode("utf-8")+b"\r\n")
                    globals.status_UART=""
                    globals.new_status = 0
            case _:
                ser.write(b"Command "+message_bytes+b" not supported.\r\nPlease make a valid selection ('?' for help)\r\n")
        
        message_bytes=ser.readline(1)
        message=message_bytes.decode('utf-8')
        print(message)
        ser.write(message_bytes+b"\r\n")
    
    print("Exiting UART")
    globals.UART_running = False
    ser.close()