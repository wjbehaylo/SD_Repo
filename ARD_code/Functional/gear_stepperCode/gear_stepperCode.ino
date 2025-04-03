#include <AccelStepper.h>

#define STEPPER3_STEP_PIN 6
#define STEPPER3_DIR_PIN 7
#define ROT_ARD_ADD 8

/* COM NOTES
General: PI Probes ARD for value, sends int response based on status
Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
*/ 

// Steps/Rev = 200 (no microstep)
const int steps_rev = 400; // 1/2 microstep
long theta = 0;

AccelStepper stepper_gear1(1,STEPPER3_STEP_PIN,STEPPER3_DIR_PIN);

void setup() {
  // Declare pins as output
  stepper_gear1.setMaxSpeed(1000);
  stepper_gear1.setAcceleration(500);
  stepper_gear1.setCurrentPosition(0);
}

void loop() {
  
  stepper_moveTheta(stepper_gear1, 90);
  theta = currentTheta(stepper_gear1);
  delay(1000);
  stepper_moveTheta(stepper_gear1, 0);
  theta = currentTheta(stepper_gear1);
  delay(1000);
}

//How many steps is it to move the upper part 1 degree? 0.1 degree?
//400 steps per revolution of small gear. 
//X number of small gear revolutions per big gear revolution
//Stepper steps -> degrees rotated = 400 steps/360 degrees small * xdegrees small/ydegrees big
void stepper_moveTheta (AccelStepper &stepper, float theta) {
  float steps = theta*steps_rev/360;
  stepper.moveTo(steps);
  stepper.runToPosition();
}

long currentTheta (AccelStepper &stepper) {
  return long(stepper.currentPosition()*360/steps_rev);
}