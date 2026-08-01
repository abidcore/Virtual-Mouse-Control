"""
src/utils.py
============
Shared helper functions: geometry calculations and on-screen UI drawing.
Keeping these outside the main control loop keeps main.py focused and
readable.
"""

import math
from typing import Tuple

import cv2
import numpy as np

from config import settings


def calculate_distance(point_a: Tuple[int, int], point_b: Tuple[int, int]) -> float:
    """Euclidean distance between two 2D points."""
    return math.hypot(point_b[0] - point_a[0], point_b[1] - point_a[1])


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Restrict a value to the inclusive range [min_value, max_value]."""
    return max(min_value, min(value, max_value))


def map_range(value: float, in_min: float, in_max: float,
              out_min: float, out_max: float) -> float:
    """Linearly map a value from one numeric range to another."""
    in_span = in_max - in_min
    if in_span == 0:
        return out_min
    scaled = (value - in_min) / in_span
    return out_min + (scaled * (out_max - out_min))


def draw_rounded_panel(frame: np.ndarray, top_left: Tuple[int, int],
                        bottom_right: Tuple[int, int],
                        color: Tuple[int, int, int],
                        alpha: float = 0.6) -> np.ndarray:
    """Draw a semi-transparent filled rectangle used as a UI backdrop."""
    overlay = frame.copy()
    cv2.rectangle(overlay, top_left, bottom_right, color, thickness=-1)
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)


def draw_status_panel(frame: np.ndarray, fps: float, webcam_ok: bool,
                       detection_confidence: float, mode: str) -> np.ndarray:
    """
    Render the heads-up display: FPS counter, webcam status,
    detection confidence, and the currently recognized gesture mode.
    """
    panel_height = 130
    frame = draw_rounded_panel(
        frame, (0, 0), (300, panel_height), settings.COLOR_PANEL_BG, alpha=0.55
    )

    # FPS
    fps_color = settings.COLOR_SUCCESS if fps >= 15 else settings.COLOR_WARNING
    cv2.putText(frame, f"FPS: {fps:.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, fps_color, 2)

    # Webcam status
    status_text = "Webcam: ONLINE" if webcam_ok else "Webcam: OFFLINE"
    status_color = settings.COLOR_SUCCESS if webcam_ok else settings.COLOR_ERROR
    cv2.putText(frame, status_text, (12, 56),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

    # Detection confidence
    cv2.putText(frame, f"Detection Conf: {detection_confidence:.2f}",
                (12, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                settings.COLOR_TEXT, 1)

    # Current gesture / mode
    cv2.putText(frame, f"Mode: {mode}", (12, 112),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, settings.COLOR_PRIMARY, 2)

    return frame


def draw_exit_hint(frame: np.ndarray) -> np.ndarray:
    """Render the keyboard shortcut hint in the bottom-left corner."""
    h, _ = frame.shape[:2]
    text = f"Press '{settings.EXIT_KEY.upper()}' to exit safely"
    cv2.putText(frame, text, (12, h - 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, settings.COLOR_TEXT, 1)
    return frame


def draw_control_region(frame: np.ndarray) -> np.ndarray:
    """Draw the rectangle representing the active cursor-control zone."""
    h, w = frame.shape[:2]
    reduction = settings.FRAME_REDUCTION
    cv2.rectangle(
        frame,
        (reduction, reduction),
        (w - reduction, h - reduction),
        settings.COLOR_PRIMARY,
        2,
    )
    return frame
