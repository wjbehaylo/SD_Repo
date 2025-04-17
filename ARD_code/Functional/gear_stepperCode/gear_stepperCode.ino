#include <AccelStepper.h>

#define STEPPER3_STEP_PIN 3
#define STEPPER3_DIR_PIN 2
#define ROT_ARD_ADD 8
#define joyxPin A0

/* COM NOTES
General: PI Probes ARD for value, sends int response based on status
Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
*/ 

int xVal;
int xSpeed;

const int threshold = 15;
const int maxSpeed = 100;
const int maxAccel = 100;

// Steps/Rev = 200 (no microstep)
const int steps_rev = 2000; // 1/2 microstep
const int gear_ratio = 3; // Base gear ratio
const float increment = 0.1; // Stepper theta increment
float theta_d = 0; // Desired theta
float theta = 0; // Angle tracker

AccelStepper stepper_gear1(1,STEPPER3_STEP_PIN,STEPPER3_DIR_PIN);

void setup() {
  // Declare pins as output
  Serial.begin(9600);
  stepper_gear1.setMaxSpeed(maxSpeed);
  stepper_gear1.setAcceleration(maxAccel);
  stepper_gear1.setCurrentPosition(0);
}

void loop() {
  
  //* Function test code *//
  // theta_d = 90;
  // stepper_rotate(stepper_gear1);
  // delay(1000);

  // theta_d = 0;
  // stepper_rotate(stepper_gear1);
  // delay(1000);

  //* Joystick code for demo *//
  xVal = analogRead(joyxPin); // 0-900
  xSpeed = map(xVal, 0, 900, maxSpeed, -1*maxSpeed);

  // Apply dead zone
  if (abs(xSpeed) < threshold){
    xSpeed = 0;
  }

  stepper_gear1.setSpeed(xSpeed);

  stepper_gear1.runSpeed();
}

//How many steps is it to move the upper part 1 degree? 0.1 degree?
//400 steps per revolution of small gear. 
//X number of small gear revolutions per big gear revolution
//Stepper steps -> degrees rotated = 400 steps/360 degrees small * xdegrees small/ydegrees big
void stepper_moveTheta (AccelStepper &stepper, float theta) {
  float steps = gear_ratio*theta*steps_rev/360;
  stepper.moveTo(steps);
  stepper.runToPosition();
}

float currentTheta (AccelStepper &stepper) {
  return float(stepper.currentPosition()*360/steps_rev);
}

void stepper_rotate(AccelStepper &stepper) {
  //now we will move by 0.1 degree in the negative direction, and update current angle
  stepper_moveTheta(&stepper, theta - increment); // need to test direction (+/-)
  theta = currentTheta(&stepper);
}