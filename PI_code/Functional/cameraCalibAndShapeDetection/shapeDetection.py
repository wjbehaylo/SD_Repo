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
import math
import threading

# Constants
ARUINO_I2C_ADDRESS = 8
WIDTH = 640
HEIGHT = 480

# Initialize SMBus library for I2C communication (using bus 1)
#i2c_bus = SMBus(1)

# Load Camera Calibration Data
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")

# Extract focal length from camera matrix
FOCAL_LENGTH = [camera_matrix[0, 0], camera_matrix[1, 1]]  # fx

# Current frame captured from camera
current_frame = None
#Flag to control main loop
is_running = True

# Define known dimensions for each object type (in meters)
KNOWN_DIMENSIONS = {
    "CubeSat": {"width": 0.1, "length": 0.38, "height": 0.1},  # 1U CubeSat width, length, and height
    "Starlink": {"width": 0.7, "length": 1.4, "height": 0.1},  # Approximate deployed width, length, and height
    "Rocket Body": {"diameter": 0.62}  # Minotaur upper stage diameters
}

# Function to estimate distance based on object type
def estimate_distance(corners, object_type):
    if object_type not in KNOWN_DIMENSIONS:
        return None

    if object_type == "Rocket Body":
        # For Rocket Body, we only have a diameter
        diameter = KNOWN_DIMENSIONS["Rocket Body"]["diameter"]
        known_width = diameter
        known_length = diameter  # Use diameter as both width and height
    else:
        # CubeSat and Starlink
        known_width = KNOWN_DIMENSIONS[object_type]["width"]
        known_length = KNOWN_DIMENSIONS[object_type]["length"]

    # Define object points in 3D space (assuming object is flat and on Z=0 plane)
    object_points = np.array([
        [-known_width / 2, -known_length / 2, 0],
        [known_width / 2, -known_length / 2, 0],
        [known_width / 2, known_length / 2, 0],
        [-known_width / 2, known_length / 2, 0]
    ], dtype=np.float32)

        # Corners from the bounding box of the detected object (in 2D image coordinates)
    image_points = np.array([
        [corners[0][0], corners[0][1]],  # Top-left
        [corners[1][0], corners[1][1]],  # Top-right
        [corners[2][0], corners[2][1]],  # Bottom-right
        [corners[3][0], corners[3][1]]   # Bottom-left
    ], dtype=np.float32)


    # SolvePnP to get the rotation and translation vectors
    _, rvec, tvec = cv2.solvePnP(object_points, image_points, camera_matrix, distortion_coeffs)

    # Calculate the distance based on the tvec (translation vector)
    distance = np.linalg.norm(tvec)
    return distance

# Function to classify objects
def classify_object(contour):
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / h  # Width / Height
    
    # Get the object length and width
    object_length = h  # Assuming height is the length
    object_width = w   # Assuming width is the width
    area = cv2.contourArea(contour)

    # Debug: Show aspect ratio, area, width, and height
    print(f"Aspect Ratio: {aspect_ratio:.2f}, Area: {area:.2f}, Width: {object_width}, Height: {object_length}")

    # Classification logic

    # CubeSat: Small rectangular object
    cube_sat_area = KNOWN_DIMENSIONS["CubeSat"]["width"] * KNOWN_DIMENSIONS["CubeSat"]["length"]
    if aspect_ratio >= 0.8 and aspect_ratio <= 1.2 and \
       object_length >= KNOWN_DIMENSIONS["CubeSat"]["height"] and \
       object_width >= KNOWN_DIMENSIONS["CubeSat"]["width"] and \
       area <= cube_sat_area * 2:  # Allow some variation in area
            return "CubeSat"
        #testing on cubesat sideview image, Aspect Ratio: 1.27, Area: 239706.00, Width: 569, Height: 448

    # Starlink: Larger rectangular object
    starlink_area = KNOWN_DIMENSIONS["Starlink"]["width"] * KNOWN_DIMENSIONS["Starlink"]["length"]
    if aspect_ratio >= 2.0 and \
       object_width >= KNOWN_DIMENSIONS["Starlink"]["width"] and \
       object_length >= KNOWN_DIMENSIONS["Starlink"]["height"] and \
       area >= starlink_area * 0.5 and area <= starlink_area * 2:  # Allow some variation in area
            return "Starlink"
        #testing on starlink top view image, i got Aspect Ratio: 1.79, Area: 156171.00, Width: 550, Height: 307

    # Rocket Body: Circular object
    if aspect_ratio >= 0.9 and aspect_ratio <= 1.1:
        diameter = KNOWN_DIMENSIONS["Rocket Body"]["diameter"]
        estimated_diameter = object_width

        diameter_tolerance = 0.05
        if abs(estimated_diameter - diameter) <= diameter_tolerance:
            expected_area = np.pi * (diameter / 2) ** 2
            if area >= expected_area * 0.5 and area <= expected_area * 1.5:
                return "Rocket Body"
            #testing on minotaur bottom view, i got AR: 0.95, area: 117105.50, width: 380, height: 395

    # If nothing matches, return Unknown
    return "Unknown"


def object_dect_and_distance(camera):
    global is_running
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Failed to capture image!")
            break

        # **Apply camera calibration to remove distortion**
        frame_undistorted = cv2.undistort(frame, camera_matrix, distortion_coeffs)

        # Convert to grayscale and process
        gray = cv2.cvtColor(frame_undistorted, cv2.COLOR_BGR2GRAY)
        # Improve lighting conditions
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY, 11, 2)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Use morphological operations to clean up the edges
        kernel = np.ones((5, 5), np.uint8)
        processed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_contour_area = 100  # minimum area for a contour to be considered
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]


        for contour in contours:
            # Draw the contour for debugging
            cv2.drawContours(frame_undistorted, [contour], -1, (0, 0, 255), 2)

            # Get bounding box and classify
            x, y, w, h = cv2.boundingRect(contour)
            object_type = classify_object(contour)

            # Draw bounding box for classified objects
            cv2.rectangle(frame_undistorted, (x, y), (x + w, y + h), (0, 255, 0), 2)

            label = f"{object_type}" if object_type != "Unknown" else f"Unknown"
            cv2.putText(frame_undistorted, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Show the center of the object for debugging
            cx = x + w // 2
            cy = y + h // 2
            cv2.circle(frame_undistorted, (cx, cy), 5, (0, 0, 255), -1)

        cv2.imshow("Object Classification", frame_undistorted)

        key = cv2.waitKey(1) & 0xFF
        # Press 'q' to exit
        if key == ord('q'):
            is_running = False
            break

def main():
    #Main function to start capturing and processing frames
    global is_running
    #init camera
    camera = cv2.VideoCapture(0)

    # Set up camera properties (optional)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # Start the processing thread
    process_thread = threading.Thread(target=object_dect_and_distance, args=(camera,))
    process_thread.start()

    try:
        while is_running:
            time.sleep(0.1)  # Main thread can handle other tasks if necessary
    except KeyboardInterrupt:
        is_running = False

    process_thread.join()
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
