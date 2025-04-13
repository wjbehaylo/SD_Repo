/**
 * @file linear_endstop.cpp
 * @brief
 *   Implements the logic for detecting state changes from 4 limit switches.
 *   Stops motion if any are triggered.
 *
 * This version is for Arduino A (Linear movement control).
 */

 #include "linear_endstop.h"

 static int lastState1 = HIGH, lastState2 = HIGH, lastState3 = HIGH, lastState4 = HIGH;
 static unsigned long lastDebounceTime = 0;
 
 void setupEndstops() {
   pinMode(LIMIT_SWITCH_1, INPUT_PULLUP);
   pinMode(LIMIT_SWITCH_2, INPUT_PULLUP);
   pinMode(LIMIT_SWITCH_3, INPUT_PULLUP);
   pinMode(LIMIT_SWITCH_4, INPUT_PULLUP);
 }
 
 // Returns true if any limit switch is pressed (LOW)
 bool anyEndstopPressed() {
   int currentState1 = digitalRead(LIMIT_SWITCH_1);
   int currentState2 = digitalRead(LIMIT_SWITCH_2);
   int currentState3 = digitalRead(LIMIT_SWITCH_3);
   int currentState4 = digitalRead(LIMIT_SWITCH_4);
 
   bool changed = (currentState1 != lastState1) || (currentState2 != lastState2) ||
                  (currentState3 != lastState3) || (currentState4 != lastState4);
 
   if (changed) lastDebounceTime = millis();
 
   lastState1 = currentState1;
   lastState2 = currentState2;
   lastState3 = currentState3;
   lastState4 = currentState4;
 
   if ((millis() - lastDebounceTime) > debounceDelay) {
     return (currentState1 == LOW || currentState2 == LOW ||
             currentState3 == LOW || currentState4 == LOW);
   }
 
   return false;
 }
 