import cv2
import numpy as np
import threading
import queue
from smbus2 import SMBus
import board
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from time import sleep
import math
import glob
#reference for calibration: https://medium.com/@ed.twomey1/using-charuco-boards-in-opencv-237d8bc9e40d

# ------------------------------
# ENTER YOUR PARAMETERS HERE:
ARUCO_DICT = cv2.aruco.DICT_5X5_250
SQUARES_VERTICALLY = 7
SQUARES_HORIZONTALLY = 5
SQUARE_LENGTH = 0.03
MARKER_LENGTH = 0.015
LENGTH_PX = 640   # total length of the page in pixels
MARGIN_PX = 20    # size of the margin in pixels
SAVE_NAME = 'ChArUco_Marker.png'
# ------------------------------

def create_and_save_new_board():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    board = cv2.aruco.CharucoBoard((SQUARES_VERTICALLY, SQUARES_HORIZONTALLY), SQUARE_LENGTH, MARKER_LENGTH, dictionary)
    size_ratio = SQUARES_HORIZONTALLY / SQUARES_VERTICALLY
    img = cv2.aruco.CharucoBoard.generateImage(board, (LENGTH_PX, int(LENGTH_PX*size_ratio)), marginSize=MARGIN_PX)
    #cv2.imshow("img", img)
    #cv2.waitKey(2000)
    cv2.imwrite(SAVE_NAME, img)

create_and_save_new_board()

# ------------------------------
# ENTER YOUR REQUIREMENTS HERE:
ARUCO_DICT = cv2.aruco.DICT_6X6_50
SQUARES_VERTICALLY = 7
SQUARES_HORIZONTALLY = 5
SQUARE_LENGTH = 0.0213
MARKER_LENGTH = 0.0108
# ...

# ------------------------------
def calibrate_and_save_parameters():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    board = cv2.aruco.CharucoBoard((SQUARES_VERTICALLY, SQUARES_HORIZONTALLY), SQUARE_LENGTH, MARKER_LENGTH, dictionary)
    params = cv2.aruco.DetectorParameters()

    all_charuco_corners = []
    all_charuco_ids = []
    images = ["0.png","1.png", "2.png", "3.png", "4.png", "5.png", "6.png", "7.png", "8.png", "9.png", "10.png", "11.png", "12.png", "13.png", "14.png","15.png", "16.png", "17.png", "18.png", "19.png", "20.png"] # Your list of image filenames

    for image_file in images:
        image = cv2.imread(image_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        marker_corners, marker_ids, _ = cv2.aruco.detectMarkers(gray, ARUCO_DICT, params)
        
    if marker_ids is not None:
        charuco_retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(marker_corners, marker_ids, gray, board)
        if charuco_retval:
            all_charuco_corners.append(charuco_corners)
            all_charuco_ids.append(charuco_ids)

    # Perform camera calibration
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(all_charuco_corners, all_charuco_ids, gray.shape[::-1], None, None)
    if ret:
        np.save('camera_matrix.npy', camera_matrix)
        np.save('dist_coeffs.npy', dist_coeffs)
    else:
        print("Calibration failed.")   
    

    
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
   
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (7,6),None)
    
        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
   
            cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners)
   
            # Draw and display the corners
            cv2.drawChessboardCorners(img, (7,6), corners2,ret)
            cv2.imshow('img',img)
            cv2.waitKey(500)
   
    cv2.destroyAllWindows()

    
    # Calibrate camera
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
    # Save calibration data
    np.save('camera_matrix.npy', camera_matrix)
    np.save('dist_coeffs.npy', dist_coeffs)

    # Iterate through displaying all the images of the board
    for image_file in images:
        image = cv2.imread(image_file)
        undistorted_image = cv2.undistort(image, camera_matrix, dist_coeffs)
        #cv2.imshow('Undistorted Image', undistorted_image)
        #cv2.waitKey(0)

    cv2.destroyAllWindows()

calibrate_and_save_parameters()



#LCD screen stuff
# I2C address of the Arduino, set in Arduino sketch
ARD_ADDR = 8
offset = 0

#set up LCD screen
lcd_columns = 16
lcd_rows = 2

#create queue q
q = queue.Queue()
'''
#i2c bus for LCD
i2c_lcd = board.I2C()
lcd = character_lcd.Character_LCD_RGB_I2C(i2c_lcd, lcd_columns, lcd_rows)

def LCD_Display():
    #create LCD class
    lcd=character_lcd.Character_LCD_RGB_I2C(i2c_lcd,lcd_columns,lcd_rows)
    lcd.clear()
    while True:
        if not q.empty():
            location = q.get()
            lcd.clear()
            lcd.message="Desied Location:\n" + str(location)

LCDthread = threading.Thread(target=LCD_Display,args=())
LCDthread.start()
'''






# Initialize SMBus library with I2C bus 1
i2c = SMBus(1)


#calculate focal length of camera
camera_matrix=np.load("camera_matrix.npy")
dist_coeffs = np.load("dist_coeffs.npy")

#camera_matrix = np.array([[671.09226718, 0, 338.40076081],[0, 673.42201483, 248.89317651],[0, 0, 1]])

#dist_coeffs = np.array([0.12563296, -0.77214271, 0.00728876, 0.01058025, 1.37633237])
print("Camera Matrix:", camera_matrix)
print("Dist Coeffs:", dist_coeffs)

f_x = camera_matrix[0][0]
f_y = camera_matrix[1][1]
c_x = camera_matrix[0][2]
c_y = camera_matrix[1][2]

import cv2
from cv2 import aruco
import numpy as np

ARUCO_DICT = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
parameters = aruco.DetectorParameters()
    
# initialize the camera. If channel 0 doesn't work, try channel 1
camera = cv2.VideoCapture(0)

# Let the camera warmup
#sleep(1)

angle = "empty"
previousAngle = "empty"
    
while(True):
    # Get an image from the camera stream
    ret, image = camera.read()

    if not ret:
        print("Failed to read image")
        break

    undistortImg = cv2.undistort(image, camera_matrix, dist_coeffs)
    
    gray = cv2.cvtColor(undistortImg, cv2.COLOR_BGR2GRAY)
    corners,ids,rejected = aruco.detectMarkers(gray, ARUCO_DICT, parameters=parameters)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(gray, corners, ids)
        
        
        markerSizeInM = 0.039
        #t_vec contains distance to marker as a z value
        r_vec, t_vec, _ = aruco.estimatePoseSingleMarkers(corners, markerSizeInM, camera_matrix, dist_coeffs)
        #print(t_vec[0][0][0])
        markerDistance = t_vec[0][0][2]
        print("Dist:")
        print(markerDistance)
        angleRad = math.atan2(1 - t_vec[0][0][0], t_vec[0][0][2])
        print("T_vec:")
        print(t_vec)
        angle = angleRad *180 / np.pi
        print("Angle:")
        print(angle)
        #note if error too large, account for distance between camera lens and camera shell
        '''if previousAngle != angle:
            q.put(angle)
        previousAngle = angle
'''
    cv2.imshow("gray", gray)
    #cv2.imshow("Img", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
    
    
