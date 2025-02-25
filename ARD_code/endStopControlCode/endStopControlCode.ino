/* 
LimitSwitch

Turns off motor is limit switch is pressed, otherwise motor will continue running
*/


/* 
LimitSwitch

Stops motor when any limit switch is pressed, otherwise motor continues running. 
HIGH means the limit switch is NOT pressed. 
LOW means the switch is pressed.
*/

#define LIMIT_SWITCH_PIN1 7  // Limit switch 1 connected to pin 7
#define LIMIT_SWITCH_PIN2 8  // Limit switch 2 connected to pin 8
#define LIMIT_SWITCH_PIN3 12 // Limit switch 3 connected to pin 12
#define LIMIT_SWITCH_PIN4 13 // Limit switch 4 connected to pin 13

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
  if (currentState1 != lastState1 || currentState2 != lastState2 ||
      currentState3 != lastState3 || currentState4 != lastState4) {
    lastDebounceTime = millis();
  }

  // Wait for debounce delay
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (currentState1 == LOW || currentState2 == LOW || 
        currentState3 == LOW || currentState4 == LOW) {
      Serial.println("A limit switch is PRESSED. Stopping motor.");
      digitalWrite(MOTOR_PIN, LOW);  // Stop motor
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

