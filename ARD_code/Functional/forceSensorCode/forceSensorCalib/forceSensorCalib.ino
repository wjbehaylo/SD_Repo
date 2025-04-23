// ——————— Multi‐Sensor Calibration & Force Conversion ———————

const int   NUM_SENSORS  = 4;
const int   sensorPins[NUM_SENSORS] = { A0, A1, A2, A3 };
const int   NUM_SAMPLES  = 100;   // how many ADC samples to average

// calibration storage
float raw0[NUM_SENSORS];   // ADC at 0 N
float raw1[NUM_SENSORS];   // ADC at known force F1
float m[NUM_SENSORS];      // slope for each sensor
float b[NUM_SENSORS];      // intercept for each sensor

float F1;  // the one known force (in N) you’ll use for all sensors

// ——————— Helper functions ———————
// average NUM_SAMPLES reads on sensor i
float readAvgRaw(int i) {
  long sum = 0;
  for (int k = 0; k < NUM_SAMPLES; k++) {
    sum += analogRead(sensorPins[i]);
    delay(2);
  }
  return sum / float(NUM_SAMPLES);
}

// wait for ENTER
void waitForEnter() {
  while (!Serial.available()) {}
  while (Serial.available()) Serial.read();
}

void setup() {
  Serial.begin(9600);
  delay(200);
  Serial.println("\n=== 4-Sensor Force Calibration ===");

  // 0) get your known weight once
  Serial.println("Enter your known force in newtons (e.g. 0.98) and press ENTER:");
  while (!Serial.available()) {}
  F1 = Serial.parseFloat();
  Serial.print("Using F1 = "); Serial.print(F1,3); Serial.println(" N\n");

  // 1) calibrate each sensor in turn
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print("Sensor "); Serial.print(i); Serial.println(" calibration:");
    
    // no-load
    Serial.println("  Remove all load and press ENTER.");
    waitForEnter();
    raw0[i] = readAvgRaw(i);
    Serial.print("    raw0 = "); Serial.println(raw0[i],2);

    // known-load
    Serial.println("  Place weight on sensor and press ENTER.");
    waitForEnter();
    raw1[i] = readAvgRaw(i);
    Serial.print("    raw1 = "); Serial.println(raw1[i],2);

    // compute m, b
    m[i] =  F1 / (raw1[i] - raw0[i]);
    b[i] = -m[i] * raw0[i];
    Serial.print("    m = "); Serial.println(m[i],6);
    Serial.print("    b = "); Serial.println(b[i],6);
    Serial.println();
  }

  Serial.println("=== Calibration Complete ===\n");
}

void loop() {
  // read & convert all sensors
  for (int i = 0; i < NUM_SENSORS; i++) {
    float raw = readAvgRaw(i);
    float forceN = m[i]*raw + b[i];
    if (forceN < 0) forceN = 0;               // clamp
    Serial.print("S"); Serial.print(i);
    Serial.print(" raw="); Serial.print(raw,1);
    Serial.print(" → F="); Serial.print(forceN,3);
    Serial.print(" N   ");
  }
  Serial.println();
  delay(200);
}
