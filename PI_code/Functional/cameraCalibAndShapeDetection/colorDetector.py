import cv2
import numpy as np
import time
from smbus2 import SMBus
from time import sleep
import threading
import math
#from imutils import paths
#import imutils


# Initialize SMBus library for I2C communication (using bus 1)
ARUINO_I2C_ADDRESS = 8
#i2c_bus = SMbus(1)
#Flags 
is_running = True
need_color = True #turn on color detection immediately

# Load Camera Calibration Data
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")
# Extract focal lengths (pixels)
fx = camera_matrix[0, 0]
fy = camera_matrix[1, 1]

#flags for debris detection and I2C data
debris_found = False
#dataSent = False

# Shared frames + lock
frame_lock      = threading.Lock()
color_frame     = None
distance_frame  = None

# Degrees and Distance variables
angle_degrees = None
distance_to_object = None
debris_color = None

#different state variables
over_state = False
starter = True
count_to_over = 0
searcher = True

HEIGHT = 1080
WIDTH = 1920


# Initialize webcam
webcam = cv2.VideoCapture(0)
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
webcam.set(cv2.CAP_PROP_BRIGHTNESS, 250)
webcam.set(cv2.CAP_PROP_EXPOSURE, 39) 
webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
webcam.set(cv2.CAP_PROP_FPS, 120)


def capture_frame(): 
	# Capture frames from current camera in separate thread
	global color_frame, is_running, distance_frame
	# Continue capturing frames while is_running is True
	while is_running:
		ret, frame = webcam.read()
		# Check if frame capture was successful
		if not ret:
			print("Failed to capture frame")
			is_running = False
			return
		#undistort the image
		und = cv2.undistort(frame, camera_matrix, distortion_coeffs)

		 # safely hand off to the detector
		with frame_lock:
			color_frame    = und.copy()
			distance_frame = und.copy()
			
	webcam.release()


def debris_detect():
	global is_running, need_color, debris_color

	# Continue processing frames while is_running is True
	while (is_running):
		with frame_lock:
			snap = color_frame.copy() if color_frame is not None else None
			
		if snap is None:
			time.sleep(1)
			continue
		
		if need_color:
			hsv = cv2.cvtColor(snap, cv2.COLOR_BGR2HSV)
			print("In debris color")
		
			# red
			lower1 = np.array([170, 120, 70], np.uint8)
			upper1 = np.array([180, 255, 255], np.uint8)
			lower2 = np.array([0, 120, 70], np.uint8)
			upper2 = np.array([10, 255, 255], np.uint8)
			red_mask1 = cv2.inRange(hsv, lower1, upper1)
			red_mask2 = cv2.inRange(hsv, lower2, upper2)

			#Set range for green color and define mask
			green_lower = np.array([50, 100, 100], np.uint8)
			green_upper = np.array([70, 255, 255], np.uint8)
			green_mask = cv2.inRange(hsv, green_lower, green_upper) 

			# Set range for blue color and define mask
			blue_lower = np.array([30, 40, 40], np.uint8)
			blue_upper = np.array([90, 255, 255], np.uint8)
			blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)

			kernel = np.ones((5, 5), "uint8")
			red_mask1 = cv2.dilate(red_mask1, kernel) 
			red_mask2 = cv2.dilate(red_mask2, kernel) 
			mask_red = cv2.bitwise_or(red_mask1, red_mask2)
			res_red1   = cv2.bitwise_and(snap, snap, mask=red_mask1)
			res_red2   = cv2.bitwise_and(snap, snap, mask=red_mask2)

			# For green color 
			green_mask = cv2.dilate(green_mask, kernel) 
			res_green   = cv2.bitwise_and(snap, snap, mask=green_mask)

			#For blue
			blue_mask = cv2.dilate(blue_mask, kernel)
			res_blue   = cv2.bitwise_and(snap, snap, mask=blue_mask)

			# ─── Detection flags ─────────────────────────────────────────
			redDetected   = False
			greenDetected = False
			blueDetected  = False

			contoursR1, hierarchy = cv2.findContours(red_mask1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			for pic, contour in enumerate(contoursR1):
				if cv2.contourArea(contour) > 500:
					x, y, w, h = cv2.boundingRect(contour)
					snap = cv2.rectangle(snap, (x, y), (x + w, y + h), (0, 0, 255), 2)
					if len(contoursR1) >= 6:
						cv2.putText(snap, "RocketBody Detected!", (x, y - 10),
								cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
						debris_color = "red"
						need_color   = False
						redDetected  = True
			
			
			contoursR2, hierarchy = cv2.findContours(red_mask2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			for pic, contour in enumerate(contoursR2):
				if cv2.contourArea(contour) > 300:
					x, y, w, h = cv2.boundingRect(contour)
					snap = cv2.rectangle(snap, (x, y), (x + w, y + h), (0, 0, 255), 2)
					if len(contoursR2) >= 6:
						cv2.putText(snap, "RocketBody Detected!", (x, y - 10),
								cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
						debris_color = "red"
						need_color   = False
						redDetected  = True

			# — Green
			contoursG, hierarchy = cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			for pic, contour in enumerate(contoursG):
				if cv2.contourArea(contour) > 300:
					x, y, w, h = cv2.boundingRect(contour)
					snap = cv2.rectangle(snap, (x, y), (x + w, y + h), (0, 255, 0), 2)
					if len(contoursG) >= 6:
						cv2.putText(snap, "Starlink Detected!", (x, y - 10),
								cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
						debris_color = "green"
						need_color = False
						greenDetected = True

			# — Blue
			contoursB, hierarchy = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			for pic, contour in enumerate(contoursB):
				if cv2.contourArea(contour) > 300:
					x, y, w, h = cv2.boundingRect(contour)
					snap = cv2.rectangle(snap, (x, y), (x + w, y + h), (255, 0, 0), 2)
					if len(contoursB) >= 6:
						cv2.putText(snap, "CubeSat Detected!", (x, y - 10),
								cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
						debris_color = "blue"
						need_color   = False
						blueDetected = True
		



			# show and check for quit
			cv2.imshow("Debris Detection", snap)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				is_running = False
				webcam.release() 
				cv2.destroyAllWindows() 
				break

if __name__ == "__main__":
	# start threads
	t1 = threading.Thread(target=capture_frame, daemon=True)
	t2 = threading.Thread(target=debris_detect, daemon=True)
	t1.start()
	t2.start()

	# wait for detection thread to finish
	t2.join()
	# capture thread will exit when is_running → False


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
