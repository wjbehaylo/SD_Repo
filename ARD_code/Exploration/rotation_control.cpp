/**
 * @file rotation_control.cpp
 * @brief Implements control of a single stepper motor for rotational movement.
 *
 * Hardware Connections (Arduino B - Rotation Control, I2C Address: 0x09):
 * - Stepper Driver:
 *     - STEP → pin 2
 *     - DIR  → pin 3
 * - I2C (shared with Raspberry Pi and linear Arduino):
 *     - SDA → A4
 *     - SCL → A5
 *     - GND shared with Raspberry Pi
 * - ENDSTOPS :
 *     - LIMIT_SWITCH_1 → pin D11, GND, 5V
 *     - LIMIT_SWITCH_2 → pin D12, GND, 5V
 *
 * Functionality:
 * - Receives one byte via I2C: [angle_byte]
 * - Maps angle_byte (0–255) to target steps (0–200 for 0–180° rotation)
 * - Commands rotation stepper motor to move to calculated target using AccelStepper
 */

 #include "rotation_control.h"

 // Instantiate the rotation stepper
 AccelStepper rotateStepper(AccelStepper::DRIVER, ROTATE_STEP_PIN, ROTATE_DIR_PIN);
 
 volatile int targetRotateSteps = 0;
 volatile bool newRotateCommand = false;
 
 void setupRotationStepper() {
   rotateStepper.setMaxSpeed(500);
   rotateStepper.setAcceleration(100);
   rotateStepper.setCurrentPosition(0);
 }
 
 void updateRotationStepper() {
   rotateStepper.moveTo(targetRotateSteps);
   rotateStepper.run();
 }
 
 void receiveRotationEvent(int howMany) {
   if (howMany < 1) return;  // Only angle byte is needed for rotation
   uint8_t angleByte = Wire.read();
 
   targetRotateSteps = map(angleByte, 0, MAX_ANGLE_BYTE, 0, MAX_ROTATE_STEPS);
   newRotateCommand = true;
 
   Serial.print("[ROTATION I2C] Angle byte: ");
   Serial.print(angleByte);
   Serial.print(" → Rotate steps: ");
   Serial.println(targetRotateSteps);
 }
 