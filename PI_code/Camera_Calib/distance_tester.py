import cv2
import numpy as np
from cv2 import aruco


# Load camera parameters
calibration_data = np.load('camera_calibration.npz')
camera_matrix = calibration_data['camera_matrix']
distortion_coeffs = calibration_data['distortion_coeffs']

# Initialize the ArUco dictionary and parameters
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_parameters = aruco.DetectorParameters()

# Known width of the ArUco marker (in meters)
known_marker_width = 0.0484  # Adjust according to your marker size

# Start video capture
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Undistort the frame
    undistorted_frame = cv2.undistort(frame, camera_matrix, distortion_coeffs)

    # Convert to grayscale
    gray_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)

    # Detect ArUco markers
    corners, ids, rejected = aruco.detectMarkers(gray_frame, aruco_dict, parameters=aruco_parameters)

    if ids is not None:
        # Estimate pose of the detected markers
        rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, known_marker_width, camera_matrix, distortion_coeffs)

        for i in range(len(ids)):
            # Draw detected markers and axes
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            #cv2.aruco.drawFrameAxis(frame, camera_matrix, distortion_coeffs, rvecs[i], tvecs[i], 0.1)

            # Calculate distance and angle
            distance = np.linalg.norm(tvecs[i][0])*39.37008  # Distance from camera to marker
            angle = np.arctan2(tvecs[i][0][2], tvecs[i][0][0]) * (180.0 / np.pi)  # Angle in degrees

            # Display the distance and angle
            cv2.putText(frame, f'Distance: {distance:.2f} inches', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(frame, f'Angle: {angle:.2f} degrees', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Show the frame
    cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
