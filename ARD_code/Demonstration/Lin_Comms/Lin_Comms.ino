/* Purpose: This is a functional file to set up the Rotational Arduino as an I2C Slave 
        for receiving rotational commands from the Raspberry Pi and 
        controlling stepper motors for linear and rotational motion.
Contributors: Walter, Angela
Sources: SEED_LAB repository for previous examples
        IEEE 754 float conversion reference
        Arduino Wire Library Documentation (https://www.arduino.cc/reference/en/libraries/wire/)
        Stepper Library Documentation (https://www.arduino.cc/reference/en/libraries/stepper/)
Relevant Files: This file is related to the ARD_Comms.py file located in Demonstration/PI_code, it also goes with the FSM_Actual
Circuitry: Connect the following listed pins
  - Note that when things are numbered, i.e. the force sensors or arm pairs, it goes clockwise from low to high, with the pi at 6pm, starting top left
  - SDA on Arduino, second pin from top on left (03) is SDA on Pi
  - SCL on Arduino, third pin from top on left (05) is SCL on Pi
  - Ground on Arduino needs to connect to ground bus from Pi

  - A0=A3 on Arduino connects to the blue cables coming through the force sensors 0-3
  - These force sensors need to connect to 5V bus with their white cables
  - The force sensors also need to connect to the ground bus

  - Digital 2 on Arduino is the direction pin to connect to the driver for pair0
  - Digital 3 on Arduino is the Step pin to connect to the driver for pair0
  - Digital 4 on Arduino is the direction pin to connect to the driver for pair1
  - Digital 5 on Arduino is the step pin to connect to the driver for pair1
  - Each of these drivers also has ground pins that need to connect to the bus

  - Digital 10 on Arduino is end stop 0, top of pair 0
  - Digital 11 on Arduino is end stop 1, top of pair 1

  - GND on Arduino to GND bus for rotational end stops
  - 5V on Arduino to 5V bus for rotational end stops
  - Bus to pins for ground and 5V on the end stops
  - GND on Arduino to fifth pin from top left (09) on Pi

Libraries to be included:
 - Wire.h (For I2C communication)
 - AccelStepper.h (For controlling stepper motors) 
 - MultiStepper.h (For controlling multiple motors at the same time)
 
 */

#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Wire.h>

#define FORCE0_PIN A0
#define FORCE1_PIN A1
#define FORCE2_PIN A2
#define FORCE3_PIN A3

#define PAIR0_DIR_PIN 2
#define PAIR0_STP_PIN 3
#define PAIR1_DIR_PIN 4
#define PAIR1_STP_PIN 5

#define ENDSTOP_TOP_0_PIN 10
#define ENDSTOP_TOP_1_PIN 11

#define LIN_ARD_ADD 15


//Honestly I'm not sure what of these I will/won't need, I will probably get rid of some and add some as I go through
volatile uint8_t instruction[32] = {0}; //content of the message
volatile uint8_t messageLength=0; //length of the message sent
volatile bool newMessage=false; //1 when we have a message to interpret


volatile bool messageReceived=false; //1 if the Pi has prompted the non 20 status, indicating that 'DONE' state is done
volatile bool ctrlBusy=false; //whether or not the control system is actively busy or not
volatile bool ctrlDone=false; //whether or not the control system is done (1) or not.
volatile bool moving0 = false; //if moving pair 0
volatile bool moving1 = false; //if moving pair 1

//these are the volatile things to record the position and target position of each of the motors, as well as their execution status
//note that for now we are communicating steps, not mm of movement
volatile uint8_t executionStatus0=0; //the status of the capturing execution for pair 0
volatile uint8_t executionStatus1=10; //the status of the capturing execution for pair 1
volatile long targ_steps_pair[2] = {0, 0};
static long curr_steps_pair[2]; //0 is for pair0, 


//this is for the FSM states
//WAIT is while the Arduino is on and waiting for instructions
//MOVING is while the Arduino is moving its amount
//DONE is when it is done moving for whatever reason, and waiting for Pi to ask result
typedef enum {WAIT, MOVING, DONE} state;

//this is for interpretting the data sent from PI
volatile union FloatUnion 
{
uint8_t bytes[4];
float floatValue;
} byteFloat;

volatile uint8_t offset = 0; //offset of the message


const float lead_step = 0.01; // 0.01mm: Lead/Revolution = 2mm
const int steps_rev = 400; // 1/2 microstep: Steps/Rev = 200 (no microstep)
const int threshold = 60;
const int maxSpeed = 1000;
const int maxAccel = 500;
const int increment = 1; //I think its probably fine to have it move 1 step at a time, if too slow we could increase this though

AccelStepper stepper_lin0(AccelStepper::DRIVER, PAIR0_STP_PIN, PAIR0_DIR_PIN);
AccelStepper stepper_lin1(AccelStepper::DRIVER, PAIR1_STP_PIN, PAIR1_DIR_PIN);
MultiStepper steppers_lin;

// MultiStepper steppers_lin;
int numSteppers = 2; // Number of steppers in MultiStepper

void setup() {
    // Declare pins as output:
    stepper_lin0.setMaxSpeed(maxSpeed); // Set max speed stepper
    stepper_lin0.setAcceleration(maxAccel);
    // Accel not supported for AccelStepper
    // stepper_lin1.setCurrentPosition(0); // Set current position for stepper
    stepper_lin1.setMaxSpeed(maxSpeed);
    stepper_lin1.setAcceleration(maxAccel);

    //this is temporary, as we are about to have them open fully and will reset this
    stepper_lin0.setCurrentPosition(0);
    stepper_lin1.setCurrentPosition(0);

    steppers_lin.addStepper(stepper_lin0);
    steppers_lin.addStepper(stepper_lin1);

    //initializing the end stops
    pinMode(ENDSTOP_TOP_0_PIN, INPUT_PULLUP);
    pinMode(ENDSTOP_TOP_1_PIN, INPUT_PULLUP);

    //initialize the I2C slave
    Wire.begin(LIN_ARD_ADD); 
    Wire.onReceive(PiDataReceive); //this is triggered when Raspberry Pi sends data
    Wire.onRequest(PiDataRequest); //this is triggered when Raspberry Pi requests data

    //initialize the force sensors
    pinMode(FORCE0_PIN, INPUT);
    pinMode(FORCE1_PIN, INPUT);
    pinMode(FORCE2_PIN, INPUT);
    pinMode(FORCE3_PIN, INPUT);

    //Start serial for debugging
    //Note that you get rid of this and all serial statements if no longer debugging
    Serial.begin(9600);

    //also here, when this is starting being run, we want the arms to fully open up, regardless of where they are at initially. 
    Serial.println("Fully opening claw:");
    
    //we need to initialize their positions
    //debugging, note that the '+' in the below code need to be - for proper functionality

    curr_steps_pair[0]=0;
    curr_steps_pair[1]=0;

    //debugging
    if(digitalRead(ENDSTOP_TOP_0_PIN)==HIGH){
      Serial.println("ENDSTOP_TOP_0_PIN is HIGH");
    }
    if(digitalRead(ENDSTOP_TOP_1_PIN)==HIGH){
      Serial.println("ENDSTOP_TOP_1_PIN is HIGH");
    }

    while(digitalRead(ENDSTOP_TOP_0_PIN)==HIGH && digitalRead(ENDSTOP_TOP_1_PIN)==HIGH){
      curr_steps_pair[0] = curr_steps_pair[0] - increment;
      curr_steps_pair[1] = curr_steps_pair[1] - increment;
      steppers_lin.moveTo(curr_steps_pair);
      steppers_lin.runSpeedToPosition();
    }
    //at this point, at least one of the arms has hit its position, so we do the other
    while(digitalRead(ENDSTOP_TOP_0_PIN)==HIGH){
      stepper_lin0.moveTo(curr_steps_pair[0]-increment);
      stepper_lin0.runSpeedToPosition();
      curr_steps_pair[0]=curr_steps_pair[0]-increment;
    }
    //if it wasn't that one, it must be this one
    while(digitalRead(ENDSTOP_TOP_1_PIN)==HIGH){
      stepper_lin1.moveTo(curr_steps_pair[1]-increment);
      stepper_lin1.runSpeedToPosition();
      curr_steps_pair[1]=curr_steps_pair[1]-increment;
    }
    //we need to initialize their position that will be stored and changed and whatnot
    curr_steps_pair[0]=0;
    curr_steps_pair[1]=0;
    stepper_lin0.setCurrentPosition(0);
    stepper_lin1.setCurrentPosition(0);

    

    Serial.println("Linear Arduino Initialized.");
}

void loop() {
  //what we need here is to just wait to see if new thing to rotate to has been sent or not
 static int state = WAIT; //our state we are initializing to. Could be moving or done alternatively
 //based on what we get from 'on receive', we might change states
 
 //the functionality varies depending on what we are actively doing
 
 //debugging
 //Serial.println(state); //0 is waiting for message, 1 is moving, 2 is done
 delay(3000); //wait 3 seconds between this, just for debugging
 
 
  switch(state){
    case WAIT:
      //Serial.println("Waiting for message");
      if(newMessage==true){
        //debugging
        //Serial.print("newMessage: ");
        //Serial.println(newMessage);
        
        //here we will go into the moving state, and begin to move
        //the targetAngle is set in the receiveData ISR, 
        state=MOVING;
        //we also need to signal that we no longer have a new message
        newMessage=false;
        break;
      }
      else{
        state=WAIT;
        break;
      }
    case MOVING:
      //debugging:
      //Serial.print("ctrlDone: ");
      //Serial.println(ctrlDone);
      //Serial.print("ctrlBusy: ");
      //Serial.println(ctrlBusy);
      
      //if we are not actively controlling the system, 
      if(ctrlDone==true){
        //if we are done moving, we will go to the next state, and set the value of 'execution status' to the resulf of our move.
        ctrlDone=false;
        state=DONE;
        break;
      }
      if(ctrlBusy==false){
        //here we add in whatever move function
        ctrlBusy=true;
        //============MOVE FUNCTION=================
        //debugging
        //Serial.println("Starting moving!");
        if(moving0 == true && moving1 == true){
          steppers_move();
        }
        else if (moving0 == true){
          stepper0_move();
        }
        else if (moving1 == true){
          stepper1_move();
        }
        else{
          Serial.println("No steppers to move");
        }
        state=MOVING;
        break;
      }
      
      //if we are here we haven't just started or just finished moving
      //Serial.println("Still Moving");
    break;
  case DONE:
  //if the Pi has received our updated message, we can move back to waiting
    if(messageReceived==true){
      //debugging
      //Serial.println("Pi has sampled the non-20 messsage");
      
      messageReceived=false;
      state=WAIT;
      break;
    }
    else{
      state=DONE;
      break;
    }
  }
 //at this point, we are done with state transition logic. 
 //I am a bit concerned at the simplicity as compared to seed lab to be honest, but I think this all makes sense
 //there was just much more logic in the other one after the loop ended. 
}
//Note that for all of these, positive steps is moving arms up, cable tree down, negative steps is moving arms down, cable tree up


//stpper_lin0 is defined as a global variable, so we control it by changing its value globally rather than a pass by reference or whatever
void stepper0_move(){
  //the amount to move should be stored in targ_steps_pair0
  //and this would be updated when messages are sent or received

  
    //debugging
    Serial.print("Moving pair0\ncurr_steps_pair0: ");
    Serial.println(curr_steps_pair[0]);
    Serial.print("targ_steps_pair0: ");
    Serial.println(targ_steps_pair[0]);

  //if we want to move to more steps than we're at, we are actually closing the arm/moving tree down rn
  if(targ_steps_pair[0]>curr_steps_pair[0]){
    //we want to keep looping as long as the following things are true
    // we have more steps to move
    // we haven't triggered the low end stop (maximum closure)
    // we haven't gotten pressure on the sensors, which output a number 0-1023 when read, with 1023 being that they are experiencing full force
    // debugging, took out this from the while loop since it won't be wired up  && digitalRead(ENDSTOP_BOT_0_PIN)==HIGH

    //debugging, make sure to re-include the force sensors later
    while(targ_steps_pair[0] > curr_steps_pair[0]/* && analogRead(FORCE0_PIN)<1000 && analogRead(FORCE1_PIN<1000)*/){
      //debugging
      //Serial.print("Moving pair0\ncurr_steps_pair0: ");
      //Serial.println(curr_steps_pair[0]);
      //Serial.print("targ_steps_pair0: ");
      //Serial.println(targ_steps_pair[0]);
      curr_steps_pair[0] = stepper_lin0.currentPosition() + increment;
      stepper_lin0.moveTo(curr_steps_pair[0]);
      stepper_lin0.runSpeedToPosition();
    }
  }
  //we are opening the pair/moving tree up here
  else if (targ_steps_pair[0]<curr_steps_pair[0]){
    //we want to keep looping as long as the following things are true
    // we have more steps to move
    // we haven't triggered the high end stop (maximum closure)
    
    while(targ_steps_pair[0] < curr_steps_pair[0] && digitalRead(ENDSTOP_TOP_0_PIN)==HIGH){  
      //debugging
      //Serial.print("Moving pair0\ncurr_steps_pair0: ");
      //Serial.println(curr_steps_pair[0]);
      //Serial.print("targ_steps_pair0: ");
      //Serial.println(targ_steps_pair[0]);
      curr_steps_pair[0] = stepper_lin0.currentPosition() - increment;
      stepper_lin0.moveTo(curr_steps_pair[0]);
      stepper_lin0.runSpeedToPosition();
    }

  }
  //if we get here, we aren't moving this pair for some reason
  else{
    Serial.println("No pair0 movement");
  }
  //now we have finished moving stepper0
  moving0 = false;
  ctrlBusy = false;
  ctrlDone = true;
  
  //now we need to determine our output status based on what flags are set
  //our priority will go: normal movement, force sensor, end stop

  //debugging, make sure to re-include force sensors later
  if (targ_steps_pair[0]==curr_steps_pair[0]){
    executionStatus0 = 1;
    return;
  }
  /*
  else if(analogRead(FORCE0_PIN)>1000 || analogRead(FORCE1_PI)>1000)){
    executionStatus0 = 4;
    return;
  }
  //fully open end stop
  */
  else if(digitalRead(ENDSTOP_TOP_0_PIN)==LOW){
    executionStatus0 = 2;
    return;
  }
  //debugging, fully closed end stop, commented because it will never be triggered since meches miss-sized the area and so it isn't worth it to wire up
  /*
  else if(digitalRead(ENDSTOP_BOT_0_PIN)==LOW){
    executionStatus0 = 3;
    return;
  }
  */
  //unrecognized command/result/failed output
  else{
    executionStatus0 = 5;
    return;
  }

}

//stepper_lin1 is defined as a global variable as well, so we control it by accessing it locally not passing by reference
void stepper1_move(){
  //the amount to move should be stored in targ_steps_pair0
  //and this would be updated when messages are sent or received

  
    //debugging
    Serial.print("Moving pair1\ncurr_steps_pair1: ");
    Serial.println(curr_steps_pair[1]);
    Serial.print("targ_steps_pair1: ");
    Serial.println(targ_steps_pair[1]);

  //if we want to move to more steps than we're at, we are actually closing the arm/moving tree down rn
  if(targ_steps_pair[1]>curr_steps_pair[1]){
    //we want to keep looping as long as the following things are true
    // we have more steps to move
    // we haven't triggered the low end stop (maximum closure)
    // we haven't gotten pressure on the sensors, which output a number 0-1023 when read, with 1023 being that they are experiencing full force
    
    //NOte that this is the previous while loop, but ENDSTOP_BOT_1_PIN will always be high 
    //while(targ_steps_pair[1] > curr_steps_pair[1] && digitalRead(ENDSTOP_BOT_1_PIN)==HIGH && analogRead(FORCE2_PIN)<1000 && analogRead(FORCE3_PIN<1000)){

    //debugging, remember to reinclude force sensors later

    while(targ_steps_pair[1] > curr_steps_pair[1]/* &&  analogRead(FORCE2_PIN)<1000 && analogRead(FORCE3_PIN<1000)*/){
      curr_steps_pair[1]=stepper_lin1.currentPosition() + increment;
      stepper_lin1.moveTo(curr_steps_pair[1]);
      stepper_lin1.runSpeedToPosition();
    }
  }
  //we are opening the pair/moving tree up here
  else if (targ_steps_pair[1]<curr_steps_pair[1]){
    //we want to keep looping as long as the following things are true
    // we have more steps to move
    // we haven't triggered the high end stop (maximum closure)
    
    while(targ_steps_pair[1] < curr_steps_pair[1] && digitalRead(ENDSTOP_TOP_1_PIN)==HIGH){
      curr_steps_pair[1]=stepper_lin1.currentPosition() - increment;
      stepper_lin1.moveTo(curr_steps_pair[1]);
      stepper_lin1.runSpeedToPosition();
    }
  }
  //if we get here, we aren't moving this pair for some reason
  else{
    Serial.println("No pair1 movement");
  }
  //now we have finished moving stepper0
  moving1 = false;
  ctrlBusy = false;
  ctrlDone = true;
  
  //now we need to determine our output status based on what flags are set
  //our priority will go: force sensor, end stop, normal movement

  //debugging, remember to re-include force sensors later
  if (targ_steps_pair[1]==curr_steps_pair[1]){
    executionStatus1 = 11;
    return;
  }
  /*else if(analogRead(FORCE2_PIN)>1000 || analogRead(FORCE3_PIN)>1000){
    executionStatus1 = 14;
    return;
  }
  //fully open end stop
  */
  else if(digitalRead(ENDSTOP_TOP_1_PIN)==LOW){
    executionStatus1 = 12;
    return;
  }
  //debugging, fully closed end stop, commented because it will always be low since we're not wiring it
  /*
  else if(digitalRead(ENDSTOP_BOT_1_PIN)==LOW){
    executionStatus1 = 13;
    return;
  }
  */
  //unrecognized command/result/failed output
  else{
    executionStatus1 = 15;
    return;
  }

}

//this is the shared function for both of the stepper motors' simultaneous movement
void steppers_move() {
  //going into this function, we have no assumptions about the current position of the arms
  //this means that they could be beyond their target locations or before, closing or opening, and may or may not be at the same step value

  //debugging
  Serial.print("Moving both pairs\ncurr_steps_pair[0]: ");
  Serial.println(curr_steps_pair[0]);
  Serial.print("curr_steps_pair[1]: ");
  Serial.println(curr_steps_pair[1]);

  Serial.print("targ_steps_pair[0]: ");
  Serial.println(targ_steps_pair[0]);
  Serial.print("targ_steps_pair[1]: ");
  Serial.println(targ_steps_pair[1]);

  

  //if both will be moving up
  //debugging, remember to reinclude force sensors later
  if(targ_steps_pair[0]>curr_steps_pair[0] || targ_steps_pair[1]>curr_steps_pair[1]){
    while((targ_steps_pair[0] > curr_steps_pair[0]/* && analogRead(FORCE0_PIN)<1000 && analogRead(FORCE1_PIN<1000)*/) && (targ_steps_pair[1] > curr_steps_pair[1]/* && analogRead(FORCE2_PIN)<1000 && analogRead(FORCE3_PIN)<1000*/)){
      curr_steps_pair[0] = curr_steps_pair[0] + increment;
      curr_steps_pair[1] = curr_steps_pair[1] + increment;
      steppers_lin.moveTo(curr_steps_pair);
      steppers_lin.runSpeedToPosition();
    }
    //at this point, one of the pairs has finished but the other might not have for some reason
    //first, lets check for pair 0
    while(targ_steps_pair[0] > curr_steps_pair[0]/* && analogRead(FORCE0_PIN)<1000 && analogRead(FORCE1_PIN<1000)*/){
      curr_steps_pair[0] = stepper_lin0.currentPosition() + increment;
      stepper_lin0.moveTo(curr_steps_pair[0]);
      stepper_lin0.runSpeedToPosition();
    }
    //now, lets check for pair1
    while(targ_steps_pair[1] > curr_steps_pair[1]/* && analogRead(FORCE2_PIN)<1000 && analogRead(FORCE3_PIN)<1000*/){
      curr_steps_pair[1] = stepper_lin1.currentPosition() + increment;
      stepper_lin1.moveTo(curr_steps_pair[1]);
      stepper_lin1.runSpeedToPosition();
    }
  }
  //the alternative is if both arms will be moving down
  //if both will be moving up
  else if(targ_steps_pair[0]<curr_steps_pair[0] || targ_steps_pair[1]<curr_steps_pair[1]){
    while((targ_steps_pair[0] < curr_steps_pair[0] && digitalRead(ENDSTOP_TOP_0_PIN)==HIGH) && (targ_steps_pair[1] < curr_steps_pair[1] && digitalRead(ENDSTOP_TOP_1_PIN)==HIGH)){
      curr_steps_pair[0] = curr_steps_pair[0] - increment;
      curr_steps_pair[1] = curr_steps_pair[1] - increment;
      steppers_lin.moveTo(curr_steps_pair);
      steppers_lin.runSpeedToPosition();
    }
    //at this point, one of the pairs has finished but the other might not have for some reason
    //first, lets check for pair 0
    while(targ_steps_pair[0] < curr_steps_pair[0] && digitalRead(ENDSTOP_TOP_0_PIN)==HIGH){
      curr_steps_pair[0] = stepper_lin0.currentPosition() - increment;
      stepper_lin0.moveTo(curr_steps_pair[0]);
      stepper_lin0.runSpeedToPosition();
    }
    //now, lets check for pair1
    while(targ_steps_pair[1] < curr_steps_pair[1] && digitalRead(ENDSTOP_TOP_1_PIN)==HIGH){
      curr_steps_pair[1] = stepper_lin1.currentPosition() - increment;
      stepper_lin1.moveTo(curr_steps_pair[1]);
      stepper_lin1.runSpeedToPosition();
    }
  }
  else { //if we get here there must be no movement
    Serial.println("No movement for both arms");
  }

  //at this point, for better or worse, all of the movement has been done, which means that all that's left to do is the stuff with the status generation
  moving0 = false;
  moving1 = false;
  ctrlBusy = false;
  ctrlDone = true;
//our priority will go: force sensor, end stop, normal movement
//debugging: remember to reinclude force sensors later
  if (targ_steps_pair[0]==curr_steps_pair[0]){
    executionStatus0 = 1;
  }
  /*else if(analogRead(FORCE0_PIN)>1000 || analogRead(FORCE1_PIN)>1000){
    executionStatus0 = 4;
  }
  */
  //fully open end stop
  else if(digitalRead(ENDSTOP_TOP_0_PIN)==LOW){
    executionStatus0 = 2;
  }
  //debugging, fully closed end stop, commented because it will never be triggered since meches miss-sized the area and so it isn't worth it to wire up
  /*
  else if(digitalRead(ENDSTOP_BOT_0_PIN)==LOW){
    executionStatus0 = 3;
    return;
  }
  */
  //unrecognized command/result/failed output
  else{
    executionStatus0 = 5;
  }

  //now we just have to generate the output status stuff
  //now we need to determine our output status based on what flags are set
  //our priority will go: force sensor, end stop, normal movement
  //debugging, remember to reinclude force sensors later

  if (targ_steps_pair[1]==curr_steps_pair[1]){
    executionStatus1 = 11;
  }
  /*else if(analogRead(FORCE2_PIN)>1000 || analogRead(FORCE3_PIN)>1000){
    executionStatus1 = 14;
  }
  */
  //fully open end stop
  else if(digitalRead(ENDSTOP_TOP_1_PIN)==LOW){
    executionStatus1 = 12;
  }
  //debugging, fully closed end stop, commented because it will always be low since we're not wiring it
  /*
  else if(digitalRead(ENDSTOP_BOT_1_PIN)==LOW){
    executionStatus1 = 13;
    return;
  }
  */
 
  //unrecognized command/result/failed output
  else{
    executionStatus1 = 15;
  }
  return;

}


//the challenging part here is that I need to get both of them to move together now.
/*
void steppers_moveMM (MultiStepper &steppers, float mm, int numSteppers) {
  long positions[numSteppers];
  float steps = (mm*steps_rev)/(200*lead_step);
  for (int i = 0; i < numSteppers; i++) {
    positions[i] = steps;
  }
  steppers.moveTo(positions);
  steppers.runSpeedToPosition();
}
*/

//This gets called when the Pi tries to send data over
//
void PiDataReceive(){
    //debugging
    //Serial.println("Entering PiDataReceive");

    //getting the offset
    offset = Wire.read();

    //debugging
    //Serial.print("We are receiving offset: ");
    //Serial.println(offset);

    if(offset==0 || offset==1 || offset==2){
      //getting the full message
      while(Wire.available()){
        instruction[messageLength] = Wire.read(); //get the next byte of info
        messageLength++;
      }
    }
    //now we need to decide what to do with the message based on the input offset
    //if offset=0, we are getting sent the target steps for pair0
    if(offset==0){
        byteFloat.bytes[0] = instruction[3];
        byteFloat.bytes[1] = instruction[2];
        byteFloat.bytes[2] = instruction[1];
        byteFloat.bytes[3] = instruction[0];
        targ_steps_pair[0] = byteFloat.floatValue + curr_steps_pair[0];
        moving0 = true;
    }
    //if offset=1, we are getting sent the target steps for pair1
    else if(offset==1){
        byteFloat.bytes[0] = instruction[3];
        byteFloat.bytes[1] = instruction[2];
        byteFloat.bytes[2] = instruction[1];
        byteFloat.bytes[3] = instruction[0];
        targ_steps_pair[1] = byteFloat.floatValue + curr_steps_pair[1];
        moving1 = true;
    }
    //if offset=2, we are getting the steps for both pairs
    else if(offset==2){
        byteFloat.bytes[0] = instruction[3];
        byteFloat.bytes[1] = instruction[2];
        byteFloat.bytes[2] = instruction[1];
        byteFloat.bytes[3] = instruction[0];
        targ_steps_pair[0] = byteFloat.floatValue + curr_steps_pair[0];
        targ_steps_pair[1] = byteFloat.floatValue + curr_steps_pair[1];
        moving0 = true;
        moving1 = true;
    }
    //
    else if(offset==3 || offset==4 || offset==5){
        //Serial.println("Preparing to be read");
        return;
    }
    else{
        //debugging
        Serial.println("Unknown offset");
    }
    //Because we have multiple offsets to read from for the status, 
    //debugging
    Serial.print("targ_steps_pair[0]: ");
    Serial.println(targ_steps_pair[0]);
    Serial.print("targ_steps_pair[1]: ");
    Serial.println(targ_steps_pair[1]);


    newMessage = true;
    messageLength = 0;
}

//this function gets called whenever the Pi requests data from the Arduino about the execution status
void PiDataRequest(){
  //I think we need to get the offset first?
  //I think this is done in the Pi_Data_Receive, so offset should be properly set already
  //for the pair0 information

  //debugging
  //Serial.println("Entering PiDataRequest");
  //Serial.print("Offset is: ");
  //Serial.println(offset);

  uint8_t status_block[2] = {executionStatus0, executionStatus1}; //note that this might be out of order compared to how it will be received, I need to check though
  
  //debugging
  //Serial.print("executionStatus0: ");
  //Serial.println(executionStatus0);
  //Serial.print("executionStatus1: ");
  //Serial.println(executionStatus1);
  if(offset==3){
    //debugging
    //Serial.println("trying to write offset 3");

    Wire.write(status_block, 2);
    //also make sure that if the status is as desired we continue
    if(executionStatus0!=0){
      executionStatus0=0;
      messageReceived=1;
    }
  }
  //for the pair1 information
  else if(offset==4){
    //debugging
    //Serial.println("trying to write offset 4");
    
    Wire.write(status_block, 2);
    //also make sure that if the Pi read status correctly we continue, 
    //note that we only care if the second one is done executing here
    if(executionStatus1!=10){
      executionStatus1=10;
      messageReceived=1;
    }
  }
  //for both the pairs' information
  else if(offset==5){
    //debugging
    //Serial.println("trying to write offset 5");

    Wire.write(status_block, 2);
    //if both are done executing 
    if(executionStatus0 != 0 && executionStatus1 != 10){
      executionStatus0 = 0;
      executionStatus1 = 10;
      messageReceived = 1;
    }
  }
  else{
    Serial.println("Unknown offset");
  }
  //honestly I think that is all that there is in this area.

  //debugging
  //Serial.println("Exiting PiDataRequest");


}