/**
 * @file linear_control.cpp
 * @brief Implementation of synchronized dual-stepper lift motion based on distance data.
 *
 * Description:
 * ------------
 * This file sets up two synchronized stepper motors using AccelStepper to control lift motion.
 * It receives two bytes over I2C from the Raspberry Pi: [angle_byte, distance_byte],
 * and only the distance_byte is used to determine lift height.
 *
 * Hardware Connections:
 * ----------------------
 * Arduino A (Linear Control) — I2C Address: 0x08
 *
 * Stepper Motor 1 (Left):
 *   - STEP → pin 4
 *   - DIR  → pin 5
 *
 * Stepper Motor 2 (Right):
 *   - STEP → pin 6
 *   - DIR  → pin 7
 *
 * I2C:
 *   - SDA → A4
 *   - SCL → A5
 *   - GND → shared with Raspberry Pi and rotation Arduino
 */

 #include "linear_control.h"

 // Instantiate the lift steppers
 AccelStepper liftStepper1(AccelStepper::DRIVER, LIFT1_STEP_PIN, LIFT1_DIR_PIN);
 AccelStepper liftStepper2(AccelStepper::DRIVER, LIFT2_STEP_PIN, LIFT2_DIR_PIN);
 
 volatile int targetLiftSteps = 0;
 volatile bool newLiftCommand = false;
 
 // Setup speed, acceleration, and initial position for both lift steppers
 void setupLinearSteppers() {
   liftStepper1.setMaxSpeed(1000);
   liftStepper1.setAcceleration(200);
   liftStepper1.setCurrentPosition(0);
 
   liftStepper2.setMaxSpeed(1000);
   liftStepper2.setAcceleration(200);
   liftStepper2.setCurrentPosition(0);
 }
 
 // Move both steppers toward the shared target position
 void updateLinearSteppers() {
   liftStepper1.moveTo(targetLiftSteps);
   liftStepper2.moveTo(targetLiftSteps);
 
   liftStepper1.run();
   liftStepper2.run();
 }
 
 // I2C receive handler: reads 2 bytes, uses distance byte for lift
 void receiveLinearEvent(int howMany) {
   if (howMany < 2) return;  // Expecting angle and distance; only distance used here
   uint8_t angleByte = Wire.read();      // Ignore angle for linear control
   uint8_t distanceByte = Wire.read();   // Use distance byte
 
   targetLiftSteps = map(distanceByte, 0, MAX_DISTANCE_BYTE, 0, MAX_LIFT_STEPS);
   newLiftCommand = true;
 
   Serial.print("[LINEAR I2C] Distance byte: ");
   Serial.print(distanceByte);
   Serial.print(" → Lift steps: ");
   Serial.println(targetLiftSteps);
 }
 