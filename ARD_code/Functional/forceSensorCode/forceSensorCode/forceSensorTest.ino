#define FORCE0_PIN A0
#define FORCE1_PIN A1
#define FORCE2_PIN A2
#define FORCE3_PIN A3

const int FORCE_THRESH = 610;  // 0–1023 range, value from calibration

//initialize the force sensors
pinMode(FORCE0_PIN, INPUT);
pinMode(FORCE1_PIN, INPUT);
pinMode(FORCE2_PIN, INPUT);
pinMode(FORCE3_PIN, INPUT);

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
