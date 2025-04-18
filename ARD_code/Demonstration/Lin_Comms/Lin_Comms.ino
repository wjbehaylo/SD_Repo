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


  - Digital 11 on Arduino is the signal pin for the 0 degree end stop, this is the orange cable
  - Digital 12 on Arduino is the signal pin for the 90 degree end stop, this is the purple cable
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

#define FORCE0_Pin A0
#define FORCE1_Pin A1
#define FORCE2_Pin A2
#define FORCE3_Pin A3

#define dirPin_l1 2
#define stepPin_l1 3
#define dirPin_l2 12
#define stepPin_l2 12
#define joyxPin A0

/* COM NOTES
General: PI Probes ARD for value, sends int response based on status
Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
*/ 

int xVal;
int xSpeed;

const float lead_step = 0.01; // 0.01mm: Lead/Revolution = 2mm
const int steps_rev = 400; // 1/2 microstep: Steps/Rev = 200 (no microstep)
const int threshold = 60;
const int maxSpeed = 500;
const int maxAccel = 500;

AccelStepper stepper_lin1(1,stepPin_l1,dirPin_l1);
AccelStepper stepper_lin2(1,stepPin_l2,dirPin_l2);

// MultiStepper steppers_lin;
int numSteppers = 2; // Number of steppers in MultiStepper

void setup() {
  Serial.begin(9600);
   // Declare pins as output:
  stepper_lin1.setMaxSpeed(maxSpeed); // Set max speed stepper
  stepper_lin1.setAcceleration(maxAccel);
  // Accel not supported for AccelStepper
  // stepper_lin1.setCurrentPosition(0); // Set current position for stepper
  stepper_lin2.setMaxSpeed(maxSpeed);
  stepper_lin2.setAcceleration(maxAccel);
  // stepper_lin2.setCurrentPosition(0);

  // steppers_lin.addStepper(stepper_lin1);
  // steppers_lin.addStepper(stepper_lin2);
}

void loop() {
  //* Function test code *//
  // steppers_moveMM(steppers_lin, 100, numSteppers); // + goes up
  // delay(1000);

  // steppers_moveMM(steppers_lin, 0, numSteppers);
  // delay(1000);

  //* Joystick code for demo *//
  xVal = analogRead(joyxPin); // 0-900
  xSpeed = map(xVal, 0, 900, maxSpeed, -1*maxSpeed);

  // Apply dead zone
  if (abs(xSpeed) < threshold){
    xSpeed = 0;
  }

  stepper_lin1.setSpeed(xSpeed);
  stepper_lin2.setSpeed(xSpeed);

  stepper_lin1.runSpeed();
  stepper_lin2.runSpeed();
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