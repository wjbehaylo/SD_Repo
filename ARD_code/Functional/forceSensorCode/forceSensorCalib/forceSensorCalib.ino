// put this at the top with your other defines/calibration:
const int FORCE_RAW_THRESH = 600;  // tune this to your mid-point
#define NUM_SENSORS 4
const int FORCE_PINS[NUM_SENSORS] = { FORCE0_PIN, FORCE1_PIN, FORCE2_PIN, FORCE3_PIN };

// call this once in setup() after Serial.begin():
void testForceSensors() {
  Serial.println(F("=== Force Sensor Test ==="));
  for (int i = 0; i < NUM_SENSORS; i++) {
    int raw = analogRead(FORCE_PINS[i]);
    bool pressed = (raw > FORCE_RAW_THRESH);
    Serial.print(F("Sensor "));
    Serial.print(i);
    Serial.print(F(": raw="));
    Serial.print(raw);
    Serial.print(pressed ? F("  PRESSED") : F("  free"));
    Serial.println();
  }
  Serial.println();
}
