/* Purpose: This is a functional file to set up the Rotational Arduino as an I2C Slave 
         for receiving rotational commands from the Raspberry Pi and 
         controlling stepper motors for linear and rotational motion.
Contributors: Walter, Noah Kelly
Sources: SEED_LAB repository for previous examples
         IEEE 754 float conversion reference
         Arduino Wire Library Documentation (https://www.arduino.cc/reference/en/libraries/wire/)
         Stepper Library Documentation (https://www.arduino.cc/reference/en/libraries/stepper/)
Relevant Files: This file is related to the ARD_Comms.py file located in Demonstration/PI_code.
Circuitry: Connect the following listed pins for I2C communication:
   - A4 is SDA on Arduino, second pin from top on left (03) is SDA on Pi
   - A5 is SCL on Arduino, third pin from top on left (05) is SCL on Pi
   - Digital 2 on Arduino is the direction pin to connect to the driver
   - Digital 3 on Arduino is the Step pin to connect to the driver
   - Digital 11 on Arduino is the signal pin for the 0 degree end stop
   - Digital 12 on Arduino is the signal pin for the 90 degree end stop
   - GND on Arduino to GND bus for rotational end stops
   - 5V on Arduino to 5V bus for rotational end stops
   - Bus to pins for ground and 5V on the end stops
   - GND on Arduino to fifth pin from top left (09) on Pi
Libraries to be included:
  - Wire.h (For I2C communication)
  - Stepper.h (For controlling stepper motors) */



  #include <AccelStepper.h>

  #define STEPPER3_DIR_PIN 2
  #define STEPPER3_STEP_PIN 3
  #define ENDSTOP_0_SIGNAL_PIN 11
  #define ENDSTOP_90_SIGNAL_PIN 12
  
  #define ROT_ARD_ADD 8
  
  
  /* COM NOTES
  General: PI Probes ARD for value, sends int response based on status
  Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
  */ 
  
  const float lead_step = 0.01; // 0.01mm
  const int steps_rev = 400; // 1/2 microstep
  // Lead/Revolution = 2mm
  // Steps/Rev = 200 (no microstep)
  
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

  
  AccelStepper stepper_gear1(1,STEPPER3_STEP_PIN,STEPPER3_DIR_PIN);
  
  void setup() {
    // Declare pins as output
    stepper_gear1.setMaxSpeed(1000);
    stepper_gear1.setAcceleration(500);
    stepper_gear1.setCurrentPosition(0);
  }
  
  void loop() {
  
    stepper_moveMM(stepper_gear1, 2);
    delay(1000);
    stepper_moveMM(stepper_gear1, 0);
    delay(1000);
  }
  
  void stepper_moveMM (AccelStepper &stepper, float mm) {
    float steps = (mm*steps_rev)/(200*lead_step);
    stepper.moveTo(steps);
    stepper.runToPosition();
  }

  