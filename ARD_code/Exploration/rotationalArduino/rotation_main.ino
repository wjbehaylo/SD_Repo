/**
 * @file rotation_main.ino
 * @brief Main program for Arduino B (rotation control)
 *
 * Hardware Setup:
 * - This Arduino receives [angle_byte] from the Raspberry Pi over I2C.
 * - It maps the angle to stepper steps and rotates the arm accordingly.
 *
 * Stepper Driver Connections:
 *   Rotation Stepper:
 *     - STEP → pin 2
 *     - DIR  → pin 3
 *
 * I2C:
 *   - SDA  → A4
 *   - SCL  → A5
 *   - GND shared with Raspberry Pi
 *
 * Usage:
 *   - Upload this along with rotation_control.h/.cpp
 *   - Use Raspberry Pi to send angle_byte
 */

#include "rotation_control.h"
#include "rotation_endstop.h"

void setup() {
  Serial.begin(9600);
  setupRotationStepper();
  setupRotationEndstops();
  Wire.begin(ROTATION_I2C_ADDRESS);
  Wire.onReceive(receiveRotationEvent);
}

void loop() {
  if (rotationEndstopPressed()) {
    Serial.println("Rotation end stop triggered — halting motor");
    rotateStepper.stop();
  } else {
    updateRotationStepper();
  }
}
