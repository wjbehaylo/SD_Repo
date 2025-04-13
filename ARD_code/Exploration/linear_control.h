/**
 * @file linear_control.h
 * @brief
 *   Header file for the Linear Arduino that controls two synchronized lift stepper motors.
 *   Declares pin configurations, stepper settings, I2C address, and shared state variables.
 *
 * Description:
 *   - Receives `distance_byte` from Raspberry Pi via I2C
 *   - Maps the byte (0–255) to a vertical range using `MAX_LIFT_STEPS`
 *   - Controls two AccelStepper objects (left + right lift motors)
 *
 * Hardware:
 *   - Lift Stepper 1:
 *       STEP → pin 4
 *       DIR  → pin 5
 *   - Lift Stepper 2:
 *       STEP → pin 6
 *       DIR  → pin 7
 *   - I2C:
 *       Address: 0x08
 *       SDA (A4), SCL (A5), GND shared with Raspberry Pi
 *
 * Constants:
 *   - MAX_LIFT_STEPS defines the max vertical range of motion
 *   - MAX_DISTANCE_BYTE defines the resolution of byte input
 */
#ifndef LINEAR_CONTROL_H
#define LINEAR_CONTROL_H

#include <AccelStepper.h>
#include <Wire.h>

// === Pin Definitions ===
#define LIFT1_STEP_PIN  4
#define LIFT1_DIR_PIN   5
#define LIFT2_STEP_PIN  6
#define LIFT2_DIR_PIN   7

#define I2C_ADDRESS 0x08  // I2C address Arduino listens on

// === Step and Byte Limits ===
const int MAX_LIFT_STEPS = 1000;    // Max travel for veritcle lift
const int MAX_DISTANCE_BYTE = 255;  // Max incoming distance byte from Pi

// === Stepper Declarations ===
extern AccelStepper liftStepper1;
extern AccelStepper liftStepper2;

// === Shared State ===
extern volatile int targetLiftSteps;
extern volatile bool newLiftCommand;

// === Function Prototypes ===
void setupSteppers();
void updateSteppers();
void receiveLinearEvent(int howMany);

#endif
