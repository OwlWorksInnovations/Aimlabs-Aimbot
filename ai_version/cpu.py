import numpy as np
import dxcam
from ultralytics import YOLO
import keyboard
import win32api, win32con
import time

# ===== TUNING PARAMETERS - ADJUST THESE FOR YOUR PREFERENCE =====
CLICK_THRESHOLD = 20           # pixels - click when within this distance (lower = more accurate)
LOCK_TOLERANCE = 50           # pixels - keep lock if target moves within this range
CONF_THRESHOLD = 0.5          # detection confidence (0.1-0.9, lower = more detections)
MOVEMENT_SMOOTHING = 0.5      # 0.1 = very smooth/slow, 1.0 = instant/no smoothing

# TUNING GUIDE:
# - If mouse overshoots: decrease MOVEMENT_SMOOTHING to 0.7-0.8
# - If mouse is too slow: increase MOVEMENT_SMOOTHING to 1.0
# - If clicking too early: decrease CLICK_THRESHOLD to 3-5
# - If not clicking: increase CLICK_THRESHOLD to 15-20
# =================================================================

# Load and configure YOLO model
model = YOLO('best.pt')
model.to('cpu')
model.overrides['verbose'] = False
model.model.eval()

print("CPU Targeting Bot (Optimized)")
print(f"Settings: Smoothing={MOVEMENT_SMOOTHING}, Click threshold={CLICK_THRESHOLD}px, Confidence={CONF_THRESHOLD}")
print("Press 'q' to exit")

# Initialize dxcam
camera = dxcam.create(output_color="BGR", max_buffer_len=1)

# Pre-cache functions
get_cursor_pos = win32api.GetCursorPos
mouse_event = win32api.mouse_event
MOVE = win32con.MOUSEEVENTF_MOVE
CLICK = win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP

# State
locked_target = None

while True:
    if keyboard.is_pressed('q'):
        break

    frame = camera.grab()
    if frame is None:
        continue

    mouse_x, mouse_y = get_cursor_pos()

    # YOLO inference
    results = model.predict(
        frame,
        conf=CONF_THRESHOLD,
        verbose=False,
        agnostic_nms=True,
        max_det=10,
        half=False
    )[0]

    boxes = results.boxes
    
    if len(boxes) == 0:
        locked_target = None
        continue

    # Vectorized center calculation
    xyxy = boxes.xyxy.cpu().numpy()
    centers = ((xyxy[:, [0, 2]].sum(axis=1) / 2).astype(np.int32),
               (xyxy[:, [1, 3]].sum(axis=1) / 2).astype(np.int32))
    
    target_x, target_y = None, None

    # Target selection
    if locked_target:
        locked_x, locked_y = locked_target
        dx = centers[0] - locked_x
        dy = centers[1] - locked_y
        dist_sq = dx * dx + dy * dy
        
        if len(dist_sq) > 0:
            min_idx = dist_sq.argmin()
            if dist_sq[min_idx] < (LOCK_TOLERANCE * LOCK_TOLERANCE):
                target_x, target_y = centers[0][min_idx], centers[1][min_idx]
                locked_target = (target_x, target_y)
            else:
                locked_target = None

    if not locked_target:
        dx = centers[0] - mouse_x
        dy = centers[1] - mouse_y
        dist_sq = dx * dx + dy * dy
        
        min_idx = dist_sq.argmin()
        target_x, target_y = centers[0][min_idx], centers[1][min_idx]
        locked_target = (target_x, target_y)

    # Execute action
    if target_x is not None:
        rel_x = target_x - mouse_x
        rel_y = target_y - mouse_y
        distance_sq = rel_x * rel_x + rel_y * rel_y
        
        if distance_sq > (CLICK_THRESHOLD * CLICK_THRESHOLD):
            # Apply smoothing
            move_x = int(rel_x * MOVEMENT_SMOOTHING)
            move_y = int(rel_y * MOVEMENT_SMOOTHING)
            
            if move_x != 0 or move_y != 0:
                mouse_event(MOVE, move_x, move_y, 0, 0)
        else:
            # Click when close enough
            mouse_event(CLICK, 0, 0, 0, 0)
            locked_target = None
