import cv2
import numpy as np
import time
from time import sleep
import threading
import math
import globals #this declared the global variables that we will be using

#from imutils import paths
#import imutils

def capture_frame(): 
	# Capture frames from current camera in separate thread
	# Continue capturing frames while SYS_running is True
	
	
	# Load Camera Calibration Data
	camera_matrix = np.load("camera_matrix.npy")
	distortion_coeffs = np.load("distortion_coeffs.npy")
	# Extract focal lengths (pixels)
	fx = camera_matrix[0, 0]
	fy = camera_matrix[1, 1]

 	# Initialize webcam
	HEIGHT = 1080
	WIDTH = 1920
	webcam = cv2.VideoCapture(0)
	webcam.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
	webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
	
	#set global flag
	with globals.running_lock:
		globals.CAM_running=True
	#debugging
	print("Capture frame running")
	
	#create a local copy of SYS_running
	with globals.running_lock:
		my_SYS_running=globals.SYS_running
	#this might break stuff tbh, from like race conditions, maybe I need to status lock it
	while my_SYS_running:
		#debugging, maybe this should be always running? Maybe only when run_cv is true
		#if(run_CV==0):
		#	time.sleep(1) #wait 1 second before checking the thread again
		#	continue
		ret, frame = webcam.read()
		# Check if frame capture was successful
		if not ret:
			print("Failed to capture frame")
			with globals.running_lock:
				globals.SYS_running = False
			return
		#undistort the image
		und = cv2.undistort(frame, camera_matrix, distortion_coeffs)

		#debugging
		#cv2.imshow("Undisorted",und)

		# safely hand off to the detector
		# only if the threads are not currently locked, save the new frame to be analyzed
		with globals.frame_lock: 
			globals.color_frame    = und.copy()
		#this might lowkey monopolize the running_lock. 
  		#I don't want to get gridlock from overlapping mutexes, which I gotta watch out for with debris_detect and capture_frame
		with globals.running_lock:
			my_SYS_running=globals.SYS_running

	webcam.release()
	globals.CAM_running=False
	return


def debris_detect():
 
	#inform that CV is going
	with globals.running_lock:
		globals.CV_running = True
	# Continue processing frames while SYS_running is True
	
	#debugging
	print("Debris detect running")
	#start the loop off strong
	my_SYS_running=True
	while (my_SYS_running):
		with globals.running_lock:
			my_SYS_running=globals.SYS_running
		#we only want to run through this loop if run_CV is 1, meaning that the FSM is trying to detect a new object
		#we will set run_CV to be 0 after we have finished finding the color

		#we want to only do this loop when we need to detect the debris, not constantly
  
		with globals.camera_lock:
			#I added this sleep in because I think it was going too fast
			sleep(0.1)
			if(globals.run_CV == 0):
				continue
			need_color=True
		
		#debugging
		print("starting CV search")
		#try to get the most recently captured frame from capture_frame() thread
		with globals.frame_lock:
			snap = globals.color_frame.copy() if globals.color_frame is not None else None
			
		#if snap is None (because capture_frame hasn't read for some reason), we restart the loop
		if snap is None:
			time.sleep(1)
			continue
		
		hsv = cv2.cvtColor(snap, cv2.COLOR_BGR2HSV)
		print("In debris color")
	
		# red
		lower1 = np.array([170, 150, 100], np.uint8)
		upper1 = np.array([180, 255, 255], np.uint8)
		lower2 = np.array([0, 150, 170], np.uint8)
		upper2 = np.array([20, 255, 255], np.uint8)
		red_mask1 = cv2.inRange(hsv, lower1, upper1)
		red_mask2 = cv2.inRange(hsv, lower2, upper2)

		#Set range for green color and define mask
		green_lower = np.array([40, 100, 70], np.uint8)
		green_upper = np.array([80, 255, 155], np.uint8)
		green_mask = cv2.inRange(hsv, green_lower, green_upper) 

		# Set range for blue color and define mask
		blue_lower = np.array([100, 50, 50], np.uint8)
		blue_upper = np.array([130, 255, 255], np.uint8)
		blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)

		kernel = np.ones((5, 5), "uint8")
		red_mask1 = cv2.dilate(red_mask1, kernel) 
		red_mask2 = cv2.dilate(red_mask2, kernel) 
		#debugging mask_red = cv2.bitwise_or(red_mask1, red_mask2)
		#debugging res_red1   = cv2.bitwise_and(snap, snap, mask=red_mask1)
		#debugging res_red2   = cv2.bitwise_and(snap, snap, mask=red_mask2)

		# For green color 
		green_mask = cv2.dilate(green_mask, kernel) 
		#debugging res_green   = cv2.bitwise_and(snap, snap, mask=green_mask)

		#For blue
		blue_mask = cv2.dilate(blue_mask, kernel)
		#debugging res_blue   = cv2.bitwise_and(snap, snap, mask=blue_mask)

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
					my_detected_debris_type = "Minotaur"
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
					my_detected_debris_type = "Minotaur"
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
					my_detected_debris_type = "Starlink"
					need_color = False
					greenDetected = True

		# — Blue
		contoursB, hierarchy = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		for pic, contour in enumerate(contoursB):
			if cv2.contourArea(contour) > 100:
				x, y, w, h = cv2.boundingRect(contour)
				snap = cv2.rectangle(snap, (x, y), (x + w, y + h), (255, 0, 0), 2)
				if len(contoursB) >= 2:
					cv2.putText(snap, "CubeSat Detected!", (x, y - 10),
							cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
					my_detected_debris_type = "CubeSat"
					need_color   = False
					blueDetected = True

		#if we are no longer looking for a color, we can set run_CV to be low to indicate that we have found our debris
		if(need_color == False):
			with globals.camera_lock:
				globals.detected_debris_type=my_detected_debris_type
				globals.run_CV = 0
		# show and check for quit
		cv2.imshow("Debris Detection", snap)
    #cv2.destroyAllWindows()
    #here we are exiting because SYS_running has been made false
	with globals.running_lock:
		globals.CV_running = False
	return
    
    
    

if __name__ == "__main__":
	# start threads
	t1 = threading.Thread(target=capture_frame, daemon=True)
	t2 = threading.Thread(target=debris_detect, daemon=True)
	t1.start()
	t2.start()

	# wait for detection thread to finish
	t2.join()
	# capture thread will exit when SYS_running → False


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
