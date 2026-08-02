# Project Report: AI Virtual Mouse Control System

**Author:** [Your Name]
**Program:** Artificial Intelligence & Machine Learning Diploma
**Date:** 2026

---

## 1. Abstract

The AI Virtual Mouse Control System is a real-time, vision-based human-computer
interaction (HCI) application that replaces the traditional physical mouse with
hand-gesture input captured through a standard webcam. The system combines a
pretrained hand-landmark detection model (MediaPipe Hands) with a custom,
rule-based gesture recognition engine and operating-system-level cursor
control (PyAutoGUI). The result is a touch-free, low-latency pointing device
controllable entirely through natural hand movements.

---

## 2. Problem Statement

Traditional input devices (mouse, trackpad) require physical contact and
dedicated hardware, which can be limiting in contexts such as:

- Presentations where the presenter wants to remain hands-free at a distance
  from the machine.
- Hygiene-sensitive environments (e.g. medical, food handling) where touching
  shared hardware is undesirable.
- Assistive technology scenarios for users with limited fine-motor dexterity
  in traditional mouse grips.
- General exploration of gesture-based interfaces as a growing HCI modality.

This project addresses the problem by building a robust, low-latency,
webcam-only gesture control pipeline.

---

## 3. System Architecture

The system follows a modular, layered architecture:

```
Webcam Frame
     │
     ▼
HandTracker (MediaPipe)  ──► 21 hand landmarks (x, y) per frame
     │
     ▼
GestureDetector           ──► Discrete gesture classification + debouncing
     │
     ▼
MouseController            ──► Coordinate mapping, EMA smoothing, PyAutoGUI calls
     │
     ▼
Operating System Cursor
```

Each layer is implemented as an independent, testable Python class with a
single responsibility, following the **Single Responsibility Principle**
and standard object-oriented design practices:

- `HandTracker` — wraps MediaPipe's `Hands` solution; exposes landmark
  positions, finger-state detection, and inter-landmark distance utilities.
- `GestureDetector` — a stateful classifier that converts raw landmark data
  into one of a fixed set of `Gesture` enum values, using geometric rules
  (finger-up patterns and fingertip pinch distances) combined with temporal
  debouncing and cooldown logic.
- `MouseController` — maps normalized hand-frame coordinates to screen-space
  coordinates, applies exponential smoothing, and issues the corresponding
  PyAutoGUI calls (move, click, drag, scroll).
- `FPSCounter` — a small utility that reports a smoothed frames-per-second
  value for the on-screen HUD.
- `utils.py` — shared geometry (distance, clamping, range mapping) and
  HUD-drawing helper functions used by `main.py`.
- `main.py` (`VirtualMouseApp`) — the orchestrator that owns the OpenCV
  capture loop, wires the above components together, renders the heads-up
  display, and handles startup/shutdown and error conditions.

---

## 4. Methodology

### 4.1 Hand Landmark Detection

MediaPipe Hands provides a pretrained, real-time hand landmark model that
outputs 21 normalized (x, y, z) landmarks per detected hand from a single
RGB frame, without requiring any custom training data. Landmarks are
converted from MediaPipe's normalized [0, 1] coordinate space into pixel
coordinates relative to the captured frame resolution.

### 4.2 Finger State Estimation

For each of the five fingers, an "up" (extended) or "down" (curled) state is
estimated:

- For the four non-thumb fingers, a finger is considered "up" if its
  fingertip landmark's y-coordinate is above (numerically smaller than) its
  corresponding PIP-joint landmark's y-coordinate.
- The thumb is handled separately by comparing x-coordinates, since the
  thumb bends laterally rather than vertically relative to the palm.

### 4.3 Gesture Classification

Gestures are classified using a priority-ordered set of geometric rules
evaluated against the finger-state vector and selected fingertip distances:

| Priority | Condition | Gesture |
|---|---|---|
| 1 | All fingers curled (fist) | Drag start / hold |
| 2 | Index, middle, ring, pinky up; thumb down | Scroll mode |
| 3 | Thumb + index pinch, other fingers curled | Double click |
| 4 | Index + middle + ring up, middle-ring pinch | Right click |
| 5 | Index + middle up, index-middle pinch | Left click |
| 6 | Index up only | Move cursor |

### 4.4 Debouncing and Cooldown (Accidental Click Prevention)

Two mechanisms prevent unintentional actions:

1. **Frame-hold debouncing** — a candidate gesture must persist for
   `GESTURE_HOLD_FRAMES` consecutive frames before being confirmed, filtering
   out single-frame misclassifications caused by motion blur or momentary
   landmark noise.
2. **Cooldown timers** — after a click-type gesture fires, a minimum time
   interval (`CLICK_COOLDOWN` / `DOUBLE_CLICK_COOLDOWN`) must elapse before
   the same gesture can fire again, preventing a single sustained pinch from
   generating a rapid stream of clicks.

### 4.5 Cursor Mapping and Smoothing

Raw hand coordinates are captured within a *reduced control region* inside
the webcam frame (`FRAME_REDUCTION` margin on each side), so the user does
not need to stretch their hand to the physical edges of the camera's field
of view to reach the edges of the screen. These coordinates are linearly
mapped to full screen-space using:

```
screen_x = map_range(hand_x, reduction, frame_width - reduction, 0, screen_width)
screen_y = map_range(hand_y, reduction, frame_height - reduction, 0, screen_height)
```

To reduce natural hand tremor from translating into visible cursor shake, an
**Exponential Moving Average (EMA)** filter is applied to the mapped
coordinates before each `moveTo` call:

```
smoothed = previous + (target - previous) * smoothing_factor
```

A lower `SMOOTHING_FACTOR` produces a smoother but slightly laggier cursor;
a higher value produces a snappier but shakier cursor. This is exposed as a
single tunable constant in `config/settings.py`.

---

## 5. Error Handling & Reliability

- Camera initialization failures raise a descriptive `RuntimeError` and exit
  the application gracefully with an informative console message instead of
  crashing with a raw traceback.
- Individual frame-read failures (e.g. transient camera disconnects) are
  logged and retried rather than terminating the session; the on-screen
  webcam status indicator reflects the live connection state.
- The main loop is wrapped in a top-level `try/except/finally` block that
  guarantees camera and MediaPipe resources are always released, even on
  unexpected exceptions or a `KeyboardInterrupt` (Ctrl+C).
- The user can exit safely at any time via the `Q`/`ESC` keyboard shortcut
  or by closing the video window directly.

---

## 6. Testing & Observations

The system was manually tested under varying lighting conditions and camera
distances. Key observations:

- Detection is most reliable under consistent, front-facing lighting with
  the hand fully inside the frame.
- The debounce and cooldown mechanisms substantially reduced accidental
  click events compared to a naive "fire on every matching frame" approach.
- EMA smoothing (`SMOOTHING_FACTOR ≈ 0.35`) provided a good balance between
  responsiveness and stability for general desktop navigation tasks.

---

## 7. Limitations

- Single-hand tracking only (by design, for control stability); no
  multi-hand gesture vocabulary.
- Gesture recognition relies on hand-crafted geometric rules rather than a
  trained gesture classifier, which may be less robust to unusual hand
  poses or camera angles than a learned model.
- Performance is dependent on webcam quality, lighting, and host machine
  processing power.

---

## 8. Future Work

See the **Future Improvements** section of `README.md` for a full list,
including a learned gesture classifier, multi-monitor support, two-hand
gestures, and packaging as a standalone executable.

---

## 9. Conclusion

This project demonstrates an end-to-end, real-time computer vision pipeline
— from raw webcam input, through pretrained landmark detection and custom
gesture logic, to operating-system-level device control — built with
maintainable, modular, and well-documented software engineering practices
suitable for a professional portfolio.
