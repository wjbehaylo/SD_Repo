/*
  Force‐Sensor Switch Setup:

  Breadboard Rails:
    +5V rail (top) ← Arduino 5V
    GND rail (bottom) ← Arduino GND

  Each SoftPot (force sensor) has 3 pins:
    • Pin 1 (outer)    → GND rail
    • Pin 3 (outer)    → +5V rail
    • Pin 2 (middle)   → Analog input (A0–A3)

  Pull‐down resistor:
    • 10 kΩ from each Pin 2 row to GND rail (prevents floating)

  Arduino connections:
    A0 ← Sensor 1 Pin 2
    A1 ← Sensor 2 Pin 2
    A2 ← Sensor 3 Pin 2
    A3 ← Sensor 4 Pin 2

  Calibration:
    1. Run a simple analog‐read sketch
    2. Note unpressed (≈100–200) vs. pressed (≈800–900)
    3. Set THRESHOLD ≈ midpoint (e.g. 500–700)

*/
const int sensorPins[4] = { A1, A2, A3 };
const unsigned long PHASE_MS = 5000;

void setup() {
  Serial.begin(9600);
  while (!Serial) {}  
  Serial.println("\n=== Auto-Calibration ===");

  int minVal[3], maxVal[3];
  for (int i = 0; i < 3; i++) {
    minVal[i] = 1023;
    maxVal[i] = 0;
  }

  // Phase 1: baseline
  Serial.println("Phase 1: leave UNPRESSED");
  unsigned long start = millis();
  while (millis() - start < PHASE_MS) {
    for (int i = 0; i < 3; i++) {
      int v = analogRead(sensorPins[i]);
      minVal[i] = min(minVal[i], v);
    }
    delay(50);
  }

  // Phase 2: pressed
  Serial.println("Phase 2: press FULLY");
  start = millis();
  while (millis() - start < PHASE_MS) {
    for (int i = 0; i < 3; i++) {
      int v = analogRead(sensorPins[i]);
      maxVal[i] = max(maxVal[i], v);
    }
    delay(50);
  }

  Serial.println("\nResults:");
  for (int i = 0; i < 3; i++) {
    int thresh = (minVal[i] + maxVal[i]) / 2;
    Serial.print("Sensor ");
    Serial.print(i);
    Serial.print(": baseline=");
    Serial.print(minVal[i]);
    Serial.print(", pressed=");
    Serial.print(maxVal[i]);
    Serial.print(" → thresh≈");
    Serial.println(thresh);
  }
  Serial.println("\nTake the lowest of these thresholds as your global FORCE_THRESHOLD.");
}

void loop() {
  // done
}

