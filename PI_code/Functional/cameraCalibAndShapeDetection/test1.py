# Purpose: This is a program that uses the camera calibration camera matrix and distortion coefficients to identify a debris object based on its shape and the number of contours
# Contributors: Angela
# How to Run: Execute using the python terminal. Make sure either camera is connected for live feed. 
# Camera and distortion coefficients need to be in the same directory as script.
# need to install: pip install opencv-python gradio
# Sources: 
#   Based on programming used in SEED_LAB for object detection and https://learnopencv.com/moving-object-detection-with-opencv/
# Relevant files: camera_calib.py, camera_matrix.npy, distortion_coeffs.npy, and relevant png checker board images from the camera

import cv2
import numpy as np
import time
#from smbus2 import SMBus
from time import sleep
import math
import threading
#import gradio as gp

# Constants
ARUINO_I2C_ADDRESS = 8
WIDTH = 1920
HEIGHT = 1080
movement_threshold = 5000  # Minimum contour area for detecting motion

# Previous frame for motion detection
previous_frame = None  # Store the previous frame
frame_rate_delay = 0.1  # Delay in seconds (0.1 = 10 FPS)

# Function to detect moving objects and display contours
def object_dect_and_distance(camera):
    global previous_frame
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Failed to capture image!")
            break

        # **Use the original frame without undistortion**
        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)  # Apply blur to reduce noise

        # Initialize the previous frame (first time run)
        if previous_frame is None:
            previous_frame = gray
            continue

        # Frame differencing (find the absolute difference between the current frame and the previous frame)
        frame_diff = cv2.absdiff(previous_frame, gray)

        # Threshold the difference to identify significant changes (motion)
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)

        # Use morphological operations to clean up the thresholded image (remove noise)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours from the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Ignore small contours that don't represent significant motion
            if cv2.contourArea(contour) < movement_threshold:
                continue

            # Draw the contours on the frame for visualization
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Optional: Show the center of the object for debugging
            cx = x + w // 2
            cy = y + h // 2
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        # Update the previous frame
        previous_frame = gray

        # Show the processed frame
        cv2.imshow("Moving Object Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        # Press 'q' to exit
        if key == ord('q'):
            break
        
        # Add delay to slow down the frame rate
        time.sleep(frame_rate_delay)

# Main function to start capturing and processing frames
def main():
    global previous_frame
    # Initialize camera
    camera = cv2.VideoCapture(0)  # Use the default camera (usually webcam)
    
    # Set up camera properties (optional)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # Start the processing thread
    process_thread = threading.Thread(target=object_dect_and_distance, args=(camera,))
    process_thread.start()

    try:
        while True:
            time.sleep(0.1)  # Main thread can handle other tasks if necessary
    except KeyboardInterrupt:
        print("Exiting...")
    
    process_thread.join()
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
