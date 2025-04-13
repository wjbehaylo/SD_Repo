/**
 * @file linear_endstop.h
 * @brief 
 *   Header for managing 4 limit switches on the Linear Arduino (Arduino A).
 *   Each switch halts stepper movement when pressed.
 *
 * Usage:
 *   - Called from loop() to stop liftStepper1 and liftStepper2 if any limit is triggered.
 *   - Uses input pullups and debouncing for clean edge detection.
 *
 * Hardware (for Arduino A - Linear Control):
 *       LIMIT_SWITCH_1 → pin D10, GND, 5V
 *       LIMIT_SWITCH_2 → pin D11, GND, 5V
 *       LIMIT_SWITCH_3 → pin D12, GND, 5V
 *       LIMIT_SWITCH_4 → pin D13, GND, 5V
 *
 * Switch Logic:
 *   - HIGH = not pressed
 *   - LOW  = pressed → motor should stop
 */

 #ifndef ENDSTOP_CONTROL_H
 #define ENDSTOP_CONTROL_H
 
 #include <Arduino.h>
 
 // Pin assignments for limit switches
 #define LIMIT_SWITCH_1 10
 #define LIMIT_SWITCH_2 11
 #define LIMIT_SWITCH_3 12
 #define LIMIT_SWITCH_4 13
 
 const unsigned long debounceDelay = 50;  // debounce time in ms
 
 void setupEndstops();
 bool anyEndstopPressed();
 
 #endif
 