/* Purpose: This is a functional file to set up the Arduino as an I2C Slave 
         for receiving movement commands from the Raspberry Pi and 
         controlling stepper motors for linear and rotational motion.
Contributors: Angela
Sources: SEED_LAB repository for previous examples
         IEEE 754 float conversion reference
         Arduino Wire Library Documentation (https://www.arduino.cc/reference/en/libraries/wire/)
         Stepper Library Documentation (https://www.arduino.cc/reference/en/libraries/stepper/)
Relevant Files: This file is related to the ARD_Comms.py file located in Demonstration/PI_code.
Circuitry: Connect the following listed pins for I2C communication:
   - A4 is SDA on Arduino, second pin from top on left (03) is SDA on Pi
   - A5 is SCL on Arduino, third pin from top on left (05) is SCL on Pi
   - GND on Arduino to fifth pin from top left (09) on Pi
Libraries to be included:
  - Wire.h (For I2C communication)
  - Stepper.h (For controlling stepper motors) 
  - MultiStepper.h (For multiple steppers at same or different speeds) */

// Libraries
#include <Wire.h>
#include <AccelStepper.h>
#include <MultiStepper.h>  

// ============================ I2C ADDRESSES ============================
// These addresses must match the ones used in the Raspberry Pi code.
#define LIN_ARD_ADD 15  // I2C Address linear movement
#define ROT_ARD_ADD 8   // I2C Address rotational movement

// ============================ STEPPER MOTOR SETUP ============================
// Define motor pins for linear motion 
#define STEPPER1_STEP_PIN 2
#define STEPPER1_DIR_PIN 3
#define STEPPER2_STEP_PIN 5
#define STEPPER2_DIR_PIN 4
// Define motor pins for rotational motion 
#define STEPPER3_DIR_PIN 7
#define STEPPER3_STEP_PIN 6

const float lead_step = 0.01; // 0.01mm, not sure how to use this atm
const int STEPS_PER_REV = 400; // 1/2 microstep
const float DEG_TO_STEP = STEPS_PER_REV / 360.0;  // convert degrees to steps


// initialize stepper motors 
AccelStepper stepper1(AccelStepper::DRIVER, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
AccelStepper stepper2(AccelStepper::DRIVER, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);
AccelStepper stepper3(AccelStepper::DRIVER, STEPPER3_STEP_PIN, STEPPER3_DIR_PIN);
MultiStepper steppers_lin; //Multi-stepper controller for synchronized motion 

// Variables for received I2C data
volatile byte receivedOffset = 0;
uint8_t receivedData[4];  // Buffer for incoming data (4 bytes for IEEE float)
float moveAmount = 0.0;   // Stores movement amount (in steps or degrees)
int status = 0;           // Status variable to be sent to Raspberry Pi
bool newData = false;  // Flag to indicate new data received

// ============================ FUNCTION DECLARATIONS ============================
void receiveData(int byteCount);
void requestEvent();
float convertBytesToFloat(uint8_t bytes[4]);
void moveLinear(int pair, float steps);
void moveRotational(float degrees);
void handleCommand();

// ============================ SETUP FUNCTION ============================
void setup() {
    Wire.begin(LIN_ARD_ADD);  // linear movement address for I2C comms
    Wire.onReceive(receiveData);
    Wire.onRequest(requestEvent);

    Serial.begin(9600); 
    Serial.println("Arduino I2C Initialized.");

    //Stepper motor setup
    stepper1.setMaxSpeed(1000);
    stepper1.setAcceleration(500);
    stepper1.setCurrentPosition(0);
    stepper2.setMaxSpeed(1000);
    stepper2.setAcceleration(500);
    stepper2.setCurrentPosition(0);
    stepper3.setMaxSpeed(1000);
    stepper3.setAcceleration(500);
    stepper3.setCurrentPosition(0);
    
    //Add linear steppers to multistepper group
    steppers_lin.addStepper(stepper1);
    steppers_lin.addStepper(stepper2);

}

// ============================ MAIN LOOP ============================
void loop() {
    // Process new commands when data is received
    if (newData) {
        handleCommand();
        newData = false;
  }
    stepper1.run();
    stepper2.run();
    stepper3.run();
}

// ============================ I2C COMMAND HANDLER FUNCTION ============================
void handleCommand() {
  switch (receivedOffset) {
    case 0:
      stepper_moveMM(stepper1, receivedValue); // Move linear motor 1
      break;
    case 1:
      stepper_moveMM(stepper2, receivedValue); // Move linear motor 2
      break;
    case 2:
      steppers_moveMM(steppers_lin, receivedValue); // Move both linear motors
      break;
    case 3:
      stepper_moveMM(stepper3, receivedValue); // Move gear motor
      break;
    default:
      Serial.println("Unrecognized command");
  }
}

// ============================ I2C RECEIVE EVENT HANDLER FUNCTION ============================
void receiveData(int byteCount) {
    if (byteCount >= 5) {  
        receivedOffset = Wire.read();  // Read the first byte (Offset: identifies command type)

        // read the next 4 bytes (movement amount in IEEE 754 float format)
        for (int i = 0; i < 4; i++) {
            receiveData[i] = Wire.read();
        }

        // Convert received bytes into a float value
        moveAmount = convertBytesToFloat(receivedData);

        Serial.print("Received Offset: ");
        Serial.print(receivedOffset);
        Serial.print(" | Move Amount: ");
        Serial.println(moveAmount);
        newData = true;  // Set flag to indicate new data received
    }
}

// ============================ I2C REQUEST FUNCTION ============================
void requestEvent() {
    status = 0;
    if (stepper1.distanceToGo() != 0) status |= 0x01;
    if (stepper2.distanceToGo() != 0) status |= 0x02;
    if (stepper3.distanceToGo() != 0) status |= 0x04;

    Wire.write(status);  
    Serial.print("Sending Status: ");
    Serial.println(status);
}

// ============================ IEEE 754 BYTE TO FLOAT CONVERSION ============================
// convert 4-byte IEEE 754 encoded number into a float
float convertBytesToFloat(uint8_t bytes[4]) {
    union {
        uint8_t byteArray[4];
        float floatValue;
    } converter;

    // Copy the received bytes into the union structure
    for (int i = 0; i < 4; i++) {
        converter.byteArray[i] = bytes[i];
    }

    return converter.floatValue;  // Return the converted float value
}

// ============================ COMMAND HANDLING FUNCTION ============================
// Determines which movement function to call based on received offset
void handleCommand() {
    switch (receivedOffset) {
        case 0:
            Serial.println("Moving Linear Stepper 1...");
            moveLinear(0, moveAmount);
            break;
        case 1:
            Serial.println("Moving Linear Stepper 2...");
            moveLinear(1, moveAmount);
            break;
        case 2:
            Serial.println("Moving Both Linear Steppers...");
            moveLinear(0, moveAmount);
            moveLinear(1, moveAmount);
            break;
        case 10:
            Serial.println("Rotating Motor...");
            moveRotational(moveAmount);
            break;
        default:
            Serial.println("Unrecognized command");
    }
}

// ============================ LINEAR MOVEMENT FUNCTION ============================
void moveLinear(int pair, float steps) {
    int moveSteps = (int)steps;  // Convert float steps to integer

    if (pair == 0) {
        Serial.print("Moving Stepper 1 by ");
        Serial.print(moveSteps);
        Serial.println(" steps.");
        stepper1.move(moveSteps);
    } 
    else if (pair == 1) {
        Serial.print("Moving Stepper 2 by ");
        Serial.print(moveSteps);
        Serial.println(" steps.");
        stepper2.move(moveSteps);
    } 
    else {
        Serial.println("Invalid pair selected for movement!");
        status = 5;  // Error code for invalid command
    }
}

// ============================ ROTATIONAL MOVEMENT FUNCTION ============================
// Simulates rotating a motor by a specified number of degrees
void moveRotational(float degrees) {
    int steps = (int)(degrees * DEG_TO_STEP);  // Convert degrees to steps
    Serial.print("Rotating by ");
    Serial.print(degrees);
    Serial.println(" degrees.");
    stepper3.move(steps);  
}
