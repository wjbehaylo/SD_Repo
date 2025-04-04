# Purpose: This is a program that uses the camera calibration camera matrix and distortion coefficients to identify a debris object based on its shape and the number of contours
# Contributors: Angela
# How to Run: Execute using the python terminal. Make sure either camera is connected for live feed. 
# Camera and distortion coefficients need to be in the same directory as script.
# Sources: 
#   Based on programming used in SEED_LAB for object detection
# Relevant files: camera_calib.py, camera_matrix.npy, distortion_coeffs.npy, and relevant png checker board images from the camera

import cv2
import numpy as np
import time
from smbus2 import SMBus
from time import sleep

# Constants
ARUINO_I2C_ADDRESS = 8
WIDTH = 640
HEIGHT = 480

# Load Camera Calibration Data
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("dist_coeffs.npy")

# Extract focal length from camera matrix
FOCAL_LENGTH = camera_matrix[0, 0]  # fx

# Define known widths for each object type (in meters)
KNOWN_WIDTHS = {
    "CubeSat": 0.1,  # 1U CubeSat width
    "Starlink": 1.4,  # Approximate deployed width
    "Rocket Body": 1.27  # Minotaur upper stage diameter
}

# Function to estimate distance based on object type
def estimate_distance(perceived_width, object_type):
    if perceived_width == 0 or object_type not in KNOWN_WIDTHS:
        return None
    return (KNOWN_WIDTHS[object_type] * FOCAL_LENGTH) / perceived_width

# Initialize the camera
def initialize_camera():
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

# Function to classify objects
def classify_object(contour):
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / h  

    # Contour approximation to count corners
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    num_vertices = len(approx)

    # Classification logic
    if 0.9 <= aspect_ratio <= 1.1 and num_vertices >= 4:
        return "CubeSat"
    elif aspect_ratio > 2.0 and num_vertices > 4:
        return "Starlink"
    else:
        return "Rocket Body"

# Initialize camera
camera = initialize_camera()

while camera.isOpened():
    ret, frame = camera.read()
    if not ret:
        break

    # **Apply camera calibration to remove distortion**
    frame_undistorted = cv2.undistort(frame, camera_matrix, distortion_coeffs)

    # Convert to grayscale and process
    gray = cv2.cvtColor(frame_undistorted, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Filter small objects
            x, y, w, h = cv2.boundingRect(contour)
            perceived_width = w  # Use width of bounding box

            # Classify object
            object_type = classify_object(contour)

            # Estimate distance using appropriate known width
            distance = estimate_distance(perceived_width, object_type)

            # Draw bounding box and label
            cv2.rectangle(frame_undistorted, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"{object_type} - {distance:.2f} m" if distance else object_type
            cv2.putText(frame_undistorted, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show the result
    cv2.imshow("Object Classification", frame_undistorted)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
