# Purpose: this is a functional file to demonstrate the various states the py will go through
# Contributors: Walter, Angela
# Sources: 
#   Based on programming used in SEED_LAB for python state machine
# Relevant files: 
# Circuitry: this is purely software


#In python, one way to implement state machines is through having a function for each state, 
#then, in a while loop, the program will execute certain things based on what the state variable is currently at. 
#the states/functions are defined as follows:
#Purpose: 
#   Purpose represents the main idea of what the state does in the program's execution
#Functionality:
#   This includes the various things that will be done during the state
#Transition:
#   This includes what conditions need to be met, and what state will be gone to next
#Thoughts:
#   This section is just for any thoughts currently had about the state

#The states are as follows:
#stateA is "Initializing"
#stateB is "UART_Wait"
#stateC is "Moving_Arm"
#stateD is "Rotating_Arm"
#stateE is "ARD_Wait"
#stateF is "Detecting_Distance"
#stateG is "Detecting_Object"
#stateH is "Data_Analysis"
#stateQ is "Quit"

#stateA is "Initializing". 
#Purpose: 
#   this is here to confirm the start up of the program and FSM.
#Functionality:
#   this will include making sure that the arduinos, camera, sensors, and UART are all connected. 
#Transition: 
#   It will transition to Moving_Arms, or Quit if the system doesn't work
#Thoughts:
#   This is kind of just a sanity check, it might send messages to other things to confirm the sending lines are open

#stateB is "UART_Wait"
#Purpose: 
#   this is here to signal where the system will be while it waits for UART communication to be sent
#Functionality:
#   this mostly determines what the next state will be based on the UART communication
#Transition: 
#   It will transition to a variety of states, including Moving_Arm, Rotating_Arm, Detecting_Object, Detecting_Distance, Capture_Start, and Quit
#Thoughts:
#   this is where the system is by default, theoretically while navigating to certain capture locations or whatever


#stateC is "Moving_Arm"
#Purpose:
#   This state is where the amount the arm is intended to move will be encoded into a message and sent to the Arduino
#Functionality:
#   Take the message sent, be it, M, O, C, or from the capture start, and send a command to the Arduino
#Transition:
#   This goes to ARD_Wait, while it waits for confirmation of the move
#Thoughts:
#   This is both an isolated functionality and a capture start thing

#stateD is "Rotating_Arm"
#Purpose:
#   This state is where the amount the arm is intended to rotate will be encoded into a message and sent to the Arduino
#Functionality:
#   Take the message sent, be it, R, +, = or from the capture start, and send a command to the Arduino about where it should rotate to
#Transition:
#   This goes to ARD_Wait, while it waits for confirmation of the rotation
#Thoughts:
#   This is both an isolated functionality and a capture start thing

#stateE is "ARD_Wait"
#Purpose:
#   This state is where the PI is waiting for the Arduino to send the status of its previous instruction
#Functionality:
#   Every so often (TBD) it will probe the Arduino to see the status of the previous task
#Transition:
#   This goes to a variety of places. Typically it goes to Quit or UART wait, and during capture it can go to Quit or whatever the next thing in the capture process is
#Thoughts:
#   This is pretty essential, based on the flags set (be it rotating, capturing, or whatever else) it determines what it will probe and what the message will signify.
#   This state will need to be dynamic, because the status register that is printed out varies depending on the result of the ARD_Wait. 
#   So for states like this the status will need to be determined based on the execution of the state

#stateF is "Detecting_Distance"
#Purpose:
#   This state is where the time of flight sensor is getting the distance of the object in front of it.
#Functionality:
#   Requests distance over I2C connection with time of flight sensor
#Transition:
#   this either goes back to UART_Wait, or it could go to Quit or detecting object
#Thoughts:
#   Fundamentally the way it works is the same, but it will have to set some global variable or something to record the distance when the data analysis is performed
#   There will be a bit of work between this and the detecting object state, in that the detecting object state might actually need to have this one go first to get the distance


#stateG is "Detecting_Object"
#Purpose:
#   This state is where the PI will use CV and the distance of the object to classify it as the Minotaur Rocket Body, 3U Cubesat, or Starlink Satellite
#Functionality:
#   Based on the distance to the object and the detected contours, the PI will sort it into three categories
#Transition:
#   This goes to a variety of places. Typically it goes to Quit or UART_wait, and during capture it can go to Quit or whatever the next thing in the capture process is
#Thoughts:
#   This is honestly the most complex state right now, at least the one with the least amount of stuff done for it.
#   The object will have to be classified which determines what will be sent to the Arduino, as it is a series of messages not just one.

#stateH is "Data_Analysis"
#Purpose:
#   Based on the Detecting_Object state's results, this state determines what will be sent to the Arduino with respect to how to move its arms
#Functionality:
#   Not actually sending the Arduino instructions, as that is done later, just determining what the instructions will be/are
#Transition:
#   This goes to Rotating_Arm, as the Arduino will need to move its arms to proper configuration
#Thoughts:
#   I think this makes sense as its own state, since it isn't done elsewhere
#   in the other scenarios, based on the value after M, O, or C, the amount to move the arm is determined, 

#stateQ is "Quit"
#Purpose:
#   This state is going to be gone to when the system is exited. Maybe also if there is some type of fatal error
#Functionality:
#   This will terminate any and all open lines of communication, and turn the system off wherever it currently is at
#Transition:
#   This state doesn't go to any other states, since it is the end of the program
#Thoughts:
#   This won't be super commonly done, I mean only once per execution obviously. 