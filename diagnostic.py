import dxcam
from ultralytics import YOLO
import keyboard
import time

print("=== DIAGNOSTIC SCRIPT ===")
print("This will help us figure out what's wrong\n")

# Test 1: Load model
print("Test 1: Loading YOLO model...")
try:
    model = YOLO('best.pt')
    model.to('cpu')
    model.overrides['verbose'] = False
    print("✓ Model loaded successfully\n")
except Exception as e:
    print(f"✗ Model loading failed: {e}\n")
    exit(1)

# Test 2: Screen capture
print("Test 2: Testing screen capture...")
try:
    camera = dxcam.create(output_color="BGR", max_buffer_len=1)
    frame = camera.grab()
    if frame is not None:
        print(f"✓ Screen capture working! Frame shape: {frame.shape}\n")
    else:
        print("✗ Screen capture returned None\n")
        exit(1)
except Exception as e:
    print(f"✗ Screen capture failed: {e}\n")
    exit(1)

# Test 3: Run detection
print("Test 3: Running YOLO detection on captured frame...")
print("Looking for targets... (this may take a few seconds)")
try:
    results = model.predict(frame, conf=0.3, verbose=False)[0]
    boxes = results.boxes
    print(f"✓ Detection ran successfully!")
    print(f"  Found {len(boxes)} objects\n")
    
    if len(boxes) > 0:
        print("Detected objects:")
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls = int(box.cls[0].cpu().numpy())
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            print(f"  Object {i+1}: Center=({center_x}, {center_y}), Confidence={conf:.2f}, Class={cls}")
    else:
        print("⚠ No objects detected!")
        print("  This could mean:")
        print("  - Your model isn't detecting anything in the current screen")
        print("  - The confidence threshold is too high")
        print("  - You need to point your screen at targets")
    print()
    
except Exception as e:
    print(f"✗ Detection failed: {e}\n")
    exit(1)

# Test 4: Continuous detection test
print("Test 4: Running continuous detection...")
print("Press 'q' to stop\n")

frame_count = 0
detection_count = 0
start_time = time.time()

try:
    while frame_count < 50:  # Run for 50 frames
        if keyboard.is_pressed('q'):
            print("\nStopped by user")
            break
            
        frame = camera.grab()
        if frame is None:
            continue
            
        results = model.predict(frame, conf=0.3, verbose=False)[0]
        boxes = results.boxes
        
        frame_count += 1
        if len(boxes) > 0:
            detection_count += 1
            print(f"Frame {frame_count}: Detected {len(boxes)} targets")
        else:
            print(f"Frame {frame_count}: No targets detected")
        
        time.sleep(0.1)  # Small delay to not spam
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed
    detection_rate = (detection_count / frame_count) * 100
    
    print(f"\n=== RESULTS ===")
    print(f"Processed {frame_count} frames in {elapsed:.1f}s")
    print(f"Average FPS: {fps:.1f}")
    print(f"Detection rate: {detection_rate:.1f}% ({detection_count}/{frame_count} frames had detections)")
    
    if detection_rate < 10:
        print("\n⚠ WARNING: Very low detection rate!")
        print("  Possible issues:")
        print("  - Your model might not be trained for what's on screen")
        print("  - Confidence threshold might be too high")
        print("  - Make sure there are targets visible on screen")
    
except KeyboardInterrupt:
    print("\nInterrupted by user")
except Exception as e:
    print(f"\n✗ Continuous test failed: {e}")

print("\n=== DIAGNOSTIC COMPLETE ===")
