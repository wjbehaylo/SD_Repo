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
  - Note that when things are numbered, i.e. the force sensors or arm pairs, it goes clockwise from low to high, with the pi at 6pm
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
  - Digital 11 on Arduino is end stop 1, bot of pair 0
  - Digital 12 on Arduino is end stop 2, bot of pair 1
  - Digital 13 on Arduino is end stop 3, top of pair 1

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

#define FORCE0_PIN A0
#define FORCE1_PIN A1
#define FORCE2_PIN A2
#define FORCE3_PIN A3

#define PAIR0_DIR_PIN 2
#define PAIR0_STP_PIN 3
#define PAIR1_DIR_PIN 4
#define PAIR1_STP_PIN 5

#define ENDSTOP_TOP_0_PIN 10
#define ENDSTOP_BOT_0_PIN 11
#define ENDSTOP_BOT_1_PIN 12
#define ENDSTOP_TOP_1_PIN 13

#define LIN_ARD_ADD 15


//Honestly I'm not sure what of these I will/won't need, I will probably get rid of some and add some as I go through
volatile uint8_t instruction[32] = {0}; //content of the message
volatile uint8_t messageLength=0; //length of the message sent
volatile uint8_t newMessage=0; //1 when we have a message to interpret


volatile uint8_t messageReceived=0; //1 if the Pi has prompted the non 20 status, indicating that 'DONE' state is done
volatile bool configuring = false;
volatile short ctrlBusy=0; //whether or not the control system is actively busy or not
volatile short ctrlDone=0; //whether or not the control system is done (1) or not.

//these are the volatile things to record the position and target position of each of the motors, as well as their execution status
volatile uint8_t executionStatus0=0; //the status of the capturing execution for pair 0
volatile uint8_t executionStatus1=10; //the status of the capturing execution for pair 1
volatile long targ_steps_pair0 = 0;
volatile long targ_steps_pair1 = 0;
static long curr_steps_pair0;
static long curr_steps_pair1;

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
const int maxSpeed = 500;
const int maxAccel = 500;

AccelStepper stepper_lin0(AccelStepper::DRIVER, PAIR0_STP_PIN, PAIR0_DIR_PIN);
AccelStepper stepper_lin1(AccelStepper::DRIVER, PAIR1_STP_PIN, PAIR1_DIR_PIN);

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

    //initializing the end stops
    pinMode(ENDSTOP_TOP_0_PIN, INPUT_PULLUP);
    pinMode(ENDSTOP_BOT_0_PIN, INPUT_PULLUP);
    pinMode(ENDSTOP_TOP_1_PIN, INPUT_PULLUP);
    pinMode(ENDSTOP_BOT_1_PIN, INPUT_PULLUP);

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
    Serial.println("Linear Arduino Initialized.");
}

void loop() {
  
}

void stepper_moveMM (AccelStepper &stepper, float mm) {
  float steps = (mm*steps_rev)/(200*lead_step);
  stepper.moveTo(steps);
  stepper.runToPosition();
}

void steppers_moveMM (MultiStepper &steppers, float mm, int numSteppers) {
  long positions[numSteppers];
  float steps = (mm*steps_rev)/(200*lead_step);
  for (int i = 0; i < numSteppers; i++) {
    positions[i] = steps;
  }
  steppers.moveTo(positions);
  steppers.runSpeedToPosition();
}

//This gets called when the Pi tries to send data over
//
void Pi_Data_Receive(){
    //getting the offset
    offset = Wire.read();

    //getting the full message
    while(Wire.available()){
        instruction[messageLength] = Wire.read(); //get the next byte of info
        messageLength++;
    }

    //now we need to decide what to do with the message based on the input offset
    //if offset=0, we are getting sent the target steps for pair0
    if(offset==0){
        byteFloat.bytes[0] = instruction[3];
        byteFloat.bytes[1] = instruction[2];
        byteFloat.bytes[2] = instruction[1];
        byteFloat.bytes[3] = instruction[0];
        targ_steps_pair0 = byteFloat.floatValue + curr_steps_pair0;
    }
    //if offset=1, we are getting sent the target steps for pair1
    else if(offset==1){
        byteFloat.bytes[0] = instruction[3];
        byteFloat.bytes[1] = instruction[2];
        byteFloat.bytes[2] = instruction[1];
        byteFloat.bytes[3] = instruction[0];
        targ_steps_pair1 = byteFloat.floatValue + curr_steps_pair1;
    }
    //if offset=2, we are getting the steps for both pairs
    else if(offset==2){
        byteFloat.bytes[0] = instruction[3];
        byteFloat.bytes[1] = instruction[2];
        byteFloat.bytes[2] = instruction[1];
        byteFloat.bytes[3] = instruction[0];
        targ_steps_pair0=byteFloat.floatValue + curr_steps_pair0;
        targ_steps_pair1=byteFloat.floatValue + curr_steps_pair1;
    }
    else{
        //debugging
        Serial.println("Unknown offset");
    }
    //Because we have multiple offsets to read from for the status, 

}