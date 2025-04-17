#include <AccelStepper.h>
#include <MultiStepper.h>
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