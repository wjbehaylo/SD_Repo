/**
 * @file linear_main.ino
 * @brief
 *   Main entry point for the Linear Arduino (address 0x08) that controls
 *   two synchronized stepper motors for vertical (linear) movement.
 *
 * Description:
 *   - Receives two bytes from Raspberry Pi via I2C:
 *       [angle_byte, distance_byte]
 *     Only the second byte (distance_byte) is used for lift control.
 *   - Uses the AccelStepper library to move both motors in sync with acceleration.
 *
 * Hardware Connections:
 *   - Lift Stepper 1 (left):
 *       STEP → pin 4
 *       DIR  → pin 5
 *   - Lift Stepper 2 (right):
 *       STEP → pin 6
 *       DIR  → pin 7
 *   - I2C Bus (shared with rotation Arduino):
 *       SDA  → Arduino A4 (connect to Pi SDA)
 *       SCL  → Arduino A5 (connect to Pi SCL)
 *       GND  → shared ground with Raspberry Pi
 *
 * Usage:
 *   1. Upload this sketch (with `linear_control.h/.cpp`) to the linear Arduino.
 *   2. Ensure I2C address is set to 0x08.
 *   3. Send [angle, distance] bytes from the Pi — only distance will affect the motors.
 */

#include "linear_control.h"

void setup() {
  Serial.begin(9600);
  Serial.println("[LINEAR] Linear Lift Control Initialized");

  setupLinearSteppers();
  Wire.begin(LINEAR_I2C_ADDRESS);
  Wire.onReceive(receiveLinearEvent);
}

void loop() {
  updateLinearSteppers();
}

