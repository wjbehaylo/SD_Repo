void testForceSensors() {
  Serial.println(F("\n--- Force Sensor Raw Readings ---"));
  Serial.print(F("  [0]: ")); Serial.println(analogRead(FORCE0_PIN));
  Serial.print(F("  [1]: ")); Serial.println(analogRead(FORCE1_PIN));
  Serial.print(F("  [2]: ")); Serial.println(analogRead(FORCE2_PIN));
  Serial.print(F("  [3]: ")); Serial.println(analogRead(FORCE3_PIN));
  delay(500);  // half-second between samples
}

void loop() {
  testForceSensors();
  // once you see non-zero readings, comment out testForceSensors() 
  // and return to your FSM logic
}
