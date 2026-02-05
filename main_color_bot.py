import dxcam
import cv2
import numpy as np
import keyboard
import time
import win32gui, win32api, win32con
import pyautogui

# Ball color range (BGR)
# Created from RGB: (17, 210, 214), (18, 213, 217), (18, 208, 213), (19, 215, 218)
BALL_COLOR_LOWER = (213, 208, 17)
BALL_COLOR_UPPER = (218, 215, 19)

# GLOBAL VARIABLES
DEBUG_MODE = True

# Set up dxcam
def get_window_rect(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        # DXcam requires even numbers for all coordinates and width/height
        left = max(0, rect[0] if rect[0] % 2 == 0 else rect[0] + 1)
        top = max(0, rect[1] if rect[1] % 2 == 0 else rect[1] + 1)
        right = min(1920, rect[2] if rect[2] % 2 == 0 else rect[2] - 1)
        bottom = min(1080, rect[3] if rect[3] % 2 == 0 else rect[3] - 1)

        if right > left and bottom > top:
            return (left, top, right, bottom)
    return None

target_title = "aimlab_tb"
rect = get_window_rect(target_title)

cam = dxcam.create(output_color="BGR", max_buffer_len=1)

if rect:
    print(f"Found '{target_title}', capturing region: {rect}")
    cam.start(region=rect, target_fps=0)
else:
    print(f"Window '{target_title}' not found.")
    exit()

if DEBUG_MODE:
    window_name = "Aimlabs"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

print("Press 'q' to quit")

# Move mouse function (Full screen applications require relative movement)
def move_mouse(x, y):
    center_x = (rect[2] - rect[0]) // 2
    center_y = (rect[3] - rect[1]) // 2
    
    rel_x = x - center_x
    rel_y = y - center_y
    
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(rel_x), int(rel_y), 0, 0)

    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# Main loop
while True:
    if keyboard.is_pressed('q'):
        break

    frame = cam.get_latest_frame()
    if frame is not None:
        mask = cv2.inRange(frame, BALL_COLOR_LOWER, BALL_COLOR_UPPER)

        y_coords, x_coords = np.where(mask > 0)

        if len(x_coords) > 0:
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))
            
            move_mouse(center_x, center_y)  

            if DEBUG_MODE:
                cv2.drawMarker(frame, (center_x, center_y), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

        if DEBUG_MODE:
            cv2.imshow(window_name, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop()
cv2.destroyAllWindows()
print("Capture stopped.")