"""
config/settings.py
===================
Centralized configuration for the AI Virtual Mouse Control System.

Keeping every tunable parameter in a single module makes the application
easy to calibrate for different cameras, screen resolutions, and user
preferences without touching the core logic in `src/`.
"""

# ---------------------------------------------------------------------------
# Camera Configuration
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0                # Default webcam device index
FRAME_WIDTH = 640                # Capture frame width (pixels)
FRAME_HEIGHT = 480               # Capture frame height (pixels)
FLIP_CAMERA = True               # Mirror the webcam feed for a natural UX

# ---------------------------------------------------------------------------
# MediaPipe Hand Detection Configuration
# ---------------------------------------------------------------------------
MAX_NUM_HANDS = 1                 # Track a single hand for stable control
MIN_DETECTION_CONFIDENCE = 0.75   # Minimum confidence to detect a hand
MIN_TRACKING_CONFIDENCE = 0.75    # Minimum confidence to keep tracking a hand
MODEL_COMPLEXITY = 1              # 0 = lite, 1 = full (accuracy/speed trade-off)

# ---------------------------------------------------------------------------
# Cursor Mapping & Smoothing
# ---------------------------------------------------------------------------
# The active control region inside the webcam frame. Reducing this margin
# lets the user reach every corner of the screen without stretching their
# hand to the physical edges of the camera view.
FRAME_REDUCTION = 100

# Exponential Moving Average smoothing factor (0 < value <= 1).
# Lower values = smoother but laggier cursor. Higher values = snappier
# but shakier cursor. Tune this to taste.
SMOOTHING_FACTOR = 0.35

# Overall sensitivity multiplier applied after coordinate mapping.
# Values > 1.0 make the cursor travel faster than the physical hand.
CURSOR_SENSITIVITY = 1.0

# ---------------------------------------------------------------------------
# Gesture Recognition Thresholds
# ---------------------------------------------------------------------------
CLICK_DISTANCE_THRESHOLD = 35     # px, fingertip distance to trigger a click
PINCH_DISTANCE_THRESHOLD = 30     # px, thumb-index distance for a pinch
FIST_CURL_THRESHOLD = 0.65        # Reserved: ratio for advanced curl checks

CLICK_COOLDOWN = 0.4              # seconds between two accepted clicks
DOUBLE_CLICK_COOLDOWN = 0.6       # seconds between two accepted double clicks
GESTURE_HOLD_FRAMES = 4           # consecutive frames required before a
                                   # gesture is accepted (debounce, prevents
                                   # accidental clicks from momentary jitter)

SCROLL_SENSITIVITY = 40           # scroll "clicks" multiplier
SCROLL_DEAD_ZONE = 8              # px, ignore small vertical jitter

# ---------------------------------------------------------------------------
# UI / Overlay Configuration
# ---------------------------------------------------------------------------
SHOW_FPS = True
SHOW_LANDMARKS = True
SHOW_STATUS_PANEL = True

WINDOW_NAME = "AI Virtual Mouse Control System"

# Colors are defined in BGR (OpenCV convention)
COLOR_PRIMARY = (255, 0, 200)
COLOR_SUCCESS = (0, 220, 0)
COLOR_WARNING = (0, 165, 255)
COLOR_ERROR = (0, 0, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_PANEL_BG = (30, 30, 30)

# ---------------------------------------------------------------------------
# Application Behaviour
# ---------------------------------------------------------------------------
EXIT_KEY = "q"                    # Keyboard shortcut to quit safely
PYAUTOGUI_FAILSAFE = True         # Keep PyAutoGUI's corner failsafe enabled
PYAUTOGUI_PAUSE = 0.0             # No artificial delay between PyAutoGUI calls
