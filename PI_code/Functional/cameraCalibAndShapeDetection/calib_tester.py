import cv2
import numpy as np
import glob

# Prepare object points for the chessboard pattern (e.g., 9x6 corners)
chessboard_size = (10, 7)  # (width, height)
square_size = 0.025  # Size of a square in meters

# Prepare object points (0,0,0), (1,0,0), ..., (8,5,0)
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2) * square_size

# Arrays to store object points and image points
objpoints = []  # 3d points in real world space
imgpoints = []  # 2d points in image plane

# Load chessboard images
images = glob.glob('/home/sd-group-50/SD_Repo/PI_code/Camera_Calib/*.png')  # Adjust path accordingly

for img_path in images:
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)
        
        # Draw and display the corners
        cv2.drawChessboardCorners(img, chessboard_size, corners, ret)
        cv2.imshow('Chessboard', img)
        cv2.waitKey(500)

cv2.destroyAllWindows()

# Camera calibration
ret, camera_matrix, distortion_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# Save camera parameters
np.savez('camera_calibration.npz', camera_matrix=camera_matrix, distortion_coeffs=distortion_coeffs)

print("Camera calibration successful.")
print("Camera matrix:")
print(camera_matrix)
print("Distortion coefficients:")
print(distortion_coeffs)
