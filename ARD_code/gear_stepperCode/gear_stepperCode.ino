#include <AccelStepper.h>

#define dirPin_g1 7
#define stepPin_g1 6

/* COM NOTES
General: PI Probes ARD for value, sends int response based on status
Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
*/ 

const float lead_step = 0.01; // 0.01mm
const int steps_rev = 400; // 1/2 microstep
// Lead/Revolution = 2mm
// Steps/Rev = 200 (no microstep)

AccelStepper stepper_gear1(1,stepPin_g1,dirPin_g1);

void setup() {
  // Declare pins as output
  stepper_gear1.setMaxSpeed(1000);
  stepper_gear1.setAcceleration(500);
  stepper_gear1.setCurrentPosition(0);
}

void loop() {

  stepper_moveMM(stepper_gear1, 2);
  delay(1000);
  stepper_moveMM(stepper_gear1, 0);
  delay(1000);
}

void stepper_moveMM (AccelStepper &stepper, float mm) {
  float steps = (mm*steps_rev)/(200*lead_step);
  stepper.moveTo(steps);
  stepper.runToPosition();
}