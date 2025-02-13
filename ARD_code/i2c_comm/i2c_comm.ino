#include <Wire.h>
#define MY_ADDR 8
#define LED_OFFSET 1
#define STR_OFFSET 2
// Global variables to be used for I2C communication
volatile uint8_t offset = 0;
volatile uint8_t reply = 0;

volatile uint8_t instruction[32] = {0};
volatile uint8_t msgLength = 0;
void setup() {
  Serial.begin(9600);
  // We want to control the built-in LED (pin 13)
  pinMode(LED_BUILTIN, OUTPUT);
  // Initialize I2C
  Wire.begin(MY_ADDR);
  // Set callbacks for I2C interrupts
  Wire.onReceive(receive);
  Wire.onRequest(request);
}
void loop() {
  // If there is data on the buffer, read it
  if (msgLength > 0) {
    if (offset==LED_OFFSET){ 
      //in theory, sending null character '\0' would turn it one way, anything else would turn it the other
      digitalWrite(LED_BUILTIN,instruction);
    }
    printReceived();
    msgLength = 0;
  }
}
// printReceived helps us see what data we are getting from the leader
void printReceived() {
  // Print on serial console
  Serial.print("Offset received: ");
  Serial.println(offset);
  Serial.print("Message Length: ");
  Serial.println(msgLength);
  Serial.print("Instruction received: ");
  for (int i=0;i<msgLength;i++) {
    Serial.print(String(instruction[i])+"\t");
  }
  Serial.println("");
}
// function called when an I2C interrupt event happens
void receive() {
  // Set the offset, this will always be the first byte.
  offset = Wire.read();
  // If there is information after the offset, it is telling us more about the command.
  while (Wire.available()) {
    instruction[msgLength] = Wire.read();
    msgLength++; //after each byte is read, update the length of the message accordingly
  }
  
}
void request() {
  // According to the Wire source code, we must call write() within the requesting ISR
  // and nowhere else. Otherwise, the timing does not work out. See line 238:
  // https://github.com/arduino/ArduinoCore-avr/blob/master/libraries/Wire/src/Wire.cpp
  
  //theoretically, it would send a constant status when probed, which would update when the system has successfully captured the debris or failed to. It could also be other stuff for like arm movement and whatnot.
  
  number=1; //for now we will send a '1'
  Serial.print("Sending: ");
  Serial.print(number);
  Wire.write(number);
}
