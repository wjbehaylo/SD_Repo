# Purpose: this is a demonstrable file that generates a string based on the status number input
# Contributors: Walter
# Sources: 
#   Status values can come from many different areas in the program
# Relevant files: 
#   Many other files return a status value
# Circuitry: 
#   This is purely software


#status is the input value, a single integer
#this will return a string
def Generate_Status(status):
    #this is the returned value
    # Nothing important, empty status if you will
    if status==-1:
        status_string = "Programming or circuitry error"
    elif status == 0:
        status_string = ""
    # 0-25 come from the ARD_Comms file
    elif status == 1:
        status_string = "Arm pair 0 movement complete, no end stops or force sensors triggered"
    elif status == 2:
        status_string = "Arm pair 0 fully open end stop triggered"
    elif status == 3:
        status_string = "Arm pair 0 fully closed end stop triggered"
    elif status == 4:
        status_string = "Arm pair 0 force sensor triggered"
    elif status == 5:
        status_string = "Arm pair 0 unrecognized movement command"
    elif status == 10:
        return ""  # Do not populate if divisible by 10
    elif status == 11:
        status_string = "Arm pair 1 movement complete, no end stops or force sensors triggered"
    elif status == 12:
        status_string = "Arm pair 1 fully open end stop triggered"
    elif status == 13:
        status_string = "Arm pair 1 fully closed end stop triggered"
    elif status == 14:
        status_string = "Arm pair 1 force sensor triggered"
    elif status == 15:
        status_string = "Arm pair 1 unrecognized movement command"
    elif status == 20:
        return ""  # Do not populate if divisible by 10
    elif status == 21:
        status_string = "Rotation success"
    elif status == 22:
        status_string = "Configuration success"
    elif status == 23:
        status_string = "(0) End stop hit"
    elif status == 24:
        status_string = "(90) End stop hit"
    elif status == 25:
        status_string = "Rotational unrecognized command"
    else:
        status_string = "Unknown Status"
    
    return status_string
