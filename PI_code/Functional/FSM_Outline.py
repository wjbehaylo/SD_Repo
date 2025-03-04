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


#stateA is "initializing". 
#Purpose: 
#   this is here to confirm the start up of the program and FSM.
#Functionality:
#   this will include making sure that the arduinos, camera, sensors, and UART are all connected. 
#Transition: 
#   It will automatically transition to stateB on success, and stateQ if the system doesn't work
#Thoughts:
#   This is kind of just a sanity check, it might send messages to other things to confirm the sending lines are open
def stateA():
    return stateB

#stateB is "waiting to start"
#Purpose:
#   This state just is waiting for the external computer to send information over UART to signify program start
#Functionality:
#   Wait for a message to be sent over UART to signify start
#Transition:
#   If a message was sent and it is our desired message, transition to stateC
#   If no message is sent, or it isn't the desired one, remain in this state
#Thoughts:
#   Different messages could mean various different things, I'm not sure what we will be sending yet.
#   It would be cool if we could just message the Pi like "+ configuration" or "= configuration" or "Full close" and stuff like that, and it would tell the Arduino
#       We could very simply demonstrate individual parts of the process as well. So maybe the 'message' that is sent is just in a global buffer that gets sent out whenever we are in the send state
#       Then the message we get could be what we are supposed to send to the Arduino, so even if it is one character it would have tons of possibilities
#       I know that Noah Kelly programmed the steppers to turn as a function of distance and stuff, maybe then that function is what would be called?
def stateB():
    return stateC

#stateC is "confirming Send"
#Purpose:
#   This state is the pi communicating externally to the computer that the UART connection is sound and the capture process will begin
#Functionality:
#   This will send a UART message back to the host computer, indicating that the procedure is starting
#Transition:
#   This state will go to Arduino start if everything is alright, otherwise it will go to stateQ
#Thoughts:
#   How often should we send stuff back to the base?

#stateD is "Arduino Start" **ARDUINO SEND**
#Purpose:
#   This state is where the Pi tells the arduinos that they should configure themselves for capture to begin.
#Functionality:
#   The arduino's will just be waiting until this point, so here the Pi sends an I2C message to them to tell them to start
#   Also, in theory they may be in launch configuration or something so this sets them back to resting position
#Transition:
#   After this, I think the Arduinos will be moving. So we will move to the state where we wait for them to be done moving.
#Thoughts:
#   In theory, here we could begin the scanning for the debris, so that this goes faster and functions while the Motors are moving
#   However, time isn't really a concern and so we might not need to worry about it. Also maybe the arms would get in the way of the debris or something
#   Also though, maybe we might be worried about having multiple things using the I2C bus at the same time, so splitting it up could be good
#       Maybe even into the movement of individual arduinos

#stateE is "Arduino Wait" **ARDUINO WAIT**
#Purpose:
#   Wait for I2C from Arduinos to confirm that they are reset and ready to move
#Functionality:
#   I think that this will just periodically request I2C info from the Arduinos, maybe like every 10 seconds or so(?), and the Arduino will have a message to signal done
#Transition:
#   Another error checking moment, if the arduino's send back an error message (maybe 0 is waiting, 1 is success, 2 is error) we go to stateQ
#   If there is no error, we will begin scanning the debris to identify its type and shape in 'Scanning Debris' state
#Thoughts:
#   Maybe we could speed this up by also capturing data during this time. If that wouldn't mess anything up.

#stateF is "Scanning Debris"
#Purpose:
#   We have the camera which will get an image, and the time of fligth sensor which will get distance to the debris. This state is when that data will be acquirred.
#Functionality:
#   The state will send a request to the I2C time of flight sensor to ask for a distance reading, and do IMshow on the camera as well.
#Transition:
#   This will be done once the debris has been scanned, and will move to 'Data Analysis' state.
#Thoughts:
#   In typical control unit and datapath architecture, the control unit just tells the datapath what to do
#   So maybe, in this state, the data analysis would also be done, but I suppose maybe not?
#   In the datapath would there be a global status word control bit to signify that the analysis was complete?

#stateG is "Data Analysis"
#Purpose:
#   Data is captured from sensors. Now it needs to be analyzed to inform motor movements. 
#Functionality:
#   This will be the main CV area. OpenCV will be used to classify the debris based on its shape and size, with size gained through trigonometry using the TOF sensor
#   We will determine the following information based on our data analysis. If any one is not possible, we may need to restart the process.
#       Based on shape we will know what configuration to be in (+ or =)
#       Based on orientation we will know if the detumbling and navigation were a success
#       Based on size we will know how far to close the arms
#       Based on distance we will know if we are in range
#Transition:
#   Another error check, if any of the 'based on' statements above are inconclusive, we will set error flags and information and go to stateQ
#       Note that in stateQ, the messages sent back to the computer will be based on what errors occurred in operation
#   Otherwise, if we are properly prepared, we will send information to the Arduino in "Arduino Capture Message" state
#Thoughts:
#   This is the state we currently have the least amount of stuff for, being totally honest
#   Because of how many ways we could go to the quit state, (stateQ), this part gave me the idea to set global flags of like status word, so that when stateQ is entered it can say what went wrong

#stateH is "Arduino Capture Message" **ARDUINO SEND**
#Purpose:
#   The way that the arduino needs to capture the debris has been determined from previous states. Now the Arduino needs to be informed of this.
#Functionality:
#   Sending over I2C, this state will first message the rotational Arduino, saying to go to = configuration or + configuration. 
#   Then, it would tell the claw how far to close. 
#       Maybe this could have the point that could be closed to fast, before first contact was made, as well as how far after that it needs to close.
#       This would mean that in the future we could extend it to have the locking mechanism or whatever
#Transition:
#   This transitions into "Arduino capture Wait", where it is waiting for the Arduino to confirm the object's capture
#Thoughts:
#   This could be simplified into an Arduino Receive state. Maybe there should be a way for the host computer to abort processes, so the UART needs to be threaded?

#stateI is "Arduino Capture Wait" **ARDUINO RECEIVE**
#Purpose:
#   The arduino has tried to capture the thing now, so we will see if it is successful or not. 
#Functionality:
#   Periodically requesting over I2C, waiting for confirmation of capture.
#Transition:
#   stateQ on failure, or success. The differenec is what flags it raises.
#Thoughts:
#   This is the final state in the Capture process, as we wait to see if the Arduino captured it successfully or not yet.
#   This makes me believe even moreso that we should modularize this more, with arduino send and receive as functions that are called based on the state with their own parameters.
#   We would also have a wider range of UART possibilities, and that could set its own flags up and down and whatnot.
#   I still think the initial thing should totally be resetting it to true 0, but it doesn't necessarily absolutely have to be.
#   Should we have each pair of arms directable on its own?
#       Maybe in the messages we send over we will have a lot of information, including obviously address, but also like what needs to move where, how much, etc

