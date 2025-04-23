# Purpose: this is a file that will have all the global variables in it
# Contributors: Walter, Angela
# Sources: 
#   From other files, all brought into here
# Relevant files: 
#   Many files use it, but it does not depend on any
# Circuitry: 
#   This just has files in it


from smbus2 import SMBus
import threading #so we can have the locks


#Global Variables for UART

#this is a flag to signal if the program should stop, it won't often be set
program_quit=0
#this is a flag to signal that we should determine the object type, things that matter
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
#this will be a flag to be set if there is new status during the process
new_status=0

#Variables for CV
#this will store the actual detected debris type
detected_debris_type=None
#this is a flag to signal between FSM_Actual and Computer_Vision that a new frame should be captured and object type determined
run_CV=0
#This is where the image is sent when it is passed between the functions
color_frame = None

#Variables for arduino
#I think these are global things that only really need to bein this file though? Maybe not in the case of like pair_select
i2c_arduino=SMBus(1) #Maybe I don't need to initialize this here? only in the top level?
rot_ard_add = 8
lin_ard_add = 15


#Locks: these are locks to manage communication between the threads
#This is a lock so that the function capturing images and the one analyzing them don't have race issues
frame_lock= threading.Lock()
#This lock manages the communication between UART and the FSM, including i2c type messages
comms_lock= threading.Lock()
#this lock manages actually writing and using the i2c bus
i2c_lock= threading.Lock()
#This lock is used when adding to vs writing the status
status_lock= threading.Lock()

#Flag to control main loop
#If this gets set to false, everything will end
SYS_running = True
#This is a flag to signal that the UART is running
UART_running = False
#this is a flag to signal that the camera thread is running
CAM_running=False
#this is a flag to signal that the CV is running
CV_running=False