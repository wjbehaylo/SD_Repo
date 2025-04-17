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
import threading
import math

# Constants
ARUINO_I2C_ADDRESS = 8
WIDTH = 1920
HEIGHT = 1080

# Load Camera Calibration Data
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")

# Extract focal lengths (pixels)
fx = camera_matrix[0, 0]
fy = camera_matrix[1, 1]

# Known object dimensions in **millimeters**
KNOWN_DIMENSIONS = {
    "CubeSat":    {"width": 100, "length": 380, "height": 100},   # 1U CubeSat (100×100×380 mm)
    "Starlink":   {"width": 700, "length": 140, "height": 100},   # Approx. Starlink panel (700×140×100 mm)
    "Rocket Body":{"diameter": 620}                               # Minotaur upper stage diameter (mm)
}


def estimate_distance_simple(pixel_size, real_size_mm, f=fy):
    """
    Simple pinhole‐camera distance estimate:
      Z ≈ f * H / h
    where:
      f: focal length in pixels
      H: real size (mm)
      h: measured size in pixels
    Returns distance in meters.
    """
    if pixel_size <= 0:
        return None
    return (f * (real_size_mm / 1000.0)) / pixel_size


def estimate_distance_pnp(corners, object_type):
    """
    Use solvePnP for a more accurate distance. 
    corners: list of four (x,y) image points in the order
             top-left, top-right, bottom-right, bottom-left
    Returns distance in meters or None on failure.
    """
    dims = KNOWN_DIMENSIONS[object_type]
    # Build 3D object points in mm → convert to meters
    if object_type == "Rocket Body":
        d = dims["diameter"] / 1000.0
        object_pts = np.array([
            [-d/2, -d/2, 0],
            [ d/2, -d/2, 0],
            [ d/2,  d/2, 0],
            [-d/2,  d/2, 0]
        ], dtype=np.float32)
    else:
        w = dims["width"] / 1000.0
        l = dims["length"] / 1000.0
        object_pts = np.array([
            [-w/2, -l/2, 0],
            [ w/2, -l/2, 0],
            [ w/2,  l/2, 0],
            [-w/2,  l/2, 0]
        ], dtype=np.float32)

    image_pts = np.array(corners, dtype=np.float32)
    success, rvec, tvec = cv2.solvePnP(object_pts, image_pts,
                                        camera_matrix, distortion_coeffs,
                                        flags=cv2.SOLVEPNP_IPPE_SQUARE)
    if not success:
        return None
    # tvec is in meters
    return np.linalg.norm(tvec)


def classify_and_distance(contour, frame):
    x, y, w, h = cv2.boundingRect(contour)
    area = cv2.contourArea(contour)
    aspect = float(w) / (h + 1e-6)

    # Simple shape+size rules first
    # CubeSat
    cube = KNOWN_DIMENSIONS["CubeSat"]
    if 0.8 < aspect < 1.2 and area < cube["width"] * cube["length"]:
        obj = "CubeSat"
    # Starlink (long rectangle)
    elif aspect > 2.0 and area > 0.5 * KNOWN_DIMENSIONS["Starlink"]["width"] * KNOWN_DIMENSIONS["Starlink"]["length"]:
        obj = "Starlink"
    # Rocket Body (circle)
    elif 0.9 < aspect < 1.1:
        obj = "Rocket Body"
    else:
        return "Unknown", None

    # Estimate distance with simple formula
    real_size_mm = (cube["height"] if obj == "CubeSat" else
                    KNOWN_DIMENSIONS[obj].get("height", KNOWN_DIMENSIONS[obj].get("diameter")))
    dist_simple = estimate_distance_simple(h if obj!="Rocket Body" else w, real_size_mm)

    # Reject if simple distance is outside expected range (~1 m ±20 cm)
    if dist_simple is None or not (0.8 < dist_simple < 1.2):
        return "Unknown", None

    # Now refine with solvePnP
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    dist_pnp = estimate_distance_pnp(corners, obj)
    if dist_pnp is None or not (0.8 < dist_pnp < 1.2):
        return "Unknown", None

    # Draw and label
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(frame,
                f"{obj} @ {dist_pnp:.2f}m",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    # debug center
    cx, cy = x + w // 2, y + h // 2
    cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)

    return obj, dist_pnp


def object_detect_and_distance(camera):
    while True:
        ret, frame = camera.read()
        if not ret:
            print("Failed to capture image!")
            break

        # undistort
        frame_u = cv2.undistort(frame, camera_matrix, distortion_coeffs)

        gray = cv2.cvtColor(frame_u, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        # clean up
        kernel = np.ones((5, 5), np.uint8)
        proc = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        cnts, _ = cv2.findContours(proc, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            if cv2.contourArea(cnt) < 1000:
                continue
            # draw raw contour
            cv2.drawContours(frame_u, [cnt], -1, (0, 0, 255), 1)
            classify_and_distance(cnt, frame_u)

        cv2.imshow("Detection & Distance", frame_u)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def main():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    try:
        object_detect_and_distance(camera)
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
