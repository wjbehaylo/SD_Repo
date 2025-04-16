import cv2
import numpy as np
import glob
import os

# ─── PARAMETERS ───────────────────────────────────────────────────────────────
VIDEO_SOURCE  = 0                # 0 = default webcam, or replace with "your_video.mp4"
MATCH_METHOD  = cv2.TM_CCOEFF_NORMED
THRESHOLD     = 0.6             # tune between 0.6–0.95 depending on your templates
FONT          = cv2.FONT_HERSHEY_SIMPLEX
# ────────────────────────────────────────────────────────────────────────────────

# 1. Load templates into a dict: { label: gray_image }
TEMPLATE_DIR = {
    "CubeSat": "templates/CubeSat/*.png",
    "Minotaur": "templates/Minotaur/*.png",
    "Starlink": "templates/Starlink/*.png"
}
templates = {}
for tpl_path in glob.glob(os.path.join(TEMPLATE_DIR, "*", "*.png")):
    label = os.path.basename(os.path.dirname(tpl_path))  # folder name as label
    img   = cv2.imread(tpl_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read {tpl_path}")
    templates.setdefault(label, []).append(img)

# 2. Open video capture
cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video source {VIDEO_SOURCE}")

while True:
    ret, frame = cap.read()
    if not ret: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    for label, tpl_list in templates.items():
        for tpl in tpl_list:
            h, w = tpl.shape
            res   = cv2.matchTemplate(gray, tpl, MATCH_METHOD)

            # find all matches above threshold
            loc = np.where(res >= THRESHOLD)
            for pt in zip(*loc[::-1]):  # switch x,y
                score = res[pt[1], pt[0]]
                top_left     = pt
                bottom_right = (pt[0] + w, pt[1] + h)
                cv2.rectangle(frame, top_left, bottom_right, (0,255,0), 2)
                cv2.putText(frame,
                            f"{label} {res[pt[1],pt[0]]:.2f}",
                            (pt[0], pt[1]-10),
                            FONT, 0.6, (0,255,0), 1,
                            cv2.LINE_AA)
                print(f"Match: {label}@{pt}, score={score:.2f}")

    cv2.imshow("Live Template Matching", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
