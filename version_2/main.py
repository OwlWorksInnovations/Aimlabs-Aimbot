import cv2
import numpy as np
import dxcam
from ultralytics import YOLO
import time
import keyboard
import win32api, win32con
import math

# Load the YOLO model
model = YOLO('best.pt')  # Replace with your model path

model.to('cuda')

def move_mouse_relative(x, y):
    # Move mouse by a relative amount
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Initialize dxcam for screen capturing
camera = dxcam.create()

locked_target = None

while True:
    # Check if the 'q' key is pressed to exit the script
    if keyboard.is_pressed('q'):
        print("Q pressed, exiting")
        break

    # Start the time measurement for FPS calculation
    start_time = time.time()

    # Capture screenshot
    frame = camera.grab()

    # Ensure the frame is valid before proceeding
    if frame is None:
        print("Failed to grab frame, skipping this iteration.")
        continue

    # Convert the frame to a valid numpy array with the correct dtype (uint8)
    frame = np.array(frame, dtype=np.uint8)

    # Convert frame from BGR to RGB for YOLO
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get screen dimensions from the frame shape
    screen_height, screen_width, _ = frame.shape

    # Run YOLO detection
    results = model(frame)

    # Get the current mouse position
    mouse_x, mouse_y = win32api.GetCursorPos()

    # Variables to track the closest object
    closest_distance = float('inf')
    closest_center_x = None
    closest_center_y = None

    # Process the results
    detected_targets = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Get the bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Calculate center of the bounding box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Ensure the coordinates are within screen bounds
            center_x = max(0, min(center_x, screen_width - 1))
            center_y = max(0, min(center_y, screen_height - 1))

            detected_targets.append((center_x, center_y))

    # Check if the locked target still exists
    if locked_target:
        if locked_target in detected_targets:
            closest_center_x, closest_center_y = locked_target
        else:
            locked_target = None

    # If no locked target, find the nearest one
    if not locked_target:
        for center_x, center_y in detected_targets:
            distance = calculate_distance(mouse_x, mouse_y, center_x, center_y)
            if distance < closest_distance:
                closest_distance = distance
                closest_center_x = center_x
                closest_center_y = center_y
        
        if closest_center_x is not None and closest_center_y is not None:
            locked_target = (closest_center_x, closest_center_y)

    # Move to the locked target if found
    if locked_target:
        closest_center_x, closest_center_y = locked_target
        # Calculate how far the mouse needs to move
        rel_x = closest_center_x - mouse_x
        rel_y = closest_center_y - mouse_y

        # Move the mouse in small steps toward the target
        move_mouse_relative(int(rel_x), int(rel_y))
        # Update the mouse's position after moving
        mouse_x, mouse_y = win32api.GetCursorPos()

        # Recalculate distance to the target
        distance_to_target = calculate_distance(mouse_x, mouse_y, closest_center_x, closest_center_y)

        # Only click when the mouse is close enough to the target (within 10 pixels)
        if distance_to_target < 20:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            print(f"Mouse clicked at: {mouse_x}, {mouse_y} (distance to target: {distance_to_target})")
            locked_target = None  # Release the lock after clicking
    
    # Calculate the time taken for the frame and compute FPS
    end_time = time.time()
    fps = 1 / (end_time - start_time)

    # Print FPS to console
    print(f"FPS: {fps:.2f}")
