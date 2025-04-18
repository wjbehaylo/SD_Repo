import cv2
import numpy as np

def nothing(x):
    pass

def calibrate_hsv(source=0):
    """
    Launches a window with 6 trackbars (H_min, S_min, V_min, H_max, S_max, V_max).
    Displays your webcam feed and the resulting mask in real time.
    Hit ‘s’ to print and return your chosen ranges; ‘q’ to quit without saving.
    """
    cap = cv2.VideoCapture(source)
    cv2.namedWindow("HSV Calibration")

    # create trackbars for min/max HSV
    for name, val in zip(
        ("H_min","S_min","V_min","H_max","S_max","V_max"),
        (0, 0, 0, 180, 255, 255)
    ):
        cv2.createTrackbar(name, "HSV Calibration", val, 180 if 'H' in name else 255, nothing)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # read trackbar positions
        h0 = cv2.getTrackbarPos("H_min", "HSV Calibration")
        s0 = cv2.getTrackbarPos("S_min", "HSV Calibration")
        v0 = cv2.getTrackbarPos("V_min", "HSV Calibration")
        h1 = cv2.getTrackbarPos("H_max", "HSV Calibration")
        s1 = cv2.getTrackbarPos("S_max", "HSV Calibration")
        v1 = cv2.getTrackbarPos("V_max", "HSV Calibration")

        lower = np.array([h0, s0, v0])
        upper = np.array([h1, s1, v1])
        mask  = cv2.inRange(hsv, lower, upper)

        # show feed and mask side by side
        combined = np.hstack([frame, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
        cv2.imshow("HSV Calibration", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            print(f"Chosen range: lower={lower.tolist()}, upper={upper.tolist()}")
            cap.release()
            cv2.destroyAllWindows()
            return lower, upper
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None, None

if __name__ == "__main__":
    # run this once to get good HSV bounds for a given color
    lower, upper = calibrate_hsv(0)
    if lower is not None:
        print("Apply these in your mask:", lower, upper)
