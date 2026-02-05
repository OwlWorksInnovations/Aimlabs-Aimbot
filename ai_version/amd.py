import numpy as np
import dxcam
import keyboard
import win32api, win32con
import cv2
import time

# ===== TUNING PARAMETERS =====
CLICK_THRESHOLD = 40           # pixels - click when within this distance
LOCK_TOLERANCE = 50           # pixels
CONF_THRESHOLD = 0.01         # Confidence threshold for detection
MOVEMENT_SMOOTHING = 0.9      # 0.5 = no overshoot
CLICK_COOLDOWN = 0.1          # seconds - prevents double clicking
MAX_TARGET_DISTANCE = 800     # pixels - ignore targets further than this from mouse
MODEL_INPUT_SIZE = 640
# =================================

# ONNX Runtime setup for AMD GPU
try:
    import onnxruntime as ort
    
    providers = ort.get_available_providers()
    print(f"Available ONNX providers: {providers}")
    
    if 'DmlExecutionProvider' in providers:
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        model = ort.InferenceSession(
            'best.onnx',
            sess_options=session_options,
            providers=['DmlExecutionProvider']
        )
        print("✓ Using ONNX Runtime with DirectML (AMD GPU)")
    else:
        print("DirectML not available, using CPU")
        model = ort.InferenceSession('best.onnx', providers=['CPUExecutionProvider'])
        
except Exception as e:
    print(f"Error: {e}")
    print("\nRun: py -3.11 export_to_onnx.py first")
    print("Then: pip install onnxruntime-directml")
    exit(1)

input_name = model.get_inputs()[0].name
print(f"Model loaded: {input_name}")
print(f"Smoothing={MOVEMENT_SMOOTHING}, Click cooldown={CLICK_COOLDOWN}s")
print("Press 'q' to exit\n")

# Initialize dxcam
camera = dxcam.create(output_color="BGR", max_buffer_len=1)

# Pre-cache functions
get_cursor_pos = win32api.GetCursorPos
mouse_event = win32api.mouse_event
MOVE = win32con.MOUSEEVENTF_MOVE
CLICK = win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP

# State
locked_target = None
last_click_time = 0
frame_count = 0
fps_start = time.perf_counter()
debug_printed = False

def preprocess_frame(frame):
    img = cv2.resize(frame, (MODEL_INPUT_SIZE, MODEL_INPUT_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = img.transpose(2, 0, 1)
    return np.expand_dims(img, axis=0)

def postprocess_output(output, conf_threshold=0.5, debug=False):
    if len(output.shape) == 3:
        output = output[0]  
    
    boxes = []
    for detection in output:
        x1, y1, x2, y2, conf, cls = detection[0:6]
        if conf > conf_threshold:
            boxes.append([int(x1), int(y1), int(x2), int(y2)])
    
    return np.array(boxes) if len(boxes) > 0 else None

while True:
    if keyboard.is_pressed('q'):
        break

    frame = camera.grab()
    if frame is None:
        continue

    screen_h, screen_w = frame.shape[:2]
    mouse_x, mouse_y = get_cursor_pos()
    current_time = time.perf_counter()

    # Run inference
    input_tensor = preprocess_frame(frame)
    outputs = model.run(None, {input_name: input_tensor})
    
    # Get detections
    boxes = postprocess_output(outputs[0], CONF_THRESHOLD, debug=(not debug_printed))
    debug_printed = True

    # FIX: If no boxes are found, reset everything and SKIP loop immediately
    if boxes is None or len(boxes) == 0:
        locked_target = None
        if frame_count % 60 == 0:
            print("No targets detected - Staying still.")
        frame_count += 1
        continue

    # Scale boxes to screen size
    scale_x = screen_w / MODEL_INPUT_SIZE
    scale_y = screen_h / MODEL_INPUT_SIZE
    
    # Calculate centers for all detections
    # We do this before target selection to ensure we have valid points
    scaled_boxes = boxes.copy()
    scaled_boxes[:, [0, 2]] = (scaled_boxes[:, [0, 2]] * scale_x).astype(np.int32)
    scaled_boxes[:, [1, 3]] = (scaled_boxes[:, [1, 3]] * scale_y).astype(np.int32)
    
    c_x = ((scaled_boxes[:, 0] + scaled_boxes[:, 2]) / 2).astype(np.int32)
    c_y = ((scaled_boxes[:, 1] + scaled_boxes[:, 3]) / 2).astype(np.int32)
    
    target_x, target_y = None, None

    # Target selection logic
    if locked_target:
        lx, ly = locked_target
        dx = c_x - lx
        dy = c_y - ly
        dist_sq = dx*dx + dy*dy
        min_idx = np.argmin(dist_sq)
        
        if dist_sq[min_idx] < (LOCK_TOLERANCE * LOCK_TOLERANCE):
            target_x, target_y = c_x[min_idx], c_y[min_idx]
        else:
            locked_target = None # Lost lock

    if not locked_target:
        dx = c_x - mouse_x
        dy = c_y - mouse_y
        dist_sq = dx*dx + dy*dy
        
        max_dist_sq = MAX_TARGET_DISTANCE * MAX_TARGET_DISTANCE
        valid_mask = dist_sq < max_dist_sq
        
        if np.any(valid_mask):
            # Only look at targets within range
            valid_indices = np.where(valid_mask)[0]
            closest_idx = valid_indices[np.argmin(dist_sq[valid_indices])]
            target_x, target_y = c_x[closest_idx], c_y[closest_idx]
            locked_target = (target_x, target_y)

    # FINAL SAFETY: If we failed to pick a target despite having boxes (e.g. all out of range)
    if target_x is None or target_y is None:
        locked_target = None
        continue

    # Execute movement/click action
    rel_x = target_x - mouse_x
    rel_y = target_y - mouse_y
    dist_to_target_sq = rel_x**2 + rel_y**2
    
    if dist_to_target_sq > (CLICK_THRESHOLD * CLICK_THRESHOLD):
        # Move towards target
        move_x = int(rel_x * MOVEMENT_SMOOTHING)
        move_y = int(rel_y * MOVEMENT_SMOOTHING)
        
        # Only move if there is a meaningful distance to travel
        if move_x != 0 or move_y != 0:
            mouse_event(MOVE, move_x, move_y, 0, 0)
    else:
        # Click logic
        if current_time - last_click_time >= CLICK_COOLDOWN:
            mouse_event(CLICK, 0, 0, 0, 0)
            last_click_time = current_time
            locked_target = None  # Reset after shot to find next spider
            print("✓ Shot fired!")
    
    # FPS counter
    frame_count += 1
    if frame_count % 30 == 0:
        fps_end = time.perf_counter()
        fps = 30 / (fps_end - fps_start)
        print(f"FPS: {fps:.1f} | Detections: {len(boxes)}")
        fps_start = fps_end