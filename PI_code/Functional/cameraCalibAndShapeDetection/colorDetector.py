import cv2
import numpy as np
import time
from smbus2 import SMBus
from time import sleep
import threading
import math
from imutils import paths
import imutils


# Initialize SMBus library for I2C communication (using bus 1)
ARUINO_I2C_ADDRESS = 8
#i2c_bus = SM(1)

# Global variables
global status, searcher, color_frame, over_state, need_color, angle_degrees, distance_to_object, debris_color, dataSent, starter,count_to_over

#flags for debris detection and I2C data
debris_found = False
dataSent = False

# Degrees and Distance variables
angle_degrees = None
distance_to_object = None
debris_color = None

#flag for color needed
need_color = False

#different imageg frames from camera for image processing
current_frame = None
color_frame = None
distance_frame = None

#different state variables
over_state = False
starter = True

#count of frames 
count_to_over = 0

#flag for searching
searcher = True

# Create a lock for thread-safe frame access
frame_lock = threading.Lock()

#Flag to control main loop
is_running = True

# Initialize webcam
webcam = cv2.VideoCapture(0) 
webcam.set(cv2.CAP_PROP_FPS, 30) #set frames per second so the camera doesn't get overwhelmed
# Load Camera Calibration Data
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")
# Extract focal lengths (pixels)
fx = camera_matrix[0, 0]
fy = camera_matrix[1, 1]

def capture_frame(): 
    # Capture frames from current camera in separate thread
    global current_frame, is_running, color_frame, distance_frame
    # Continue capturing frames while is_running is True
    while is_running:
        ret, frame = webcam.read()
        # Check if frame capture was successful
        if ret and current_frame is not None:
            # Ensure thread-safe access to current_frame
            current_frame = frame
			undistort_frame = cv2.undistort(current_frame, camera_matrix, distortion_coeffs)
            color_frame = undistort_frame.copy()
			distance_frame = undistort_frame.copy()

def debris_detect():
	# Process captured frames to detect ArUco markers and calculate their angles and distance
    global is_running, frame_lock, debris_found, debris_color, need_color, color_frame, is_running
    # Continue processing frames while is_running is True
	# Continue processing frames while is_running is True
    while (is_running):

        if color_frame is not None and need_color == True:
			print("In arrowColor")
            #Apply erosion to image
            kernel = np.ones((5,5), "uint8")
            opening = cv2.morphologyEx(color_frame, cv2.MORPH_OPEN, kernel)
			#Convert image to HSV for color detection
			hsv_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV) 
		
			# Set range for red color and define mask 
			red_lower = np.array([136, 87, 111], np.uint8) 
			red_upper = np.array([180, 255, 255], np.uint8) 
			red_lower2 = np.array([0,150,170])
			red_upper2 = np.array([10, 255, 255])
			red_mask = cv2.inRange(hsv_frame, red_lower, red_upper) 
			red_mask2 = cv2.inRange(hsv_frame, red_lower2, red_upper2) 

			# Set range for green color and define mask 
			green_lower = np.array([50, 52, 72], np.uint8) 
			green_upper = np.array([102, 255, 255], np.uint8) 
			green_mask = cv2.inRange(hsv_frame, green_lower, green_upper) 

			# Set range for blue color and define mask 
			blue_lower = np.array([94, 80, 2], np.uint8) 
			blue_upper = np.array([120, 255, 255], np.uint8) 
			blue_mask = cv2.inRange(hsv_frame, blue_lower, blue_upper) 
			
			#detection flags
			green_detected = False
			red_detected = False
			blue_detected = False
				
			# Morphological Transform, Dilation 
			# for each color and bitwise_and operator to detect only that particular color 
			
			# For red color 
			red_mask = cv2.dilate(red_mask, kernel) 
			res_red = cv2.bitwise_and(color_frame, color_frame, 
										mask = red_mask) 
			red_mask2 = cv2.dilate(red_mask, kernel) 
			res_red2 = cv2.bitwise_and(color_frame, color_frame, 
										mask = red_mask2)
			# For green color 
			green_mask = cv2.dilate(green_mask, kernel) 
			res_green = cv2.bitwise_and(color_frame, color_frame, 
											mask = green_mask) 
			# For blue color 
			blue_mask = cv2.dilate(blue_mask, kernel) 
			res_blue = cv2.bitwise_and(color_frame, color_frame, 
										mask = blue_mask) 

			# Creating contour to track red color 
			contoursRed, hierarchy = cv2.findContours(red_mask, 
													cv2.RETR_TREE, 
													cv2.CHAIN_APPROX_SIMPLE)
			for pic, contour in enumerate(contoursRed): 
				area = cv2.contourArea(contour) 
				if(area > 300): 
					x, y, w, h = cv2.boundingRect(contour) 
					imageFrame = cv2.rectangle(imageFrame, (x, y), 
											(x + w, y + h), 
											(0, 0, 255), 2) 
					
					cv2.putText(imageFrame, "RocketBody Detected!", (x, y), 
								cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
								(0, 0, 255))	 
			# Creating contour to track red color 
			contoursRed2, hierarchy = cv2.findContours(red_mask2, 
													cv2.RETR_TREE, 
													cv2.CHAIN_APPROX_SIMPLE)
			for pic, contour in enumerate(contoursRed): 
				area = cv2.contourArea(contour) 
				if(area > 300): 
					x, y, w, h = cv2.boundingRect(contour) 
					imageFrame = cv2.rectangle(imageFrame, (x, y), 
											(x + w, y + h), 
											(0, 0, 255), 2) 
					
					cv2.putText(imageFrame, "RocketBody Detected!", (x, y), 
								cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
								(0, 0, 255))	

			# Creating contour to track green color 
			contoursGreen, hierarchy = cv2.findContours(green_mask, 
												cv2.RETR_TREE, 
												cv2.CHAIN_APPROX_SIMPLE) 
			
			for pic, contour in enumerate(contoursGreen): 
				area = cv2.contourArea(contour) 
				if(area > 300): 
					x, y, w, h = cv2.boundingRect(contour) 
					imageFrame = cv2.rectangle(imageFrame, (x, y), 
											(x + w, y + h), 
											(0, 255, 0), 2) 
					
					cv2.putText(imageFrame, "Minotaur Detected!", (x, y), 
								cv2.FONT_HERSHEY_SIMPLEX, 
								1.0, (0, 255, 0)) 
					
			# Creating contour to track blue color 
			contoursBlue, hierarchy = cv2.findContours(blue_mask, 
												cv2.RETR_TREE, 
												cv2.CHAIN_APPROX_SIMPLE) 
			for pic, contour in enumerate(contoursBlue): 
				area = cv2.contourArea(contour) 
				if(area > 300): 
					x, y, w, h = cv2.boundingRect(contour) 
					imageFrame = cv2.rectangle(imageFrame, (x, y), 
											(x + w, y + h), 
											(255, 0, 0), 2) 
					
					cv2.putText(imageFrame, "CubeSat Detected!", (x, y), 
								cv2.FONT_HERSHEY_SIMPLEX, 
								1.0, (255, 0, 0)) 
					
			# Program Termination 
			cv2.imshow("Debris:", imageFrame) 
			if cv2.waitKey(10) & 0xFF == ord('q'): 
				webcam.release() 
				cv2.destroyAllWindows() 
				break

'''
# ───── CONFIGURATION ─────
KNOWN_DISTANCE = 1.0  # meters (distance from camera to debris in captured frame)

# Known real-world widths in meters
DEBRIS_SPECS = {
    "CubeSat":   {"known_width": 0.11},
    "Rock":      {"known_width": 0.02},
    "Minotaur":  {"known_width": 0.03},
}
# load the first image that contains an object that is KNOWN TO BE 1 meter
# from our camera, then find the debris in the image, and initialize
# the focal length

def find_marker(distance_frame):
	# convert the image to grayscale, blur it, and detect edges
	gray = cv2.cvtColor(distance_frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (5, 5), 0)
	edged = cv2.Canny(gray, 35, 125)
	# find the contours in the edged image and keep the largest one;
	# we'll assume that this is our debris in the image
	cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	c = max(cnts, key = cv2.contourArea)

	# compute the bounding box of the of the debris region and return it
	return cv2.minAreaRect(c)

def distance_to_camera(known_width, focal_length, pixel_width):
    return (known_width * focal_length) / pixel_width

distance_frame = cv2.imread("images/2ft.png")
marker = find_marker(distance_frame)

if marker is None: 
	print("No debris found in distance frame!")

pixel_width = marker[1][0]  # width side of the box
print(f"[INFO] Reference marker width in pixels: {pixel_width:.2f}")

for name, spec in DEBRIS_SPECS.items():
    focal = (pixel_width * KNOWN_DISTANCE) / spec["known_width"]
    spec["focal_length"] = focal
    print(f"{name:10s} → focal = {focal:.2f} px")

    if marker is not None:
        px_width = marker[1][0]
        for name, spec in DEBRIS_SPECS.items():
            dist = distance_to_camera(spec["known_width"], spec["focal_length"], px_width)

            box = cv2.boxPoints(marker)
            box = np.int0(box)
            cv2.drawContours(distance_frame, [box], -1, (0, 255, 0), 2)
            cv2.putText(distance_frame, f"{name}: {dist:.2f}m", (30, 40 + 40 * list(DEBRIS_SPECS).index(name)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    cv2.imshow("Live Debris Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
'''
