/**
 * @file rotation_endstop_control.h
 * @brief
 *   Header for managing 2 end stops on the Rotational Arduino (Arduino B).
 *   These define the angular boundaries of rotation (e.g. 0° and 180°).
 *
 * Usage:
 *   - Stops rotational motion if either limit switch is pressed.
 *
 * Hardware (for Arduino B - Rotation Control):
 *   ROTATE_LIMIT_LEFT  → pin D10 (e.g., 0° limit)
 *   ROTATE_LIMIT_RIGHT → pin D11 (e.g., 180° limit)
 *
 * Switch Logic:
 *   - HIGH = not pressed
 *   - LOW  = pressed → stop rotation
 */

 #ifndef ROTATION_ENDSTOP_CONTROL_H
 #define ROTATION_ENDSTOP_CONTROL_H
 
 #include <Arduino.h>
 
 // Pin assignments for rotation limits
 #define ROTATE_LIMIT_LEFT 10
 #define ROTATE_LIMIT_RIGHT 11
 
 const unsigned long ROTATE_DEBOUNCE_DELAY = 50;
 
 void setupRotationEndstops();
 bool rotationEndstopPressed();
 
 #endif
 