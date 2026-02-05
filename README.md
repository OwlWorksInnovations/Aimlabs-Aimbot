# Aimlabs Aimbot (NEW) (PIXEL BOT) (HUMAN MADE)
Changed to a color bot which is much faster and code is much better. Code is made only for spidershot. Gridshot or others will confuse it. Tracking might work. I plan on doing heavy research into vision models because using yolo is too slow and I think that training my own neural network from scratch will be better.

The project includes the following features
- Amazingly fast screen capture using dxcam (easily 144fps)
- Color detection
- Mouse move and click events using pywin32
- Auto scales capture window to game window size
- Debug window (toggleable)

# Get Started
### Install requirements
```
pip install -r requirements.txt
```

### Aimlabs Configuration (Required for color detection)
Import the `aimlabs_theme.json` file into Aimlabs by visual > import theme (Required for color detection)

#### Set up own colors (Optional, Its not working!!! Help!!!)
If the script is not working, you can try to set up your own colors by editing the `main_color_bot.py` file. The colors are defined in the `BALL_COLOR_LOWER` and `BALL_COLOR_UPPER` variables. The values are in BGR format. You can use the `get_color.py` script, hover over ball, to get the colors of the ball.

### Run the bot
```
python main_color_bot.py
```

# Aimlabs-Aimbot (OLD) (YOLO) (AI)
aimbot for aimlabs a game where you train your aim this is external made in python using yolov10
 
~~Link for best.pt model
https://www.mediafire.com/file/0ti9ll1ghgs8wqa/best.pt/file~~ (File is now in the repository)
