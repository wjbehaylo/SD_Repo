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

#stateA is "initializing". 
# Purpose: 
#   this is here to confirm the start up of the program and FSM.
# Functionality:
#   this will include making sure that the arduinos, camera, sensors, and UART are all connected. 
#   
# Transition: It will automatically transition to stateB, and is just here to make sure the machine is running
def stateA():
    print("Initializing FSM")
    return stateB

#stateB is "waiting to start". It will wait for UART