/* 
Force sensor reading code

Senses the amount of force applied to the linear soft pot reading by reading out an analog voltage
Reads up to 3N of Force

*/

int analogPin = A3; // potentiometer wiper (middle terminal) connected to analog pin 3
                    // outside leads to ground and +3.3V
int val = 0;  // variable to store the value read

void setup() {
  Serial.begin(9600);           //  setup serial
}

void loop() {
  val = analogRead(analogPin);  // read the input pin
  Serial.println(val);          // debug value
}