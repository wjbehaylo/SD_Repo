import cv2
import numpy as np
import glob
import time

# =============================================================================
# Load Calibration Data
# =============================================================================
# Load the previously computed camera matrix and distortion coefficients.
# These are used to undistort raw video frames to correct for lens distortion.
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")

# =============================================================================
# Template Loading with Glob
# =============================================================================
# Define directories (using glob patterns) for each debris category. We assume 
# that you have multiple template images for each category stored in separate folders.
template_dirs = {
    "CubeSat": "templates/CubeSat/*.png",
    "Minotaur": "templates/Minotaur/*.png",
    "Starlink": "templates/Starlink/*.png"
}

# Create a dictionary to store the loaded templates (as grayscale images) for each category.
templates = {}
for category, pattern in template_dirs.items():
    # Get all file paths matching the pattern.
    paths = glob.glob(pattern)
    loaded = []  # Temporary list to store images for this category.
    for path in paths:
        # Load each template image in grayscale.
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            loaded.append(img)
        else:
            print(f"Warning: Could not load template image {path}")
    templates[category] = loaded
    print(f"Loaded {len(loaded)} templates for {category}")

# Set a matching threshold.
# This value determines how good a match must be to trigger detection.
match_threshold = 0.7

# Define a list of scale factors and rotation angles to search over.
scales = [0.8, 0.9, 1.0, 1.1, 1.2]         # To handle variations in object size
angles = [-15, -10, -5, 0, 5, 10, 15]         # To account for rotations (in degrees)

# =============================================================================
# Open Live Video Feed
# =============================================================================
# Open the default camera (index 0). Adjust the index if necessary.
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# =============================================================================
# Main Loop: Process each frame from the video feed
# =============================================================================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # -------------------------------------------------------------------------
    # Undistort the captured frame using the calibration data.
    # This step removes the lens distortion so that our detections
    # are geometrically accurate.
    # -------------------------------------------------------------------------
    undistorted = cv2.undistort(frame, camera_matrix, distortion_coeffs)
    
    # Convert the undistorted frame to grayscale because template matching 
    # is performed on single-channel images.
    gray_frame = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

    # Optionally normalize the grayscale frame via histogram equalization 
    # to improve robustness against varying lighting conditions.
    gray_frame = cv2.equalizeHist(gray_frame)
    
    # Loop over each category and its list of templates.
    for category, template_list in templates.items():
        for tmpl in template_list:
            # Optionally equalize the template image for consistency.
            tmpl_eq = cv2.equalizeHist(tmpl)
            
            # Loop over various scale factors.
            for scale in scales:
                # Resize the template image according to the current scale.
                tmpl_scaled = cv2.resize(tmpl_eq, None, fx=scale, fy=scale)
                
                # Loop over the rotation angles.
                for angle in angles:
                    # If the current angle is not zero, rotate the template.
                    if angle != 0:
                        (h, w) = tmpl_scaled.shape
                        # Calculate the center of the template for rotation.
                        center = (w // 2, h // 2)
                        # Create the rotation matrix.
                        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                        # Rotate the template.
                        tmpl_mod = cv2.warpAffine(tmpl_scaled, rot_matrix, (w, h))
                    else:
                        tmpl_mod = tmpl_scaled

                    # Get dimensions of the modified template.
                    tmpl_h, tmpl_w = tmpl_mod.shape

                    # Perform template matching using normalized cross-correlation.
                    result = cv2.matchTemplate(gray_frame, tmpl_mod, cv2.TM_CCOEFF_NORMED)
                    # Get the minimum and maximum matching scores and their locations.
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # If the maximum score exceeds the defined threshold, consider it a detection.
                    if max_val >= match_threshold:
                        # Draw a rectangle around the detection on the undistorted frame.
                        cv2.rectangle(undistorted, max_loc, (max_loc[0] + tmpl_w, max_loc[1] + tmpl_h), (0, 0, 255), 2)
                        # Put a label (the debris category) above the rectangle.
                        cv2.putText(undistorted, category, (max_loc[0], max_loc[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        # Print debug information regarding detection.
                        print(f"Detection: {category} | Score: {max_val:.2f} | Scale: {scale} | Angle: {angle}")

    # -------------------------------------------------------------------------
    # Display: Show the processed frame with all detection results.
    # -------------------------------------------------------------------------
    cv2.imshow("Debris Detection", undistorted)
    
    # Exit the loop if the user presses the 'q' key.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# =============================================================================
# Cleanup
# =============================================================================
# Release the video capture device and close any OpenCV windows.
cap.release()
cv2.destroyAllWindows()
