import cv2
import numpy as np
import dxcam
from ultralytics import YOLO
import time
import keyboard
import win32api, win32con

# Load the YOLO model
model = YOLO('best.pt')
model.to('cuda')

# Pre-configure YOLO for maximum speed
model.overrides['verbose'] = False  # Disable verbose output
model.overrides['device'] = 'cuda'

def move_mouse_relative(x, y):
    """Move mouse by relative amount"""
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)

def click_mouse():
    """Perform mouse click"""
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# Initialize dxcam for screen capturing with optimal settings
camera = dxcam.create(output_color="BGR")  # Output BGR directly to skip conversion

# Pre-allocate variables
locked_target = None
CLICK_THRESHOLD_SQ = 400  # 20^2 - avoid sqrt by comparing squared distances
LOCK_TOLERANCE_SQ = 2500  # 50^2 - tolerance for keeping lock on target

# Cache mouse position function
get_cursor_pos = win32api.GetCursorPos

# FPS tracking (optional - comment out for max performance)
fps_counter = 0
fps_start = time.perf_counter()

while True:
    # Exit check
    if keyboard.is_pressed('q'):
        print("Q pressed, exiting")
        break

    # Capture screenshot
    frame = camera.grab()
    if frame is None:
        continue

    # Get current mouse position once
    mouse_x, mouse_y = get_cursor_pos()

    # Run YOLO detection with optimized parameters
    # conf=0.5 filters low-confidence detections early
    # half=True uses FP16 for faster inference on GPU
    results = model.predict(frame, conf=0.5, half=True, verbose=False, stream=False)

    # Fast extraction of bounding boxes
    detected_targets = []
    boxes = results[0].boxes
    
    if len(boxes) > 0:
        # Vectorized operations for speed
        xyxy = boxes.xyxy.cpu().numpy().astype(np.int32)
        
        # Calculate centers in one vectorized operation
        centers_x = (xyxy[:, 0] + xyxy[:, 2]) >> 1  # Bit shift for faster division by 2
        centers_y = (xyxy[:, 1] + xyxy[:, 3]) >> 1
        
        detected_targets = list(zip(centers_x, centers_y))

    # Target locking logic - optimized
    target_x, target_y = None, None
    
    if locked_target and detected_targets:
        # Check if locked target still exists (with tolerance)
        locked_x, locked_y = locked_target
        min_dist_sq = LOCK_TOLERANCE_SQ
        best_match = None
        
        for cx, cy in detected_targets:
            dist_sq = (cx - locked_x) ** 2 + (cy - locked_y) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_match = (cx, cy)
        
        if best_match:
            locked_target = best_match
            target_x, target_y = best_match
        else:
            locked_target = None
    
    # Find nearest target if no lock
    if not locked_target and detected_targets:
        min_dist_sq = float('inf')
        
        for cx, cy in detected_targets:
            dist_sq = (cx - mouse_x) ** 2 + (cy - mouse_y) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                target_x, target_y = cx, cy
        
        locked_target = (target_x, target_y)
    
    # Move to target
    if target_x is not None:
        rel_x = target_x - mouse_x
        rel_y = target_y - mouse_y
        
        # Calculate squared distance for comparison (avoid sqrt)
        dist_sq = rel_x ** 2 + rel_y ** 2
        
        if dist_sq > CLICK_THRESHOLD_SQ:
            # Move mouse
            move_mouse_relative(rel_x, rel_y)
        else:
            # Click when close enough
            click_mouse()
            locked_target = None  # Release lock after clicking
    
    # FPS calculation (comment out for absolute max performance)
    fps_counter += 1
    if fps_counter % 30 == 0:  # Print every 30 frames
        fps_end = time.perf_counter()
        fps = 30 / (fps_end - fps_start)
        print(f"FPS: {fps:.1f}")
        fps_start = fps_end
