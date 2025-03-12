# Purpose: this is a program that uses the camera calibration camera matrix and distortion coefficients to identify an object based on its shape and the number of contours
# Contributors: Angela
# How to Run: Execute using the python terminal.
# Make sure either camera is connected for live feed. Camera coefficients need to be in the same
# directory as script.
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

# Camera constants
HEIGHT = 480
WIDTH = 640

# Shared resources
detectedObject = False
current_frame = None
is_running = True

# Load Camera Calibration Data
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("dist_coeffs.npy")

# 3D Models for different objects (these are placeholder values, adjust as necessary)
object_models = {
    "CubeSat": np.array([
        [-0.5, -0.5, 0],   # Front-bottom-left
        [ 0.5, -0.5, 0],   # Front-bottom-right
        [ 0.5,  0.5, 0],   # Front-top-right
        [-0.5,  0.5, 0],   # Front-top-left
        [-0.5, -0.5, 1],   # Back-bottom-left
        [ 0.5, -0.5, 1],   # Back-bottom-right
        [ 0.5,  0.5, 1],   # Back-top-right
        [-0.5,  0.5, 1]    # Back-top-left
    ], dtype=np.float32),
    
    "Starlink": np.array([
        # Define 3D points for the Starlink satellite model
        [-1.0, -0.5, 0], [ 1.0, -0.5, 0], [ 1.0,  0.5, 0], [-1.0,  0.5, 0],  # Square points
        [-1.0, -0.5, 1], [ 1.0, -0.5, 1], [ 1.0,  0.5, 1], [-1.0,  0.5, 1]   # Corresponding back points
    ], dtype=np.float32),
    
    "Rocket Body": np.array([
        # Define 3D points for the Rocket Body model
        [-0.5, -0.5, 0], [ 0.5, -0.5, 0], [ 0.5,  0.5, 0], [-0.5,  0.5, 0],  # Base
        [-0.5, -0.5, 10], [ 0.5, -0.5, 10], [ 0.5,  0.5, 10], [-0.5,  0.5, 10]  # Top
    ], dtype=np.float32)
}

# Initialize the camera
def initializeCamera():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    camera.set(cv2.CAP_PROP_BRIGHTNESS, 250)
    camera.set(cv2.CAP_PROP_EXPOSURE, 39)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    camera.set(cv2.CAP_PROP_FPS, 120)
    return camera

def calculate_distance_with_pose_estimation(object_points, image_points, camera_matrix, distortion_coeffs):
    """
    Function to calculate the distance to an object using pose estimation.

    Args:
    - object_points: 3D coordinates of the object model (numpy array)
    - image_points: 2D image coordinates of the object model in the image (numpy array)
    - camera_matrix: Camera matrix containing the intrinsic parameters (numpy array)
    - distortion_coeffs: Distortion coefficients (numpy array)

    Returns:
    - distance: The distance from the camera to the object (float)
    - projected_points: The 2D projected points on the image (numpy array)
    """
    # SolvePnP to get rotation and translation vectors
    _, rvec, tvec = cv2.solvePnP(object_points, image_points, camera_matrix, distortion_coeffs)

    # Extract the translation vector (tvec) to get the distance
    distance = np.linalg.norm(tvec)  # Euclidean distance (meters)

    # Optionally, project the 3D object points to the 2D image plane using the pose
    projected_points, _ = cv2.projectPoints(object_points, rvec, tvec, camera_matrix, distortion_coeffs)

    return distance, projected_points

def capture_frame(camera):
    ret, frame = camera.read()
    if ret:
        return frame.copy()
    return None

def debris_detect(frame, camera_matrix, distortion_coeffs):
    """
    Classify the detected object and calculate its distance using pose estimation.
    
    Args:
    - frame: The captured frame from the camera.
    - camera_matrix: Camera matrix containing the intrinsic parameters (numpy array)
    - distortion_coeffs: Distortion coefficients (numpy array)
    
    Returns:
    - None (Displays the frame with distance and classification).
    """
    # Convert frame to grayscale and find contours
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_image, 127, 255, 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Calculate the area of the detected contour
        area = cv2.contourArea(contour)
        if area < 100:  # Ignore small contours
            continue

        # Assume the object is CubeSat, Starlink, or Rocket Body
        detected_object = "Unknown Object"
        image_points = []

        # Calculate bounding box for contour (image points)
        x, y, w, h = cv2.boundingRect(contour)
        image_points = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32)

        # Match object based on area or other criteria (can be expanded with more sophisticated checks)
        if area < 1500:
            detected_object = "CubeSat"
            object_points = object_models["CubeSat"]
        elif area < 3000:
            detected_object = "Starlink"
            object_points = object_models["Starlink"]
        else:
            detected_object = "Rocket Body"
            object_points = object_models["Rocket Body"]

        # Call pose estimation for the detected object
        distance, projected_points = calculate_distance_with_pose_estimation(object_points, image_points, camera_matrix, distortion_coeffs)

        # Display the distance and classification
        print(f"Detected {detected_object} at distance: {distance:.2f} meters")

        # Draw the projected points and bounding box on the frame
        for point in projected_points:
            cv2.circle(frame, tuple(point[0].astype(int)), 5, (0, 0, 255), -1)

        cv2.putText(frame, f'{detected_object}: {distance:.2f}m', (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Show the image with the projected points and object classification
    cv2.imshow("Detected Objects and Distance", frame)

def main():
    # Initialize the camera
    camera = initializeCamera()

    while True:
        # Capture a frame from the camera
        frame = capture_frame(camera)
        if frame is None:
            continue  # If the frame is not captured, skip to the next iteration
        
        # Detect debris and calculate the distance
        debris_detect(frame, camera_matrix, distortion_coeffs)
        
        # Exit the loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Releasee Resources
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
