"""
src/mouse_controller.py
=========================
Translates gesture events into actual operating-system mouse actions
via PyAutoGUI, with coordinate mapping and exponential smoothing so
the cursor moves fluidly instead of jumping between raw, noisy hand
coordinates.
"""

from typing import Tuple

import pyautogui

from config import settings
from src.utils import map_range, clamp


class MouseController:
    """Owns all interaction with the operating system's mouse cursor."""

    def __init__(self, frame_width: int, frame_height: int) -> None:
        pyautogui.FAILSAFE = settings.PYAUTOGUI_FAILSAFE
        pyautogui.PAUSE = settings.PYAUTOGUI_PAUSE

        self.screen_width, self.screen_height = pyautogui.size()
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Previous smoothed cursor position, seeded from the current
        # OS cursor position so the very first movement isn't a jump.
        self._prev_x, self._prev_y = pyautogui.position()
        self._is_dragging = False

    # ------------------------------------------------------------------
    # Coordinate mapping
    # ------------------------------------------------------------------
    def _map_to_screen(self, x: int, y: int) -> Tuple[float, float]:
        """
        Maps a coordinate from the reduced webcam control region
        (see settings.FRAME_REDUCTION) to full screen coordinates.
        """
        reduction = settings.FRAME_REDUCTION

        screen_x = map_range(
            x, reduction, self.frame_width - reduction, 0, self.screen_width
        )
        screen_y = map_range(
            y, reduction, self.frame_height - reduction, 0, self.screen_height
        )

        screen_x *= settings.CURSOR_SENSITIVITY
        screen_y *= settings.CURSOR_SENSITIVITY

        screen_x = clamp(screen_x, 0, self.screen_width - 1)
        screen_y = clamp(screen_y, 0, self.screen_height - 1)

        return screen_x, screen_y

    def _smooth(self, target_x: float, target_y: float) -> Tuple[float, float]:
        """Exponential moving average smoothing to reduce cursor jitter."""
        factor = settings.SMOOTHING_FACTOR
        smoothed_x = self._prev_x + (target_x - self._prev_x) * factor
        smoothed_y = self._prev_y + (target_y - self._prev_y) * factor

        self._prev_x, self._prev_y = smoothed_x, smoothed_y
        return smoothed_x, smoothed_y

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------
    def move(self, x: int, y: int) -> None:
        """Smoothly move the OS cursor towards the mapped hand position."""
        target_x, target_y = self._map_to_screen(x, y)
        smooth_x, smooth_y = self._smooth(target_x, target_y)
        pyautogui.moveTo(smooth_x, smooth_y)

    def left_click(self) -> None:
        pyautogui.click(button="left")

    def right_click(self) -> None:
        pyautogui.click(button="right")

    def double_click(self) -> None:
        pyautogui.doubleClick()

    def start_drag(self, x: int, y: int) -> None:
        """Press and hold the left mouse button at the mapped position."""
        if not self._is_dragging:
            target_x, target_y = self._map_to_screen(x, y)
            pyautogui.mouseDown(target_x, target_y)
            self._is_dragging = True

    def drag_to(self, x: int, y: int) -> None:
        """Move the cursor while the left mouse button is held down."""
        if self._is_dragging:
            self.move(x, y)

    def end_drag(self) -> None:
        """Release the left mouse button, ending the drag operation."""
        if self._is_dragging:
            pyautogui.mouseUp()
            self._is_dragging = False

    def scroll(self, direction: str) -> None:
        """Scroll the active window. direction must be 'up' or 'down'."""
        amount = settings.SCROLL_SENSITIVITY
        pyautogui.scroll(amount if direction == "up" else -amount)
