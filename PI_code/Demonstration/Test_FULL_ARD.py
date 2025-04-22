# Purpose: to test the functionality of the linear arduino communications as well as the rotational arduino communications
# Contributors: Walter, Angela
# Sources: 
#   Based on programming used in SEED_LAB for python state machine
#   ARD_Comms has the functions we need to send and receive from the arduino
#   Generate_Status prints out vectors from integer status codes being used
# Relevant files: 
#   UART_Comms.py contains the code for the UART system
#   ARD_Comms has the functions we need to send and receive from the arduino
#   Generate_Status prints out vectors from integer status codes being used
#   Final_Lin_Comms.ino contains the Arduino code that will be running on the linear arduino
#   Final_Rot_Comms.ino contains the arduino code that will be running on the rotational arduino
# Circuitry: 
#   for the Pi, follow the circuitry outline in UART_Comms, and I2C_Arduino (exploration file)
#   For the linear Arduino, wire it to the pins and stuff as outlined in Final_Lin_Comms.ino
#   For the rotate Arduino, wire it to the pins and stuff as outlined in Final_Rot_COmms.ino

from smbus2 import SMBus
from time import sleep
from UART_Comms import UART
from ARD_Comms import *
from Generate_Status import Generate_Status
import threading
import serial

# Arduino I2C Setup
i2c_arduino = SMBus(1)
rot_ard_add = 8
lin_ard_add = 15

# Global flags and values
pair_select = 0
move_amount = 0
rotate_amount = 0
offset = 0
status_UART = ""
new_status = 0

# Command loop
print("=== Combined Arduino Test ===")
print("You can test either the Linear or Rotational Arduino.")

while True:
    device_choice = input("\nSelect device to control — 'L' for Linear, 'R' for Rotational, 'Q' to Quit: ").upper()
    if device_choice == "Q":
        print("Quitting combined test.")
        break

    elif device_choice == "L":
        # Linear Arduino
        while True:
            try:
                sel = int(input("Select linear pair (0=pair0, 1=pair1, 2=both): "))
                if sel in (0, 1, 2):
                    pair_select = sel
                    break
                else:
                    print("Invalid input.")
            except:
                print("Please enter a valid integer (0, 1, or 2).")

        while True:
            try:
                amount = int(input("Enter number of linear steps to move (+/-): "))
                move_amount = amount
                break
            except:
                print("Please enter a valid integer.")

        lin_ARD_Write(pair_select, move_amount)
        print(f"[Linear] Sent to Arduino: pair={pair_select}, steps={move_amount}")

        sleep(5)
        result = lin_ARD_Read(3 + pair_select)
        status_msg = Generate_Status(result[0]) + Generate_Status(result[1])
        print("[Linear] Arduino Status:", status_msg)

    elif device_choice == "R":
        # Rotational Arduino
        valid_rot_cmds = ("Y", "+", "=", "C")
        while True:
            command = input("Enter 'Y' to rotate arbitrary amount, '+' (to 45°), '=' (to 0°), or 'C' to cancel: ").upper()
            if command not in valid_rot_cmds:
                print("Invalid command. Try again.")
                continue
            if command == "C":
                print("Canceled rotational command.")
                break
            elif command == "Y":
                while True:
                    try:
                        rotate_amount = float(input("Enter number of degrees to rotate (+/-): "))
                        break
                    except:
                        print("Invalid number. Try again.")
            elif command == "+":
                print("Rotating into the '+' configuration (45°).")
                rotate_amount = 45
            elif command == "=":
                print("Rotating into the '=' configuration (0°).")
                rotate_amount = 0

            rot_ARD_Write(rotate_amount)
            print(f"[Rotational] Sent to Arduino: degrees={rotate_amount}")

            sleep(5)
            result = rot_ARD_Read(3)
            status_msg = Generate_Status(result[0]) + Generate_Status(result[1])
            print("[Rotational] Arduino Status:", status_msg)
            break

    else:
        print("Invalid device choice. Enter 'L', 'R', or 'Q'.")
