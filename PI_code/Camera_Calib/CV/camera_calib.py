import numpy as np
import cv2
import glob

# Define the chessboard size
chessboard_size = (10, 7)  # Number of inner corners per a chessboard row and column

#define criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Prepare object points (0,0,0), (1,0,0), ..., (8,5,0)
object_points = np.zeros((1, chessboard_size[0] * chessboard_size[1], 3), np.float32)
object_points[0, :,:2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images
obj_points = []  # 3d point in real world space
img_points = []  # 2d points in image plane

# Load calibration images
images = glob.glob('/home/seedlab/repo/SEED/Demo1/CV/*.png')

for image in images:
    img = cv2.imread(image)
    #cv2.imshow("Image", img)
    #cv2.waitKey(2000)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)

    # If found, add object points and image points
    if ret:
        #changed from object_points
        obj_points.append(object_points)
        corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1, -1), criteria)
        img_points.append(corners2)
print(gray)
#print("Object Points: ", object_points)

#Draw and display corners
cv2.drawChessboardCorners(img, chessboard_size, corners2,ret)

#resize image
origHeight, origWidth = img.shape[:2] #get current image dimensions
displayRescaleFactor = 640 / origWidth
img = cv2.resize(img, (0, 0), fx = displayRescaleFactor, fy = displayRescaleFactor, interpolation = cv2.INTER_AREA)

# Camera calibration
ret, camera_matrix, distortion_coeffs, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)

if ret:
    np.save('camera_matrix.npy', camera_matrix)
    np.save('distortion_coeffs.npy', distortion_coeffs)
else:
    print("Calibration failed.")
        
# Display the camera matrix
print("Camera Matrix:")
print(camera_matrix)

# Display distortion coeffs
print("Distortion Coeffs:")
print(distortion_coeffs)

# Extract the focal length
focal_length_x = camera_matrix[0, 0]
focal_length_y = camera_matrix[1, 1]

print(f"Focal Length (x): {focal_length_x}")
print(f"Focal Length (y): {focal_length_y}")
