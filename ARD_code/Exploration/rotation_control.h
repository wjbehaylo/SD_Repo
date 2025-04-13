/**
 * @file rotation_control.h
 * @brief Header for controlling Arduino B (rotation control)
 *
 * Hardware Connections (Arduino B - Rotation Control, I2C Address: 0x09):
 * - Stepper Driver:
 *     - STEP → pin 2
 *     - DIR  → pin 3
 * - I2C (shared with Pi and other Arduino):
 *     - SDA → A4
 *     - SCL → A5
 *     - GND shared with Raspberry Pi
 *
 * Function:
 * - Receives one byte from the Raspberry Pi: [angle_byte]
 * - Maps angle_byte (0–255) to a rotational step target (0–180° equivalent)
 * - Updates the target position for the rotational stepper motor.
 */

 #ifndef ROTATION_CONTROL_H
 #define ROTATION_CONTROL_H
 
 #include <AccelStepper.h>
 #include <Wire.h>
 
 // === Pin Definitions ===
 #define ROTATE_STEP_PIN 2
 #define ROTATE_DIR_PIN 3
 
 // === I2C Configuration ===
 #define ROTATION_I2C_ADDRESS 0x09  // Arduino B (rotation control)
 
 // === Rotation Limits ===
 const int MAX_ROTATE_STEPS = 200;   // Max steps for 180° rotation
 const int MAX_ANGLE_BYTE = 255;     // Max incoming angle byte from Pi
 
 // === Stepper Declaration ===
 extern AccelStepper rotateStepper;
 
 // === Shared State ===
 extern volatile int targetRotateSteps;
 extern volatile bool newRotateCommand;
 
 // === Function Prototypes ===
 void setupRotationStepper();
 void updateRotationStepper();
 void receiveRotationEvent(int howMany);
 
 #endif
 