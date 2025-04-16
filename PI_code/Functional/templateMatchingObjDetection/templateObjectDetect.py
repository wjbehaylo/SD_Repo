from matplotlib import pyplot as plt
import time
import cv2
import numpy as np

#constants
WIDTH = 1920
HEIGHT = 1080

# initialize the camera and grab a reference to the raw camera capture
camera = cv2.VideoCapture(0)
camera.set(cv.CAP_PROP_FRAME_WIDTH, WIDTH)
camera.set(cv.CAP_PROP_FRAME_HEIGHT, HEIGHT)

template_paths = ['RocketBody.jpg', 'CubeSat.png', 'Starlink.jpg']
templates = [cv2.imread(template_path, 0) for template_path in template_paths]


# allow the camera to warmup
time.sleep(0.1)

#capture frames from the camera
while True:
    ret, frame = camera.read()

    if not ret:
        print("FAILED!")
        break

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr",
                                       use_video_port=True):
    # grab the raw NumPy array representing the image,
    # then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array

    # we do something here
    # we get the image or something then run some matching
    # if we get a match, we draw a square on it or something
    img_rbg = image

    img_gray = cv2.cvtColor(img_rbg, cv2.COLOR_BGR2GRAY)

    for template in templates:
        w, h = template.shape[::-1]
        
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        
        threshold = 0.8
        loc = np.where(res >= threshold)

        for pt in zip(*loc[::-1]):
            cv2.rectangle(image, (pt[1]. pt[0]), (pt[1] + w, pt[0] + h),
                      (0,0,255), 2)

    # show the frame
    cv2.imshow("Frame", img_rbg)
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    #rawCapture.truncate(0)

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break