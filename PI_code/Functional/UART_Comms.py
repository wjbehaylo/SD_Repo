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

#Global Variables

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
#if this is set to 0 in main, the loops would exit
test=1

#Flag to control main loop
is_running = True

def UART():
    #global variables
    global capture_start
    global initialize
    global program_quit
    global detecting_distance
    global detecting_object
    global moving_arm
    global move_amount
    global pair_select
    global rotating_arm
    global rotate_amount
    global configuring_arm
    global arm_configuration
    
    #will thread status_UART and check regularly
    global status_UART
    global new_status
    
    #for exiting loops when testing.
    global test
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
                
                ser.write(b"    (M): Move, followed by a value, actuate X steps (+ is closing, - is opening)\r\n")
                ser.write(b"    (O): Open, fully open the claw\r\n")
                ser.write(b"    (C): Close, fully close the claw\r\n\n")
                
                ser.write(b"    (R): Rotate, followed by a value, rotate X degrees\r\n") #degrees to steps conversion will be determined
                ser.write(b"    (=): Equals, rotates the claw into = configuration\r\n")
                ser.write(b"    (+): Plus, rotates the claw into the plus configuration\r\n\n")
            case 'S':
                #this case corresponds to the general capture process
                ser.write(b"Starting capture process\r\n")
                #this is a global flag that will be established, so that the other threaded process will know to start the process
                capture_start=1
                #it will be set back to 0 once capture is complete, at which point this while loop will stop
                while(capture_start==1 and test==1):
                    sleep(0.1)
                    #this if statement is just so that each state can still communicate through, even though the UART is doing what it is actively.
                    if(new_status==1):
                        ser.write(status_UART.encode("utf-8")+b"\r\n")
                        new_status=0
                test=1
                ser.write(b"Capture process finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
                    
            case 'I':
                #this case corresponds to the system being reset to its default, theoretically after a capture or on start up
                ser.write(b"Initializing system\r\n")
                initialize=1
                #now we wait for it to be finished initializng, which does include it going through a few states
                while(initialize==1 and test==1):
                    sleep(0.1)
                    #we check if any of these states have new status to mention
                    if(new_status==1):
                        ser.write(status_UART.encode("utf-8")+b"\r\n")
                        new_status=0
                test=1
                ser.write(b"Intialization process finished\r\n")
                
                #I don't think we need this here because we kind of gave out the status already?
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
                while(detecting_distance==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Distance detection finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'T':
                #this state has the CV detect the type of the object 
                ser.write(b"Detecting object\r\n")
                detecting_object=1
                while(detecting_object==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Object detection finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
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
                    pair_select=int(arm_sel)
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
                        moving_arm = 1
                        move_amount = x_int
                        break  # Exit loop since we got a valid integer
                    except ValueError:
                        #if we couldn't convert to int, we gotta do it again
                        ser.write(b"Invalid input. Please enter an integer.\r\n")
                    
                
                while(moving_arm==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
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
                    pair_select=int(arm_sel)
                    break
                
                ser.write(b"Opening claw\r\n")
                #note that this number will be positive or negative because of how we want to send it.
                #TBD pos or negative
                moving_arm=1
                move_amount=1000000 #undetermined positive or negative
                while(moving_arm==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
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
                    pair_select=int(arm_sel)
                    break
                
                ser.write(b"Closing claw\r\n")
                #note that this number will be positive or negative because of how we want to send it.
                #TBD pos or negative
                moving_arm=1
                move_amount=-1000000 #undetermined positive or negative
                while(moving_arm==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Claw movement finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case 'R':
                #this state has the motor move by a certain amount
                
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
                    x_int = int(move_message)  # Convert input to integer   
                    #that line was where the error would be, so at this point we know it was a proper thing
                    ser.write(b"Moving " + move_message.encode('utf-8') + b" steps\r\n")
                    moving_arm = 1
                    move_amount = x_int
                    break  # Exit loop since we got a valid integer
                except ValueError:
                    #if we couldn't convert to int, we gotta do it again
                    ser.write(b"Invalid input. Please enter an integer.\r\n")
                
                #now we wait for it to no longer be rotating
                while(rotating_arm==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Claw rotation finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case '=':
                ser.write(b"Rotating claw into = configuration\r\n")
                rotating_arm=1
                configuring_arm=1
                arm_configuration=0 #this is the configuration for the -
                while(rotating_arm==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Claw configuration finished\r\n")
                #status will be updated during the process
                #I am planning on status_UART being a string, so we need to encode it 
                ser.write(status_UART.encode("utf-8")+b"\r\n")
            case '+':
                ser.write(b"Rotating claw into + configuration\r\n")
                rotating_arm=1
                configuring_arm=1
                arm_configuration=1 #this is the configuration for the +
                while(rotating_arm==1 and test==1):
                    sleep(0.1)
                test=1
                ser.write(b"Claw configuration finished\r\n")
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
    
    
#This function is for the point of testing
def main():
    #let it warm up
    global is_running
    global test
    sleep(1)
    #setting up the thread for the UART
    UART_thread=threading.Thread(target=UART)
    UART_thread.start()
    while(UART_thread.is_alive()):
        sleep(1)
        test=0
        
    print("UART thread finished")

    sleep(1)
    try:
        while is_running:

            time.sleep(0.1)  # Main thread can handle other tasks if necessary
    except KeyboardInterrupt:
        is_running = False

if __name__ == "__main__":
    main()
