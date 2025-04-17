from matplotlib import pyplot as plt
import time
import cv2
import numpy as np

#constants
WIDTH = 1920
HEIGHT = 1080

# initialize the camera and grab a reference to the raw camera capture
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

templateCubeSat = cv2.imread('CubeSat.png', cv2.IMREAD_GRAYSCALE)

# allow the camera to warmup
time.sleep(0.1)

#capture frames from the camera
while True:
    ret, frame = camera.read()

    if not ret:
        print("FAILED!")
        break
        
    img_rgb = frame
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    w, h = templateCubeSat.shape[::-1]

    # Template Matching
    res = cv2.matchTemplate(img_gray, templateCubeSat, cv2.TM_CCOEFF_NORMED)

    threshold = 0.8  # You can adjust this threshold
    loc = np.where(res >= threshold)

    for pt in zip(*loc[::-1]):
            cv2.rectangle(img_rgb, (pt[0], pt[1]), (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

    # show the frame with matches from all templates
    cv2.imshow("Frame", img_rgb)

    key = cv2.waitKey(1) & 0xFF

    # if the 'q' key was pressed, break from the loop
    if key == ord("q"):
        break

# release the webcam and close windows
camera.release()
cv2.destroyAllWindows()
