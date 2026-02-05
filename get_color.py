import pyautogui
import keyboard
import time

print("Press 'q' to quit")

while True:
    if keyboard.is_pressed('q'):
        break
    
    x, y = pyautogui.position()
    r, g, b = pyautogui.pixel(x, y)
    
    print(f"Position: ({x}, {y}), Color: RGB({r}, {g}, {b})")
    
    time.sleep(0.1)