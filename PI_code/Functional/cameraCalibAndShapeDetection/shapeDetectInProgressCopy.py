import cv2
import numpy as np
import time
import threading

# === Configuration ===
WIDTH, HEIGHT      = 1280, 720
MIN_CONTOUR_AREA   = 1000   # ignore small specks
D                  = 1.0    # assumed, constant object distance [m]
TOLERANCE          = 0.05   # ±5 cm tolerance

# Known object widths [m]
KNOWN_WIDTHS = {
    "CubeSat":   0.10,
    "Starlink":  0.70,
    "RocketBody":0.62
}

# Load camera calibration
camera_matrix    = np.load("camera_matrix.npy")
distortion_coeff = np.load("distortion_coeffs.npy")

# focal length in pixels (we assume fx = fy)
f_px = camera_matrix[0, 0]

is_running = True

def detection_loop(cam):
    global is_running
    while is_running:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # undistort
        frame = cv2.undistort(frame, camera_matrix, distortion_coeff)

        # simple edge map
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges   = cv2.Canny(blurred, 50, 150)

        # find & filter contours
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = [c for c in cnts if cv2.contourArea(c) > MIN_CONTOUR_AREA]

        for c in cnts:
            # 1) get axis‐aligned bounding box
            x, y, w, h = cv2.boundingRect(c)

            # 2) estimate real width [m] from pinhole model
            real_w = (w * D) / f_px
            print(f"Pixel width={w}, Real width={real_w:.2f} m")

            # 3) classify by nearest known width
            obj_type = "Unknown"
            for name, kw in KNOWN_WIDTHS.items():
                if abs(real_w - kw) <= TOLERANCE:
                    obj_type = name
                    break

            # 4) draw results
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, obj_type, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Size‑Based Classification", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            is_running = False

def main():
    global is_running
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    t = threading.Thread(target=detection_loop, args=(cam,))
    t.start()

    try:
        while is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        is_running = False

    t.join()
    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
