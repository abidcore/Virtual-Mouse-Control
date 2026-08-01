"""
main.py
=======
Entry point for the AI Virtual Mouse Control System.

Captures webcam video, runs real-time hand tracking, converts the
tracked hand into mouse gestures, and drives the OS cursor accordingly.

Run this file directly to start the application:

    python main.py

Press 'Q' (or ESC) in the video window to exit safely at any time.
"""

import sys
import time

import cv2

from config import settings
from src.hand_tracker import HandTracker
from src.gesture_detector import GestureDetector, Gesture
from src.mouse_controller import MouseController
from src.fps import FPSCounter
from src.utils import draw_status_panel, draw_exit_hint, draw_control_region


class VirtualMouseApp:
    """Top-level application object: owns the main capture/processing loop."""

    def __init__(self) -> None:
        self.capture = None
        self.tracker = HandTracker()
        self.gesture_detector = GestureDetector(self.tracker)
        self.mouse = None
        self.fps_counter = FPSCounter()
        self.webcam_ok = False

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _open_camera(self) -> None:
        """Open the webcam and configure its resolution, with error handling."""
        self.capture = cv2.VideoCapture(settings.CAMERA_INDEX)

        if not self.capture.isOpened():
            raise RuntimeError(
                f"Could not open webcam at index {settings.CAMERA_INDEX}. "
                "Check that a camera is connected, that no other "
                "application is using it, and that OS camera permissions "
                "are granted."
            )

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        self.webcam_ok = True

        self.mouse = MouseController(settings.FRAME_WIDTH, settings.FRAME_HEIGHT)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Starts the application and runs until the user exits."""
        try:
            self._open_camera()
        except RuntimeError as error:
            print(f"[FATAL] {error}")
            sys.exit(1)

        print("=" * 60)
        print(" AI Virtual Mouse Control System - Started")
        print("=" * 60)
        print(f" Press '{settings.EXIT_KEY.upper()}' (or ESC) in the video "
              "window to exit safely.")
        print(" Gestures:")
        print("   Index finger only          -> Move cursor")
        print("   Index + Middle pinch        -> Left click")
        print("   Index + Middle + Ring pinch -> Right click")
        print("   Thumb + Index pinch         -> Double click")
        print("   Closed fist (hold + move)   -> Drag and drop")
        print("   Four fingers up (no thumb)  -> Scroll up / down")
        print("=" * 60)

        try:
            while True:
                success, frame = self.capture.read()

                if not success or frame is None:
                    self.webcam_ok = False
                    print("[WARNING] Failed to read frame from webcam. Retrying...")
                    time.sleep(0.1)
                    continue

                self.webcam_ok = True

                if settings.FLIP_CAMERA:
                    frame = cv2.flip(frame, 1)

                frame = self._process_frame(frame)

                cv2.imshow(settings.WINDOW_NAME, frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord(settings.EXIT_KEY) or key == 27:  # 27 = ESC key
                    print("Exit key pressed. Shutting down safely.")
                    break

                # Allow safe exit if the user closes the window directly.
                if cv2.getWindowProperty(
                    settings.WINDOW_NAME, cv2.WND_PROP_VISIBLE
                ) < 1:
                    print("Window closed. Shutting down safely.")
                    break

        except KeyboardInterrupt:
            print("\nInterrupted by user (Ctrl+C). Shutting down safely.")
        except Exception as error:  # noqa: BLE001 - top-level safety net
            print(f"[ERROR] Unexpected failure: {error}")
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    # Per-frame processing
    # ------------------------------------------------------------------
    def _process_frame(self, frame):
        """Runs detection, gesture recognition, and mouse control for one frame."""
        frame = self.tracker.find_hands(frame, draw=settings.SHOW_LANDMARKS)
        landmarks = self.tracker.find_positions(frame)

        result = self.gesture_detector.detect(landmarks)
        self._dispatch_gesture(result)

        frame = draw_control_region(frame)

        if settings.SHOW_STATUS_PANEL:
            fps = self.fps_counter.update()
            frame = draw_status_panel(
                frame,
                fps=fps,
                webcam_ok=self.webcam_ok,
                detection_confidence=self.tracker.last_detection_confidence,
                mode=result.raw_label,
            )

        frame = draw_exit_hint(frame)
        return frame

    def _dispatch_gesture(self, result) -> None:
        """Maps a GestureResult onto the appropriate MouseController call."""
        x, y = result.cursor_point

        if result.gesture == Gesture.MOVE:
            self.mouse.move(x, y)
        elif result.gesture == Gesture.LEFT_CLICK:
            self.mouse.left_click()
        elif result.gesture == Gesture.RIGHT_CLICK:
            self.mouse.right_click()
        elif result.gesture == Gesture.DOUBLE_CLICK:
            self.mouse.double_click()
        elif result.gesture == Gesture.DRAG_START:
            self.mouse.start_drag(x, y)
        elif result.gesture == Gesture.DRAG_HOLD:
            self.mouse.drag_to(x, y)
        elif result.gesture == Gesture.DRAG_END:
            self.mouse.end_drag()
        elif result.gesture == Gesture.SCROLL_UP:
            self.mouse.scroll("up")
        elif result.gesture == Gesture.SCROLL_DOWN:
            self.mouse.scroll("down")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _cleanup(self) -> None:
        """Releases all camera, window, and MediaPipe resources."""
        if self.capture is not None:
            self.capture.release()
        cv2.destroyAllWindows()
        self.tracker.close()
        print("Resources released. Goodbye!")


if __name__ == "__main__":
    app = VirtualMouseApp()
    app.run()
