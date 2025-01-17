#EENG350 - Demo 1 

import cv2
import threading
import time
import board
import numpy as np
import board
import adafruit_character_lcd.character_lcd_rgb_i2c as charcter_lcd
from cv2 import aruco
from smbus2 import SMBus
from time import sleep
import math

# Define I2C address for Arduino
ARUINO_I2C_ADDRESS = 8

# Initialize SMBus library for I2C communication (using bus 1)
i2c_bus = SMBus(1)

# Creating an ArUco dictionary from library
aruco_marker_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)

# Initialize camera
# Open camera with index 0
camera = cv2.VideoCapture(0)
# Set camera frames per second to 60
camera.set(cv2.CAP_PROP_FPS, 60)
# Width of camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
# Height of camera
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 

# Global variables
# Current frame captured from camera
current_frame = None
# Create a lock for thread-safe frame access
frame_lock = threading.Lock()
#Flag to control main loop
is_running = True

# Initializing the LCD display
lcd_columns = 16
lcd_rows = 2
# Create I2C instance for the LCD
i2c_lcd = board.I2C()
lcd = charcter_lcd.Character_LCD_RGB_I2C(i2c_lcd, lcd_columns, lcd_rows)
#Clear any exisiting messages on the LCD
lcd.clear()


#calculate focal length of camera
camera_matrix=np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")
# Extract the focal length
focal_points = [camera_matrix[0, 0], camera_matrix[1, 1]]

# Length of marker in CM
marker_axis_length = 4.84

# Known width of the ArUco marker in inches
known_marker_width = 1.90625


def capture_frame(): 
    # Capture frames from current camera in separate thread
    global current_frame, is_running, frame_lock
    # Continue capturing frames while is_running is True
    while is_running:

        ret, frame = camera.read()
        # Check if frame capture was successful
        if ret:
            # Ensure thread-safe access to current_frame
            with frame_lock:
                current_frame = frame
            


def ARUCO_angle_and_distance():
    
    # Process captured frames to detect ArUco markers and calculate their angles and distance
    global current_frame, is_running, frame_lock, known_marker_width, camera_matrix, distortion_coeffs
    # Continue processing frames while is_running is True
    while is_running:

        with frame_lock:
            # Check if there is a current frame
            if current_frame is not None:
                #undistort the image
                ret, frame = camera.read()
                if not ret:
                    print("Failed to capture image!")
                    break
                
                undistort_frame = cv2.undistort(current_frame, camera_matrix, distortion_coeffs)
                # Convert the image to grayscale for ArUco detection
                gray_frame = cv2.cvtColor(undistort_frame, cv2.COLOR_BGR2GRAY)
                # Display the gray frame
                cv2.imshow("Overlay", gray_frame)

                # Detect ArUco markers in grayscale image
                marker_corners, marker_ids, rejected_markers = aruco.detectMarkers(gray_frame, aruco_marker_dict)
                
                # Prepare overlay image for visualization
                overlay_image = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
                # Draw detected markers
                overlay_image = aruco.drawDetectedMarkers(overlay_image, marker_corners, borderColor=(0, 255, 0))

                # Initialize message for LCD
                angle_message = "Angle is: "

                if marker_ids is not None:
                    #Flatten the ids for easier access
                    marker_ids = marker_ids.flatten()
                    for (outline, marker_id) in zip(marker_corners, marker_ids):
                        #Reshape corners for processing
                        marker_corners_reshaped = outline.reshape((4, 2))
                        #Put marker ID on overlay
                        
                        overlay_image = cv2.putText(overlay_image, str(marker_id),
                                              (int(marker_corners_reshaped[0, 0]), int(marker_corners_reshaped[0, 1]) - 15),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                        # Estimate pose of the detected marker
                        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(outline, marker_axis_length, camera_matrix, distortion_coeffs)

                        # Drawing axis on overlay for visual feedback
                        for i in range(len(marker_ids)):
                            cv2.drawFrameAxes(overlay_image, camera_matrix, distortion_coeffs, rvec, tvec, .1)
                            i = i + 1

                    

                        # Create a point at the origin to project
                        origin_point = np.array([[[0, 0, 0]]], dtype=np.float64)  # Define the origin point
                    
                        
                        #Projecting the origin point to the camera plane
                        projected_marker_point, _ = cv2.projectPoints(origin_point, rvec, tvec, camera_matrix, distortion_coeffs)

                        # Extract x and y coordinates of the projected point
                        x, y= projected_marker_point[0][0]

                        # Calculate angle of ArUco relative to camera
                        #angle_radians = (np.arctan2((x - camera_matrix[0][2]), camera_matrix[0][0]))
                        angle_radians = np.arctan2(tvec[0][0][0], tvec[0][0][2])

                        #accounting for fudge factor by subtracting 2 degrees
                        angle_degrees = -1*(round((angle_radians * (180 / np.pi)),2) - .48)

                        # Update the message on LCD display
                        angle_message += str(angle_degrees)

                        lcd.message = angle_message
                        
                        print("Angle in Degrees: ", angle_degrees)
                        print("TVEC: ", tvec)

                        #Calculate distance to the marker
                        
                        corner_array = np.array(marker_corners)[0][0] #Extract corners for distance calc
                        
                        corner_x_array = (corner_array[0][0], corner_array[1][0], corner_array[2][0], corner_array[3][0]) #Get x-coordinates of corners
                        corner_y_array = (corner_array[0][1], corner_array[1][1], corner_array[2][1], corner_array[3][1])
                        #Calculate the width of the marker in pixels
                        marker_width_pixels = math.sqrt((corner_x_array[1] - corner_x_array[0])**2 + (corner_y_array[1] - corner_y_array[0])**2)
                        
                        '''
                        print("marker_width_pixels", marker_width_pixels)
                        print("corner_x_array[1]", corner_x_array[1])
                        print("corner_x_array[0]", corner_x_array[0])
                        '''     
                        #Estimate the distance to the marker using known width
                        distance_to_marker = (known_marker_width * (focal_points[0])) / marker_width_pixels
                        #print("Distance to marker: ", distance_to_marker)
                        #print("Horizontal distance: ", tvec[0][0][0]/2.54)
                        #print("Distance tvec: ", tvec[0][0][2]/2.54)
                        
   

                cv2.imshow("Overlay", overlay_image) #Show the overlay with detected markers

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    is_running = False
                    break

    
        
def main():
    #Main function to start capturing and processing frames
    global is_running
    #Start threads for capturing and processing frames
    capture_thread = threading.Thread(target=capture_frame) 
    process_thread = threading.Thread(target=ARUCO_angle_and_distance)

    capture_thread.start()
    process_thread.start()

    try:
        while is_running:
            #capture_frame()
            #ARUCO_angle_and_distance()
            time.sleep(0.1)  # Main thread can handle other tasks if necessary
    except KeyboardInterrupt:
        is_running = False

    capture_thread.join()
    process_thread.join()
    
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
