# Purpose: This is a program that uses the camera calibration camera matrix and distortion coefficients to identify a debris object based on its shape and the number of contours
# Contributors: Angela
# How to Run: Execute using the python terminal. Make sure either camera is connected for live feed. 
# Camera and distortion coefficients need to be in the same directory as script.
# Sources: 
#   Based on programming used in SEED_LAB for object detection
# Relevant files: camera_calib.py, camera_matrix.npy, distortion_coeffs.npy, and relevant png checker board images from the camera

import cv as cv2
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

# 3D Models for different objects (these are placeholder values, adjust when values are confirmed)
object_models = {
    "CubeSat": np.array([[-0.5, -0.5, 0], [0.5, -0.5, 0], [0.5, 0.5, 0], [-0.5, 0.5, 0], [-0.5, -0.5, 1], [0.5, -0.5, 1], [0.5, 0.5, 1], [-0.5, 0.5, 1]], dtype=np.float32),
    "Starlink": np.array([[-1.0, -0.5, 0], [1.0, -0.5, 0], [1.0, 0.5, 0], [-1.0, 0.5, 0], [-1.0, -0.5, 1], [1.0, -0.5, 1], [1.0, 0.5, 1], [-1.0, 0.5, 1]], dtype=np.float32),
    "Rocket Body": np.array([[-0.5, -0.5, 0], [0.5, -0.5, 0], [0.5, 0.5, 0], [-0.5, 0.5, 0], [-0.5, -0.5, 10], [0.5, -0.5, 10], [0.5, 0.5, 10], [-0.5, 0.5, 10]], dtype=np.float32)
}

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

def calculate_distance_with_pose_estimation(object_points, image_points, camera_matrix, distortion_coeffs):
    """
    Function to calculate the distance to an object using pose estimation.
    """
    success, rvec, tvec = cv2.solvePnP(object_points, image_points, camera_matrix, distortion_coeffs)
    
    if not success:
        return None, None  # If solvePnP fails

    # Calculate the Euclidean distance using the translation vector
    distance = np.linalg.norm(tvec)
    
    # Project the 3D object points back to the 2D image plane
    projected_points, _ = cv2.projectPoints(object_points, rvec, tvec, camera_matrix, distortion_coeffs)
    
    return distance, projected_points

def debris_detect(frame, camera_matrix, distortion_coeffs, object_models):
    global detected_object, detected_object_type
    
    # Convert frame to grayscale and find contours
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_image, 127, 255, 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    detected_object = False
    detected_object_type = None

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 100:  # Ignore small contours
            continue

        # Use bounding box for pose estimation
        x, y, w, h = cv2.boundingRect(contour)
        image_points = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32)

        # Match object based on area (adjust thresholds if necessary)
        if area < 1500:
            detected_object_type = "CubeSat"
            object_points = object_models["CubeSat"]
        elif area < 3000:
            detected_object_type = "Starlink"
            object_points = object_models["Starlink"]
        else:
            detected_object_type = "Rocket Body"
            object_points = object_models["Rocket Body"]

        # Get distance and projected points using pose estimation
        distance, projected_points = calculate_distance_with_pose_estimation(object_points, image_points, camera_matrix, distortion_coeffs)

        if distance is not None:
            detected_object = True
            print(f"Detected {detected_object_type} at distance: {distance:.2f} meters")

            # Draw projected points and bounding box on the frame
            for point in projected_points:
                cv2.circle(frame, tuple(point[0].astype(int)), 5, (0, 0, 255), -1)

            cv2.putText(frame, f'{detected_object_type}: {distance:.2f}m', (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            break  # Exit after detecting the first object

    cv2.imshow("Detected Objects and Distance", frame)

# Main loop
if __name__ == "__main__":
    camera = initialize_camera()
    time.sleep(1)

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        # Undistort the captured frame
        frame = cv2.undistort(frame, camera_matrix, distortion_coeffs)

        # Detect debris
        debris_detect(frame, camera_matrix, distortion_coeffs, object_models)

        # Exit loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
