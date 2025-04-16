import cv2
import numpy as np
import glob
import time

# =============================================================================
# Load Calibration Data
# =============================================================================

# Load the previously computed camera matrix and distortion coefficients,
# which are used to undistort the raw video frames.
camera_matrix = np.load("camera_matrix.npy")
distortion_coeffs = np.load("distortion_coeffs.npy")

# =============================================================================
# Template Loading with Glob
# =============================================================================

# Define the directories (using glob patterns) for each debris category.
# Here we assume that you have stored multiple template images for each
# category (CubeSat, Minotaur, and Starlink) in separate folders.
template_dirs = {
    "CubeSat": "templates/CubeSat/*.png",
    "Minotaur": "templates/Minotaur/*.png",
    "Starlink": "templates/Starlink/*.png"
}

# Create a dictionary to store the loaded templates for each category.
templates = {}
# Loop through each category and corresponding glob pattern.
for category, pattern in template_dirs.items():
    # Get the list of image file paths that match the pattern.
    paths = glob.glob(pattern)
    loaded = []  # List to hold the loaded template images for the current category.
    # Loop over each file path.
    for path in paths:
        # Load the image as grayscale since template matching is performed on single channel images.
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            loaded.append(img)
        else:
            print(f"Warning: Could not load template image {path}")
    # Store the list of loaded templates in the dictionary.
    templates[category] = loaded
    print(f"Loaded {len(loaded)} templates for {category}")

# Set a matching threshold for template matching.
# This value may require tuning depending on your templates and expected matching quality.
match_threshold = 0.7

# =============================================================================
# Open Live Video Feed
# =============================================================================

# Open the default camera (index 0). Adjust the index if you have multiple cameras.
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# =============================================================================
# Main Loop: Process each frame from the video feed
# =============================================================================

while True:
    # Read a frame from the live video feed.
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # -----------------------------------------------------------------------------
    # Undistort the captured frame using the calibration data.
    # This removes lens distortion for more accurate detection.
    # -----------------------------------------------------------------------------
    undistorted = cv2.undistort(frame, camera_matrix, distortion_coeffs)
    
    # Convert the undistorted frame to grayscale since template matching
    # works on single channel images.
    gray_frame = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

    # -----------------------------------------------------------------------------
    # Template Matching: Loop over each category and its templates.
    # -----------------------------------------------------------------------------
    for category, template_list in templates.items():
        for tmpl in template_list:
            # Perform template matching using the normalized cross-correlation method.
            # This returns a result map where each pixel value represents the match quality.
            result = cv2.matchTemplate(gray_frame, tmpl, cv2.TM_CCOEFF_NORMED)
            # Get the locations (x, y) where the matching score meets or exceeds the threshold.
            loc = np.where(result >= match_threshold)
            # Loop over the list of matching locations.
            for pt in zip(*loc[::-1]):  # Reverse the order to get (x, y) coordinates.
                # Get the template's width and height to draw the bounding box.
                h, w = tmpl.shape
                # Draw a rectangle on the undistorted frame around the detected match.
                cv2.rectangle(undistorted, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
                # Put a label (the category) just above the rectangle.
                cv2.putText(undistorted, category, (pt[0], pt[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # -----------------------------------------------------------------------------
    # Display: Show the processed frame with detection results.
    # -----------------------------------------------------------------------------
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
