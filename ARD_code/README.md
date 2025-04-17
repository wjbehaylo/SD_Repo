# ARD_code

The ARD_code is split into four directories.

ARD_code/

  Demonstration/              (Comms_Test/, Rot_Comms/)
  
  Exploration/               (linearArduinos/, rotationalArduino/, pi_proto/)
  
  Functional/                (endStopControlCode/, forceSensorCode/, gear_stepperCode/, i2c_comm/, lin_stepperCode/)
  
  PI_Comms/                  (PI_Comms.ino)
  

## Project Board
**Demonstration**
- [x] Prove basic linear and rotational motion of the robot claw. 
- [x] Move one linear stepper motor
- [x] Move one rotational stepper motor

**Exploration**
- [x] Prototype code and structure for
- [x] Isolate axis logic: Pi sends angle and distance

**Functional**
- [x] Unit test for each sensor
- [x] Unit test for each motor driver and motor

**PI_Comms**
- [x] Tie everything together for full Arduino and RaspberryPi Demo

## Demonstration

The Demonstration code is divided into two subfolders, Comms_Test and Rot_Comms. 

Within the Comms_Test folder is the Comms_Test.ino file. The Comms_Test.ino file is a test file to set up the rotational arduino as the receiver of commands from the raspberry pi and to control the stepper motors for linear and rotational motion. Hardware connections for each of the Arduino pins are detailed at the beginning of the code. Libraries to be included are also detailed in the header file. Upload the sketch to the Arduino and ensure the wiring connections are correct. 

Within the Rot_Comms folder is the Rot_Comms.ino file to be uploaded onto the Arduino. The Rot_Comms.ino file is a functional file to set up the rotational arduino as the receiver of commands from the raspberry pi and to control the stepper motors for linear and rotational motion. Hardware connections for each of the Arduino pins are detailed at the beginning of the code. Libraries to be included are also detailed in the header file. Upload the sketch to the Arduino and ensure the wiring connections are correct. 

## Exploration

The Exploration code is divided into two subfolders, linearArduinos and rotationalArduino. It also contains a python file to test sending of the angle and distance from the Pi. 

Within the linearArduinos subfolder are header files, cpp files, and an Arduino sketch 'linear_main.ino'. The linear_main.ino file is the main sketch that controls both linear stepper motors for synchornized vertical movement. The Pi will send angle/distance bytes to affect the actuation of the linear motors.

Within the rotationalArduino subfolder are header files, cpp files, and an Arduino sketch 'rotational_main.ino'

## Functional

The Functional code is divided into targeted folders for every sensor and motor driver. Each subfolder is titled after the functional test it was used for. Each component was tested individually before integration with the whole system. 

The endStopControlCode folder contains the 'endStopControlCode.ino' sketch to be uploaded to the Arduino. The code is for the electrical endstops, and turns off a motor once the endstop is pressed. 

The forceSensorCode folder contains the 'forceSensorCode.ino' sketch to be uploaded to the Arduino. The code senses the amount of force applied to the linear soft pot sensors (underneath the form on the physical system) to read out an analog voltage. The sensors are able to detect up to 3N of force. 

The gear_stepperCode folder contains the 'gear_stepperCode.ino' sketch to be uploaded to the Arduino. It will rotate to an endstop and set its position to 0. It is able to obtain directions from the Pi and rotate to a specific configuration.

The i2c_comm folder contains the 'i2c_comm.ino' sketch to be uploaded to the Arduino. This code is purely used to test the i2c connection between the Raspberry Pi and the Arduino. The header details which specific pins are required for connections.

The lin_stepperCode folder contains the 'lin_stepperCode.ino' sketch to be uploaded to the Arduino. This code is used test the linear arduinos after they receive instruction from the Pi.

## PI_Comms

The PI_Comms folder contains the 'PI_Comms.ino' sketch to be uploaded to the Arduino and test the motors for linear and rotational movement.


