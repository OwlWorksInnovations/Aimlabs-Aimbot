import dxcam
import cv2
from ultralytics import YOLO
import numpy as np

print("=== REAL-TIME SCREEN CAPTURE VIEWER WITH DETECTION ===")
print("This will show you what dxcam captures and what YOLO detects")
print("Press 'q' to quit, 's' to save current frame\n")

# Load model
print("Loading YOLO model...")
model = YOLO('best.pt')
model.to('cpu')
model.overrides['verbose'] = False

# Create camera
camera = dxcam.create(output_color="BGR")

print("✓ Starting viewer...")
print("  Green boxes = detected objects")
print("  Red dot = center of detection")
print("  Press 'q' to quit, 's' to save screenshot\n")

frame_count = 0

try:
    while True:
        # Capture frame
        frame = camera.grab()
        if frame is None:
            continue
        
        # Run detection
        results = model.predict(frame, conf=0.3, verbose=False)[0]
        boxes = results.boxes
        
        # Draw detections on frame
        display_frame = frame.copy()
        
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0].cpu().numpy())
            cls = int(box.cls[0].cpu().numpy())
            
            # Draw bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw center point
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            cv2.circle(display_frame, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Draw label
            label = f"Class {cls}: {conf:.2f}"
            cv2.putText(display_frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add info text
        info_text = f"Detected: {len(boxes)} objects | Frame: {frame_count} | Press 'q' to quit, 's' to save"
        cv2.putText(display_frame, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Resize if too large (for display)
        h, w = display_frame.shape[:2]
        if h > 1080 or w > 1920:
            scale = min(1080/h, 1920/w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            display_frame = cv2.resize(display_frame, (new_w, new_h))
        
        # Show frame
        cv2.imshow('Screen Capture + Detection', display_frame)
        
        # Handle keypresses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\nQuitting...")
            break
        elif key == ord('s'):
            filename = f"capture_frame_{frame_count}.png"
            cv2.imwrite(filename, display_frame)
            print(f"Saved: {filename}")
        
        frame_count += 1
        
except KeyboardInterrupt:
    print("\nInterrupted by user")
finally:
    cv2.destroyAllWindows()

print("Viewer closed.")
