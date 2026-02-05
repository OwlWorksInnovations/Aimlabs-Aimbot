import dxcam
import cv2
import numpy as np

print("=== DXCAM SCREEN CAPTURE CONFIGURATION ===\n")

# List available monitors
print("Available monitors:")
for i in range(10):  # Check up to 10 monitors
    try:
        cam = dxcam.create(device_idx=i, output_idx=i)
        if cam:
            print(f"  Monitor {i}: Available")
            cam = None
    except:
        break

print("\n--- OPTION 1: Capture Full Screen ---")
camera = dxcam.create(output_color="BGR")

# Capture a frame
frame = camera.grab()
if frame is not None:
    h, w = frame.shape[:2]
    print(f"Full screen capture: {w}x{h} pixels")
    
    # Save the captured frame so you can see what's being captured
    cv2.imwrite("captured_screen.png", frame)
    print("✓ Saved full screen capture to: captured_screen.png")
    print("  Open this file to see what dxcam is capturing!\n")
else:
    print("✗ Failed to capture screen\n")

print("--- OPTION 2: Capture Specific Region ---")
print("You can capture just a portion of the screen for better performance.")
print("This is useful if your game is in a window or specific area.\n")

print("Example configurations:")
print("1. Center 640x480 region:")
print("   region = (center_x - 320, center_y - 240, center_x + 320, center_y + 240)")
print("\n2. Top-left 800x600:")
print("   region = (0, 0, 800, 600)")
print("\n3. Custom region:")
print("   region = (left, top, right, bottom)")

print("\n--- Testing Center Region Capture ---")
if frame is not None:
    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2
    
    # Capture center 640x640 region
    region = (center_x - 320, center_y - 320, center_x + 320, center_y + 320)
    print(f"Capturing center region: {region}")
    
    camera_region = dxcam.create(output_color="BGR", region=region)
    frame_region = camera_region.grab()
    
    if frame_region is not None:
        cv2.imwrite("captured_region.png", frame_region)
        print(f"✓ Saved region capture ({frame_region.shape[1]}x{frame_region.shape[0]}) to: captured_region.png\n")

print("--- OPTION 3: Target FPS Configuration ---")
print("You can set a target FPS for more consistent performance:")
print("  camera = dxcam.create(output_color='BGR', target_fps=60)")
print("  # This will capture at max 60 FPS\n")

print("--- HOW TO USE THIS IN YOUR SCRIPT ---")
print("""
# Option A: Full screen (default)
camera = dxcam.create(output_color="BGR")

# Option B: Specific monitor (if you have multiple)
camera = dxcam.create(device_idx=0, output_idx=0, output_color="BGR")

# Option C: Specific region (x1, y1, x2, y2)
# Example: Center 640x640 area
screen_width = 1920  # Your screen width
screen_height = 1080  # Your screen height
center_x, center_y = screen_width // 2, screen_height // 2
region = (center_x - 320, center_y - 320, center_x + 320, center_y + 320)
camera = dxcam.create(output_color="BGR", region=region)

# Option D: With target FPS
camera = dxcam.create(output_color="BGR", target_fps=60)
""")

print("\n=== IMPORTANT NOTES ===")
print("1. dxcam captures the ENTIRE PRIMARY MONITOR by default")
print("2. If your game is on a SECONDARY monitor, use device_idx and output_idx")
print("3. If your game is WINDOWED, consider using a region capture")
print("4. Check 'captured_screen.png' to verify what's being captured")
print("5. Make sure your game/targets are VISIBLE on screen when running the bot")
print("\n=== TROUBLESHOOTING ===")
print("If no objects detected:")
print("- Open captured_screen.png - do you see your targets?")
print("- Is your game fullscreen or windowed?")
print("- Is your game on the primary monitor?")
print("- Is the confidence threshold too high? (try lowering to 0.2-0.3)")
print("- Is your YOLO model trained on the right type of targets?")
