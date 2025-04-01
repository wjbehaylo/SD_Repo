/* 
Control code for the end stops

Turns off motor is end stop is pressed, otherwise motor will continue running

Stops motor when any end stop is pressed, otherwise motor continues running. 
HIGH means the end stop is NOT pressed. 
LOW means the switch is pressed.
*/

#define LIMIT_SWITCH_PIN1 7  // Limit switch 1 connected to pin 7, currentState 1
#define LIMIT_SWITCH_PIN2 8  // Limit switch 2 connected to pin 8, currentState 2
#define LIMIT_SWITCH_PIN3 12 // Limit switch 3 connected to pin 12, currentState 3
#define LIMIT_SWITCH_PIN4 13 // Limit switch 4 connected to pin 13, currentState 4

#define MOTOR_PIN 9  // Motor control pin

void setup() {
  Serial.begin(9600);

  // Set limit switch pins as inputs
  pinMode(LIMIT_SWITCH_PIN1, INPUT_PULLUP);
  pinMode(LIMIT_SWITCH_PIN2, INPUT_PULLUP);
  pinMode(LIMIT_SWITCH_PIN3, INPUT_PULLUP);
  pinMode(LIMIT_SWITCH_PIN4, INPUT_PULLUP);

  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, HIGH); // Start motor by default
}

void loop() {
  static int lastState1 = HIGH, lastState2 = HIGH, lastState3 = HIGH, lastState4 = HIGH;
  static unsigned long lastDebounceTime = 0;
  const unsigned long debounceDelay = 50; // 50 ms debounce delay

  int currentState1 = digitalRead(LIMIT_SWITCH_PIN1);
  int currentState2 = digitalRead(LIMIT_SWITCH_PIN2);
  int currentState3 = digitalRead(LIMIT_SWITCH_PIN3);
  int currentState4 = digitalRead(LIMIT_SWITCH_PIN4);

  // Check if any switch state has changed
  if (currentState1 != lastState1) {
    lastDebounceTime = millis();
  }
  else if (currentState2 != lastState2) {
    lastDebounceTime = millis();
  }
  else if (currentState3 != lastState3) {
    lastDebounceTime = millis();
  } 
  else if (currentState4 != lastState4) {
        lastDebounceTime = millis();
  }

  // Wait for debounce delay
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (currentState1 == LOW) {
      Serial.println("Current limit switch 1 is PRESSED. Stopping motor.");
      digitalWrite(MOTOR_PIN, LOW);  // Stop motor
    } else if (currentState2 == LOW) {
      Serial.println("Current limit switch 2 is PRESSED. Stopping motor.");
      digitalWrite(MOTOR_PIN, LOW);  // Stop motor
    } else if (currentState3 == LOW) {
      Serial.println("Current limit switch 3 is PRESSED. Stopping motor.");
      digitalWrite(MOTOR_PIN, LOW); // Stop motor
    } else if (currentState4 == LOW) {
      Serial.println("Current limit switch 4 is PRESSED. Stopping motor.");
      digitalWrite(MOTOR_PIN, LOW); // Stop motor
  } else {
    Serial.println("All limit switches are UNTOUCHED. Running motor.");
    digitalWrite(MOTOR_PIN, HIGH); // Run motor
  }
  }

  // Update last states
  lastState1 = currentState1;
  lastState2 = currentState2;
  lastState3 = currentState3;
  lastState4 = currentState4;

  delay(100); // Small delay to prevent flooding Serial Monitor
}

