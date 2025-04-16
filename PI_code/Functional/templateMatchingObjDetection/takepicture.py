from time import sleep
import numpy as np
import cv2
camera = cv2.VideoCapture(0)
sleep(1)
while True:
    fileName = input("File Name: ")
    # initialize the camera. If channel 0 doesn't work, try channel 1
       # Let the camera warmup
    
    # Get an image from the camera stream
    ret, image = camera.read()
    sleep(1)
    if not ret:
        print("Could not capture image from camera!")
        quit()
    else:
        while True:
            ret, image = camera.read()
            cv2.imshow("image", image)
            k =cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                cv2.destroyAllWindows()
                break
        # Save the image to the disk
        print("Saving image "+fileName)
        try:
            cv2.imwrite(fileName,image)
        except:
            print("Could not save "+fileName)
        pass
