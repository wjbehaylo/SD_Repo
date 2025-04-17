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
import threading

# === Configuration ===
WIDTH, HEIGHT = 1280, 720
MIN_CONTOUR_AREA = 1000  # ignore specks

# Load camera calibration
camera_matrix    = np.load("camera_matrix.npy")
distortion_coeff = np.load("distortion_coeffs.npy")

is_running = True

def classify_object(contour):
    # approximate the contour to a polygon
    area = cv2.contourArea(contour)
    peri   = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
    print(f"  verts={len(approx)}, area={area:.0f}, peri={peri:.0f}")


    x, y, w, h = cv2.boundingRect(approx)
    aspect_ratio = w / float(h)

    # 4‐sided shapes → rectangles (CubeSat vs. Starlink)
    if len(approx) == 4:
        if 0.8 <= aspect_ratio <= 1.2:
            return "CubeSat"
        elif aspect_ratio > 2.0:
            return "Starlink"
        else:
            return "Rectangle"
    # many‐sided → approximate circle
    elif len(approx) > 8:
        # check how circular it is
        ((cx, cy), radius) = cv2.minEnclosingCircle(contour)
        circle_area = np.pi * (radius ** 2)
        if abs(area - circle_area) / circle_area < 0.3:
            return "Rocket Body"
        else:
            return "Unknown"
    else:
        return "Unknown"

def detection_loop(cam):
    global is_running
    while is_running:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # undistort
        #frame = cv2.undistort(frame, camera_matrix, distortion_coeff)

        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blurred, 50, 150)

        # find and filter contours
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = [c for c in cnts if cv2.contourArea(c) > MIN_CONTOUR_AREA]

        for c in cnts:
            # draw raw contour
            cv2.drawContours(frame, [c], -1, (255,0,0), 2)
            obj_type = classify_object(c)
            x, y, w, h = cv2.boundingRect(c)

            # draw
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, obj_type, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Live Classification", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            is_running = False

def main():
    global is_running
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    t = threading.Thread(target=detection_loop, args=(cam,))
    t.start()

    try:
        while is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        is_running = False

    t.join()
    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
