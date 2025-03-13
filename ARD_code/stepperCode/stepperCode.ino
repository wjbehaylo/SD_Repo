#include <AccelStepper.h>
#include <MultiStepper.h>
#define dirPin_l1 2
#define stepPin_l1 3
#define dirPin_l2 4
#define stepPin_l2 5
#define dirPin_g1 7
#define stepPin_g1 6

const float lead_step = 0.01; // 0.01mm
const int steps_rev = 400; // 1/2 microstep
// Lead/Revolution = 2mm
// Steps/Rev = 200 (no microstep)

AccelStepper stepper_lin1(1,stepPin_l1,dirPin_l1);
AccelStepper stepper_lin2(1,stepPin_l2,dirPin_l2);
AccelStepper stepper_gear1(1,stepPin_g1,dirPin_g1);

MultiStepper steppers_lin;

void setup() {
  // Declare pins as output:
  stepper_lin1.setMaxSpeed(1000); // Set max speed stepper
  stepper_lin1.setAcceleration(500); // Set max accel for stepper
  stepper_lin1.setCurrentPosition(0); // Set current position for stepper
  stepper_lin2.setMaxSpeed(1000);
  stepper_lin2.setAcceleration(500);
  stepper_lin2.setCurrentPosition(0);
  stepper_gear1.setMaxSpeed(1000);
  stepper_gear1.setAcceleration(500);
  stepper_gear1.setCurrentPosition(0);

  steppers_lin.addStepper(stepper_lin1);
  steppers_lin.addStepper(stepper_lin1);
}

void loop() {

  // steppers_lin.moveTo(400);
  // steppers_lin.runSpeedToPosition(); // If you dont want blocking consider using run() instead.
  steppers_moveMM(steppers_lin, 2);
  delay(1000);

  // steppers_lin.moveTo(0);
  // steppers_lin.runSpeedToPosition();
  steppers_moveMM(steppers_lin, 0);
  delay(1000);

  //steppers_moveMM(steppers_lin, 2);
  //steppers_moveMM(steppers_lin, 0);

}

void stepper_moveMM (AccelStepper &stepper, float mm) {
  float steps = (mm*steps_rev)/(200*lead_step);
  stepper.moveTo(steps);
  stepper.runToPosition();
}

void steppers_moveMM (MultiStepper &steppers, float mm) {
  int steps = (mm*steps_rev)/(200*lead_step);
  steppers.moveTo(steps);
  steppers.runSpeedToPosition();
}