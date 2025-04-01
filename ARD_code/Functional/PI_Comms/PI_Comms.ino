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
  - Stepper.h (For controlling stepper motors) */

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

const float lead_step = 0.01; // 0.01mm
const int STEPS_PER_REV = 400; // 1/2 microstep
const float DEG_TO_STEP = STEPS_PER_REV / 360.0;  // Conversion factor for degrees to steps

volatile union FloatUnion 
{
  uint8_t bytes[4];
  float floatValue;
} byteFloat;

/* This is how to use this FloatUnion to convert from the IEEE to integer ish form
byteFloat.bytes[0] = instruction[7];
    byteFloat.bytes[1] = instruction[6];
    byteFloat.bytes[2] = instruction[5];
    byteFloat.bytes[3] = instruction[4];
    recivedAngle = byteFloat.floatValue;
    byteFloat.bytes[0] = instruction[3];
    byteFloat.bytes[1] = instruction[2];
    byteFloat.bytes[2] = instruction[1];
    byteFloat.bytes[3] = instruction[0];
    recivedAngle = byteFloat.floatValue;
*/


// initialize stepper motors 
AccelStepper stepper1(AccelStepper::DRIVER, STEPPER1_STEP_PIN, STEPPER1_DIR_PIN);
AccelStepper stepper2(AccelStepper::DRIVER, STEPPER2_STEP_PIN, STEPPER2_DIR_PIN);
AccelStepper stepper3(AccelStepper::DRIVER, STEPPER3_STEP_PIN, STEPPER3_DIR_PIN);


// ============================ GLOBAL VARIABLES ============================
volatile uint8_t receivedData[4];  // buffer for incoming data (4 bytes for IEEE float)
volatile float moveAmount = 0.0;   // stores movement amount (in steps or degrees)
volatile int status = 0;           // status variable to be sent to RPI

// ============================ FUNCTION DECLARATIONS ============================
void receiveData(int byteCount);
void sendData();
float convertBytesToFloat(uint8_t bytes[4]);
void moveLinear(int pair, float steps);
void moveRotational(float degrees);

// ============================ SETUP FUNCTION ============================
void setup() {
    Wire.begin(LIN_ARD_ADD);  // Initialize as I2C Slave with linear movement address
    Wire.onReceive(receiveData);
    Wire.onRequest(sendData);
    
    Serial.begin(9600);  // Start serial for debugging

    stepper1.setSpeed(60);  // Set speed (RPM) for Stepper 1
    stepper2.setSpeed(60);  // Set speed (RPM) for Stepper 2

    Serial.println("Arduino I2C Initialized.");
}

// ============================ MAIN LOOP ============================
void loop() {
    // loop remains empty because the movement is handled in receiveData().
    // I2C functions execute automatically when data is received/requested.
}

// ============================ I2C RECEIVE FUNCTION ============================
// This function is triggered when Raspberry Pi sends data
void receiveData(int byteCount) {
    
    if (byteCount >= 5) {  
        uint8_t offset = Wire.read();  // Read the first byte (Offset: identifies command type)

        // read the next 4 bytes (movement amount in IEEE 754 float format)
        for (int i = 0; i < 4; i++) {
            receivedData[i] = Wire.read();
        }

        // Convert received bytes into a float value
        moveAmount = convertBytesToFloat(receivedData);

        Serial.print("Received Offset: ");
        Serial.print(offset);
        Serial.print(" | Move Amount: ");
        Serial.println(moveAmount);

        // ======================== LINEAR MOVEMENT ========================
        if (offset == 0) {
            Serial.println("Moving Pair 0...");
            moveLinear(0, moveAmount);
            status = 1;  // Movement complete
        } 
        else if (offset == 1) {
            Serial.println("Moving Pair 1...");
            moveLinear(1, moveAmount);
            status = 11;  // Movement complete
        } 
        else if (offset == 2) {
            Serial.println("Moving Both Pairs...");
            moveLinear(0, moveAmount);
            moveLinear(1, moveAmount);
            status = 21;  // Movement complete for both pairs
        } 
        // ======================== ROTATIONAL MOVEMENT ========================
        else if (offset == 10) {
            Serial.println("Rotating...");
            moveRotational(moveAmount);
            status = 21;  // Rotation success
        } 
        else {
            Serial.println("Unrecognized Command!");
            status = 5;  // Invalid command status
        }
    }
}

// ============================ I2C REQUEST FUNCTION ============================
// This function is triggered when Raspberry Pi requests the current status
void sendData() {
    Wire.write(status);  // Send the last updated status
    Serial.print("Sending Status: ");
    Serial.println(status);
}

// ============================ IEEE 754 BYTE TO FLOAT CONVERSION ============================
// This function converts a 4-byte IEEE 754 encoded number into a float
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

// ============================ LINEAR MOVEMENT FUNCTION ============================
// Controls the stepper motors for linear motion based on the received command
void moveLinear(int pair, float steps) {
    int moveSteps = (int)steps;  // Convert float steps to integer

    if (pair == 0) {
        Serial.print("Moving Stepper 1 by ");
        Serial.print(moveSteps);
        Serial.println(" steps.");
        stepper1.step(moveSteps);
    } 
    else if (pair == 1) {
        Serial.print("Moving Stepper 2 by ");
        Serial.print(moveSteps);
        Serial.println(" steps.");
        stepper2.step(moveSteps);
    } 
    else {
        Serial.println("Invalid pair selected for movement!");
        status = 5;  // Error code for invalid command
    }
}

// ============================ ROTATIONAL MOVEMENT FUNCTION ============================
// Simulates rotating a motor by a specified number of degrees
void moveRotational(float degrees) {
    int steps = (int)(degrees * (STEPS_PER_REV / 360.0));  // Convert degrees to steps

    Serial.print("Rotating by ");
    Serial.print(degrees);
    Serial.println(" degrees.");

    stepper1.step(steps);  // Assume single stepper for rotation
}
