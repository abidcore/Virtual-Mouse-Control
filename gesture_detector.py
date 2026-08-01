"""
src/gesture_detector.py
========================
Translates raw hand-landmark data into discrete, high-level gestures
that the MouseController can act on.

Recognized gestures
--------------------
- MOVE           : index finger up only -> moves the cursor
- LEFT_CLICK     : index + middle up, tips pinched together
- RIGHT_CLICK    : index + middle + ring up, middle/ring tips pinched
- DOUBLE_CLICK   : thumb + index pinch, other fingers curled
- DRAG           : closed fist held while moving -> press-drag-release
- SCROLL_UP/DOWN : open palm without thumb, vertical hand movement

Design notes
------------
- Gesture recognition is debounced: a gesture must be observed for
  several consecutive frames (settings.GESTURE_HOLD_FRAMES) before it
  is accepted. This filters out momentary misreads and prevents
  accidental clicks caused by natural hand jitter.
- Click-type gestures also respect a cooldown timer so a single
  sustained pinch doesn't fire dozens of clicks per second.
"""

import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

from config import settings
from src.hand_tracker import HandTracker


class Gesture(Enum):
    """All gestures the system can recognize."""
    NONE = auto()
    MOVE = auto()
    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    DOUBLE_CLICK = auto()
    DRAG_START = auto()
    DRAG_HOLD = auto()
    DRAG_END = auto()
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()


@dataclass
class GestureResult:
    """Container describing the gesture detected on the current frame."""
    gesture: Gesture
    cursor_point: Tuple[int, int] = (0, 0)   # index fingertip, used for MOVE/DRAG
    raw_label: str = "NONE"                  # human-readable, shown on the HUD


class GestureDetector:
    """
    Stateful gesture recognizer. Holds a small amount of history
    (previous gesture streak, cooldown timers, drag state) between frames.
    """

    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    def __init__(self, tracker: HandTracker) -> None:
        self._tracker = tracker

        self._candidate_gesture = Gesture.NONE
        self._candidate_streak = 0

        self._last_click_time = 0.0
        self._last_double_click_time = 0.0

        self._is_dragging = False
        self._previous_scroll_y = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detect(self, landmark_list: List[Tuple[int, int, int]]) -> GestureResult:
        """Main entry point: returns the gesture detected on this frame."""
        if not landmark_list:
            self._reset_streak()
            self._previous_scroll_y = None
            if self._is_dragging:
                self._is_dragging = False
                return GestureResult(Gesture.DRAG_END, raw_label="DRAG_END")
            return GestureResult(Gesture.NONE, raw_label="NO HAND")

        fingers = self._tracker.fingers_up(landmark_list)
        thumb, index, middle, ring, pinky = fingers
        index_point = self._point_of(landmark_list, self.INDEX_TIP)

        # --- Gesture checks are ordered from most to least specific -----

        # 1) Closed fist -> Drag (press, move, release)
        if fingers == [0, 0, 0, 0, 0]:
            return self._handle_drag(index_point)

        # If a drag was active and the fist just opened, end the drag.
        if self._is_dragging:
            self._is_dragging = False
            return GestureResult(Gesture.DRAG_END, index_point, "DRAG_END")

        # 2) Open palm without thumb -> Scroll mode
        if fingers == [0, 1, 1, 1, 1]:
            return self._handle_scroll(landmark_list)
        self._previous_scroll_y = None

        # 3) Thumb + Index pinch, other fingers curled -> Double click
        if thumb and index and not middle and not ring and not pinky:
            distance = self._tracker.find_distance(
                self.THUMB_TIP, self.INDEX_TIP, landmark_list
            )
            if distance is not None and distance < settings.PINCH_DISTANCE_THRESHOLD:
                return self._handle_double_click(index_point)

        # 4) Index + Middle + Ring up, Middle-Ring pinch -> Right click
        if index and middle and ring and not pinky:
            distance = self._tracker.find_distance(
                self.MIDDLE_TIP, self.RING_TIP, landmark_list
            )
            if distance is not None and distance < settings.CLICK_DISTANCE_THRESHOLD:
                return self._handle_right_click(index_point)

        # 5) Index + Middle up, Index-Middle pinch -> Left click
        if index and middle and not ring and not pinky:
            distance = self._tracker.find_distance(
                self.INDEX_TIP, self.MIDDLE_TIP, landmark_list
            )
            if distance is not None and distance < settings.CLICK_DISTANCE_THRESHOLD:
                return self._handle_left_click(index_point)

        # 6) Index finger alone -> Move the cursor
        if index and not middle and not ring and not pinky:
            self._reset_streak()
            return GestureResult(Gesture.MOVE, index_point, "MOVE")

        self._reset_streak()
        return GestureResult(Gesture.NONE, index_point, "IDLE")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _point_of(landmark_list: List[Tuple[int, int, int]],
                   landmark_id: int) -> Tuple[int, int]:
        for lm_id, x, y in landmark_list:
            if lm_id == landmark_id:
                return x, y
        return 0, 0

    def _reset_streak(self) -> None:
        self._candidate_gesture = Gesture.NONE
        self._candidate_streak = 0

    def _debounced(self, gesture: Gesture) -> bool:
        """
        Requires a gesture to be seen for GESTURE_HOLD_FRAMES consecutive
        frames before it is considered "confirmed". This prevents a single
        noisy frame from triggering an accidental click.
        """
        if self._candidate_gesture == gesture:
            self._candidate_streak += 1
        else:
            self._candidate_gesture = gesture
            self._candidate_streak = 1

        return self._candidate_streak >= settings.GESTURE_HOLD_FRAMES

    def _handle_left_click(self, point: Tuple[int, int]) -> GestureResult:
        if not self._debounced(Gesture.LEFT_CLICK):
            return GestureResult(Gesture.NONE, point, "LEFT_CLICK (confirming)")

        now = time.time()
        if now - self._last_click_time < settings.CLICK_COOLDOWN:
            return GestureResult(Gesture.NONE, point, "LEFT_CLICK (cooldown)")

        self._last_click_time = now
        self._reset_streak()
        return GestureResult(Gesture.LEFT_CLICK, point, "LEFT_CLICK")

    def _handle_right_click(self, point: Tuple[int, int]) -> GestureResult:
        if not self._debounced(Gesture.RIGHT_CLICK):
            return GestureResult(Gesture.NONE, point, "RIGHT_CLICK (confirming)")

        now = time.time()
        if now - self._last_click_time < settings.CLICK_COOLDOWN:
            return GestureResult(Gesture.NONE, point, "RIGHT_CLICK (cooldown)")

        self._last_click_time = now
        self._reset_streak()
        return GestureResult(Gesture.RIGHT_CLICK, point, "RIGHT_CLICK")

    def _handle_double_click(self, point: Tuple[int, int]) -> GestureResult:
        if not self._debounced(Gesture.DOUBLE_CLICK):
            return GestureResult(Gesture.NONE, point, "DOUBLE_CLICK (confirming)")

        now = time.time()
        if now - self._last_double_click_time < settings.DOUBLE_CLICK_COOLDOWN:
            return GestureResult(Gesture.NONE, point, "DOUBLE_CLICK (cooldown)")

        self._last_double_click_time = now
        self._reset_streak()
        return GestureResult(Gesture.DOUBLE_CLICK, point, "DOUBLE_CLICK")

    def _handle_drag(self, point: Tuple[int, int]) -> GestureResult:
        if not self._is_dragging:
            if not self._debounced(Gesture.DRAG_START):
                return GestureResult(Gesture.NONE, point, "DRAG (confirming)")
            self._is_dragging = True
            self._reset_streak()
            return GestureResult(Gesture.DRAG_START, point, "DRAG_START")

        return GestureResult(Gesture.DRAG_HOLD, point, "DRAGGING")

    def _handle_scroll(self, landmark_list: List[Tuple[int, int, int]]) -> GestureResult:
        index_point = self._point_of(landmark_list, self.INDEX_TIP)
        current_y = index_point[1]

        if self._previous_scroll_y is None:
            self._previous_scroll_y = current_y
            return GestureResult(Gesture.NONE, index_point, "SCROLL (ready)")

        delta_y = current_y - self._previous_scroll_y

        if abs(delta_y) < settings.SCROLL_DEAD_ZONE:
            return GestureResult(Gesture.NONE, index_point, "SCROLL (idle)")

        self._previous_scroll_y = current_y

        if delta_y < 0:
            return GestureResult(Gesture.SCROLL_UP, index_point, "SCROLL_UP")
        return GestureResult(Gesture.SCROLL_DOWN, index_point, "SCROLL_DOWN")
