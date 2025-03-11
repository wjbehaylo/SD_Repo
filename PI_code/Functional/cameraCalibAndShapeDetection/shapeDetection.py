# Purpose: this is a program that uses the camera calibration camera matrix and distortion coefficients to identify an object based on its shape and the number of contours
# Contributors: Angela
# Sources: 
#   Based on programming used in SEED_LAB for object detection
# Relevant files: camera_calib.py, camera_matrix.npy, distortion_coeffs.npy, and relevant png checker board images from the camera

import cv2
import threading
import time
import numpy as np
import board
import os
from smbus2 import SMBus
from time import sleep

# Define I2C address for Arduino
ARUINO_I2C_ADDRESS = 8

# Initialize SMBus library for I2C communication (using bus 1)
i2c_bus = SMBus(1)

# Initialize thread lock
frame_lock = threading.Lock()

# Initialize camera
# Open camera with index 0
camera = cv2.VideoCapture(0)
# Set camera frames per second to 60
camera.set(cv2.CAP_PROP_FPS, 60)
# Width of camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
# Height of camera
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 

# Current frame captured from camera
current_frame = None
#Flag to control main loop
is_running = True

#Load camera calibration data
camera_matrix=np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")
# Extract the focal length
focal_points = [camera_matrix[0, 0], camera_matrix[1, 1]]


def capture_frame(): 
    # Capture frames camera and updates global value for current_frame
    global current_frame, is_running
    # Continue capturing frames while is_running is True
    while is_running:
        ret, frame = camera.read()
        # Check if frame capture was successful
        if ret:
            # Ensure thread-safe access to current_frame
            with frame_lock:
                current_frame = frame.copy()

def debris_object_detect_and_distance():
    # Process captured frames to detect ArUco markers and calculate their angles and distance
    global current_frame, is_running

    # Define area thresholds for classification (example values, adjust as needed)
    CUBESAT_AREA = 500  # Example threshold for CubeSat
    ROCKET_BODY_AREA = 2000  # Example threshold for Rocket Body
    STARLINK_AREA = 1000  # Example threshold for Starlink
    TOLERANCE = 0.1  # Allow a ±10% variation in area for classification

    #continue processing frames while is_running is True
    while is_running:
        with frame_lock: #thread-safe frame access
            if current_frame is None:
                continue
            frame = current_frame.copy()
                
            #undistort image based on current_frame, camera_matrix, and distortion_coeffs
            undistort_frame = cv2.undistort(frame, camera_matrix, distortion_coeffs)
            
            # Convert the image to grayscale for object detection
            gray_image = cv2.cvtColor(undistort_frame, cv2.COLOR_BGR2GRAY)

            # separate the object from the background 
            _, thresh = cv2.threshold(gray_image, 127, 255, 0)

            # Find the contours of the object  
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 

            for contour in contours:
                area = cv2.contourArea(contour)
            
                # Check if the area is within tolerance for classification
                if (CUBESAT_AREA * (1 - TOLERANCE)) <= area <= (CUBESAT_AREA * (1 + TOLERANCE)):
                    classification = "CubeSat"
                elif (STARLINK_AREA * (1 - TOLERANCE)) <= area <= (STARLINK_AREA * (1 + TOLERANCE)):
                    classification = "Starlink"
                elif (ROCKET_BODY_AREA * (1 - TOLERANCE)) <= area <= (ROCKET_BODY_AREA * (1 + TOLERANCE)):
                    classification = "Rocket Body"
                else:
                    classification = "Unknown Object"

                # Print classification and size
                scale_factor = 0.1  # Example conversion factor (1 pixel = 0.1 cm)
                size = area * (scale_factor ** 2)
                print(f'{classification} Detected! Size: {size:.2f} cm²')

                # Draw and label the detected object
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(undistort_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(undistort_frame, classification, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Show the processed frame (optional)
        cv2.imshow("Detected Objects", undistort_frame)
    
        if cv2.waitKey(1) & 0xFF == ord('q'):
            is_running = False #exit program
            break

def main():
    #Main function to start capturing and processing frames
    global is_running
    
    #Start threads for capturing and processing frames
    capture_thread = threading.Thread(target=capture_frame) 
    process_thread = threading.Thread(target=debris_object_detect_and_distance)

    capture_thread.start()
    process_thread.start()
    sleep(1) #might not be needed but added for caution

    try:
        while is_running:
            time.sleep(0.1)  # Main thread can handle other tasks if necessary
    except KeyboardInterrupt:
        print("\nStopping threads...")
        is_running = False
    
    #wait for threads to finish
    capture_thread.join()
    process_thread.join()
    
    #clean up
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
