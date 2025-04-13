/**
 * @file rotation_endstop_control.cpp
 * @brief
 *   Implements debounced input from 2 end stops to limit rotation.
 *   Designed for Arduino B handling 180° sweep control.
 */

 #include "rotation_endstop_control.h"

 static int lastLeftState = HIGH, lastRightState = HIGH;
 static unsigned long lastDebounceTime = 0;
 
 void setupRotationEndstops() {
   pinMode(ROTATE_LIMIT_LEFT, INPUT_PULLUP);
   pinMode(ROTATE_LIMIT_RIGHT, INPUT_PULLUP);
 }
 
 // Returns true if either left or right rotation limit is triggered
 bool rotationEndstopPressed() {
   int left = digitalRead(ROTATE_LIMIT_LEFT);
   int right = digitalRead(ROTATE_LIMIT_RIGHT);
 
   if ((left != lastLeftState) || (right != lastRightState)) {
     lastDebounceTime = millis();
   }
 
   lastLeftState = left;
   lastRightState = right;
 
   if ((millis() - lastDebounceTime) > ROTATE_DEBOUNCE_DELAY) {
     return (left == LOW || right == LOW);
   }
 
   return false;
 }
 