#include <AccelStepper.h>
#include <MultiStepper.h>
#define dirPin_l1 2
#define stepPin_l1 3
#define dirPin_l2 12
#define stepPin_l2 11

/* COM NOTES
General: PI Probes ARD for value, sends int response based on status
Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
*/ 

const float lead_step = 0.01; // 0.01mm: Lead/Revolution = 2mm
const int steps_rev = 400; // 1/2 microstep: Steps/Rev = 200 (no microstep)

AccelStepper stepper_lin1(1,stepPin_l1,dirPin_l1);
AccelStepper stepper_lin2(1,stepPin_l2,dirPin_l2);

MultiStepper steppers_lin;
int numSteppers = 2; // Number of steppers in MultiStepper

void setup() {
   // Declare pins as output:
  stepper_lin1.setMaxSpeed(1000); // Set max speed stepper
  // Accel not supported for AccelStepper
  stepper_lin1.setCurrentPosition(0); // Set current position for stepper
  stepper_lin2.setMaxSpeed(1000);
  stepper_lin2.setCurrentPosition(0);

  steppers_lin.addStepper(stepper_lin1);
  steppers_lin.addStepper(stepper_lin2);
}

void loop() {

  steppers_moveMM(steppers_lin, 2, numSteppers);
  delay(1000);

  steppers_moveMM(steppers_lin, 0, numSteppers);
  delay(1000);
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