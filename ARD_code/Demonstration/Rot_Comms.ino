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
  #include <Wire.h>

  #define STEPPER3_DIR_PIN 2
  #define STEPPER3_STEP_PIN 3
  #define ENDSTOP_0_SIGNAL_PIN 11
  #define ENDSTOP_90_SIGNAL_PIN 12
  
  #define ROT_ARD_ADD 8
  
  
  /* COM NOTES
  General: PI Probes ARD for value, sends int response based on status
  Rotational: Rotate to end stop, set position to 0. Get degrees from PI and rotate. Rotate to "plus" from anywhere
  */ 
  
  //Constants to be used
  const float lead_step = 0.01; // 0.01mm
  const int steps_rev = 400; // 1/2 microstep
  const int configurationPlus = 45; //target degrees for plus configuration
  const int configurationEquals = 0; //target degrees for equal configuration
  // Lead/Revolution = 2mm
  // Steps/Rev = 200 (no microstep)
  
  //this is for the FSM states
  //WAIT is while the Arduino is on and waiting for instructions
  //MOVING is while the Arduino is moving its amount
  //DONE is when it is done moving for whatever reason, and waiting for Pi to ask result
  typedef enum {WAIT, MOVING, DONE} state;

  //STATICS are for tracking state information, since they can change between function calls
  static float currentAngle; //actual angle in degrees
  //VOLATILES are for things that could change outside of standard execution from like interrupts
  //I2C
  volatile uint8_t offset = 0; //offset of the message
  /*OFFSET, from ARD_Comms.py
    0:
        rotate a number of degrees, specified in 'rotate_amount' global variable
        this could either be an integer number, or we could use IEEE encoding to send over an accurate float if necessary
    1:
        send it to = configuration
        so the content shouldn't matter
    2:
        send it to + configuration
        so the content shouldn't matter again
  */

  volatile uint8_t instruction[32] = {0}; //content of the message
  volatile uint8_t messageLength=0; //length of the message sent
  volatile uint8_t newMessage=0; //1 when we have a message to interpret
  volatile float targetAngle; //angle that we should move to.
  volatile uint8_t executionStatus=20; //the status of the capturing execution
  volatile uint8_t messageReceived=0; //1 if the Pi has prompted the non 20 status, indicating that 'DONE' state is done
  short ctrlBusy=0; //whether or not the control system is actively busy or not
  short ctrlDone=0; //whether or not the control system is done (1) or not.
  volatile bool triggered0 = false;
  volatile bool triggered90 = false;
  /*
  STATUSES:
  status == 20:
    return ""  # Do not populate if divisible by 10
  status == 21:
    status_string = "Rotation success"
  status == 22:
    status_string = "Configuration success"
  status == 23:
    status_string = "(0) End stop hit"
  status == 24:
    status_string = "(90) End stop hit"
  status == 25:
    status_string = "Rotational unrecognized command"
  */

  //this is for interpretting the data sent from PI
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
    // Declare pins as output for the motor
    stepper_gear1.setMaxSpeed(1000);
    stepper_gear1.setAcceleration(500);
    stepper_gear1.setCurrentPosition(0);

    //declare pins for the end stops
    //I'm not sure what Input_Pullup is, I think it is that if input is 1 (pressed) it sets the logic to 1
    pinMode(ENDSTOP_0_SIGNAL_PIN, INPUT_PULLUP);
    pinMode(ENDSTOP_90_SIGNAL_PIN, INPUT_PULLUP);
    
    //I am declaring those pins as interrupts so that they can set global flags that will stop movement
    /*
    note a slight concern I am having is that if the movement is started when one is triggered it might be immediately stopped, functionally trapping us there. 
    this could be fixed maybe by calculating if the desired angle after math will extend beyond 90/0 degrees
    */
    //RISING because the end stops are active high
    attachInterrupt(digitalPinToInterrupt(ENDSTOP_0_SIGNAL_PIN), triggered0Interrupt, RISING);
    attachInterrupt(digitalPinToInterrupt(ENDSTOP_90_SIGNAL_PIN), triggered90Interrupt, RISING);


    //initialize the I2C slave
    Wire.begin(ROT_ARD_ADD); 
    Wire.onReceive(PiDataReceive); //this is triggered when Raspberry Pi sends data
    Wire.onRequest(PiDataRequest); //this is triggered when Raspberry Pi requests data

    //Start serial for debugging
    //Note that you get rid of this and all serial statements if no longer debugging
    Serial.begin(9600);
    Serial.println("Rotational Arduino Initialized.");
  }
  
  void loop() {
    //what we need here is to just wait to see if new thing to rotate to has been sent or not
    static int state = WAIT; //our state we are initializing to. Could be moving or done alternatively
    static int lastState0 = HIGH, lastState90 = HIGH;
    //based on what we get from 'on receive', we might change states

    //the functionality varies depending on what we are actively doing
    switch(state){
      case WAIT:
        Serial.println("Waiting for message");
        if(newMessage=1){
          //here we will go into the moving state, and begin to move
          //the targetAngle is set in the receiveData ISR, 
          state=MOVING;
          break;
        }
        else{
          state=WAIT;
          break;
        }
      case MOVING:
        //if we are not actively controlling the system, 
        if(ctrlBusy==0){
          //here we add in whatever move function
          
          ctrlBusy=1;
          //============MOVE FUNCTION=================
          state=MOVING;
          break;
        }
        if(ctrlDone==1){
          //if we are done moving, we will go to the next state, and set the value of 'execution status' to the resulf of our move.
          ctrlDone=0;
          state=DONE;
          break;
        }
        //if we are here we haven't just started or just finished moving
        Serial.println("Still Moving");
        break;
      case DONE:
        //if the Pi has received our updated message, we can move back to waiting
        if(messageReceived==1){
          messageReceived=0;
          state=WAIT;
          break;
        }
        else{
          state=DONE;
          break;
        }
    }
    //at this point, we are done with state transition logic. 
    //I am a bit concerned at the simplicity as compared to seed lab to be honest, but I think this all makes sense
    //there was just much more logic in the other one after the loop ended.
    


  }
  
  void stepper_moveMM (AccelStepper &stepper, float mm) {
    float steps = (mm*steps_rev)/(200*lead_step);
    stepper.moveTo(steps);
    stepper.runToPosition();
  }

  //this is our ISR for when the Pi sends data
  void PiDataReceive(){
    offset = Wire.read(); //this is the offset of the data

    //now we want the rest of the message
    while(Wire.available()){
      instruction[messageLength] = Wire.read(); //get the next byte of info
      messageLength++;
    }
    //based on the offset it determines how we interpret the message, next will be 4 bytes of data
    //if offset==0, the next 4 bytes of data will be how much farther to rotate
    //so we will set target angle to be current angle + new angle. OBviously rotation stops when it hits end stops
    if(offset==0){
      byteFloat.bytes[0] = instruction[3];
      byteFloat.bytes[1] = instruction[2];
      byteFloat.bytes[2] = instruction[1];
      byteFloat.bytes[3] = instruction[0];
      targetAngle=byteFloat.floatValue + currentAngle;
    }
    //if offset ==1, target Angle just becomes the angle of = configuration
    else if(offset==1){
      targetAngle=configurationEquals; //0 degrees
    }
    else if(offset==2){
      targetAngle=configurationPlus; //45 degrees
    }
    else{
      Serial.println("Unknown offset");
    }
    //debugging check tbh
    Serial.println("Rotating to angle: " + String(targetAngle));
    //now we have interpretted the message, so we have to signal that we have a new message so our FSM can progress
    newMessage=1;
    messageLength=0; //we don't need this anymore
  }

  //this is what we will send when Pi requests data. This is typically to get the current status of what's happening.
  //on the Arduino's side I don't think it cares about the offset or anything.
  void PiDataRequest(){
    Wire.write(executionStatus);  // Send the last updated status
    Serial.print("Sending Status: ");
    Serial.println(executionStatus);
    //now we need to clear the executionStatus back to 20 if it wasn't because we have finished
    if(executionStatus!=20){
      executionStatus=20;
      messageReceived=1;
    }
  }

  //this is what will happen when the 0 end stop is triggered
  void triggered0Interrupt(){
    triggered0=true;
  }

  void triggered90Interrupt(){
    triggered90=true;
  }