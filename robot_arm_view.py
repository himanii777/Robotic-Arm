import math

import cv2
import numpy as np


PANEL_BG = (22, 24, 32)
PANEL_GRID = (60, 64, 78)
PANEL_TEXT = (238, 241, 248)
PANEL_MUTED = (160, 168, 184)
ROBOT_BLUE = (255, 148, 56)
ROBOT_ORANGE = (64, 180, 255)
ROBOT_GREEN = (110, 230, 170)
ROBOT_LIMIT = (82, 95, 120)
WARNING = (80, 110, 255)


def _wrap_degrees(angle):
    return (angle + 180.0) % 360.0 - 180.0


def _clamp(value, low, high):
    return max(low, min(high, value))


def estimate_hand_roll_deg(hand_landmarks, hand_enum):
    lm = hand_landmarks.landmark
    index_mcp = lm[hand_enum.INDEX_FINGER_MCP]
    pinky_mcp = lm[hand_enum.PINKY_MCP]

    dx = pinky_mcp.x - index_mcp.x
    dy = pinky_mcp.y - index_mcp.y
    if abs(dx) + abs(dy) < 1e-6:
        return None

    return math.degrees(math.atan2(-dy, dx))


def palm_scale(hand_landmarks, hand_enum):
    lm = hand_landmarks.landmark
    wrist = lm[hand_enum.WRIST]
    middle = lm[hand_enum.MIDDLE_FINGER_MCP]
    return math.hypot(wrist.x - middle.x, wrist.y - middle.y)


def select_primary_hand(hand_landmarks_list, hand_enum):
    if not hand_landmarks_list:
        return None
    return max(hand_landmarks_list, key=lambda hand: palm_scale(hand, hand_enum))


class RobotRollMapper:
    def __init__(
        self,
        min_roll_deg=-70.0,
        max_roll_deg=70.0,
        smoothing=0.22,
        deadband_deg=1.5,
    ):
        self.min_roll_deg = float(min_roll_deg)
        self.max_roll_deg = float(max_roll_deg)
        self.smoothing = _clamp(float(smoothing), 0.01, 1.0)
        self.deadband_deg = max(0.0, float(deadband_deg))
        self.neutral_raw_deg = None
        self.raw_roll_deg = None
        self.filtered_roll_deg = 0.0
        self.command_roll_deg = 0.0
        self.has_signal = False

    def update(self, hand_landmarks, hand_enum):
        raw_deg = None
        if hand_landmarks is not None:
            raw_deg = estimate_hand_roll_deg(hand_landmarks, hand_enum)

        self.has_signal = raw_deg is not None
        if raw_deg is None:
            return self.snapshot()

        self.raw_roll_deg = raw_deg
        if self.neutral_raw_deg is None:
            self.neutral_raw_deg = raw_deg

        relative = _wrap_degrees(raw_deg - self.neutral_raw_deg)
        target = _clamp(relative, self.min_roll_deg, self.max_roll_deg)
        self.filtered_roll_deg += self.smoothing * (target - self.filtered_roll_deg)

        if abs(self.filtered_roll_deg) < self.deadband_deg:
            self.command_roll_deg = 0.0
        else:
            self.command_roll_deg = self.filtered_roll_deg

        return self.snapshot()

    def calibrate_to_current(self):
        if self.raw_roll_deg is None:
            return False

        self.neutral_raw_deg = self.raw_roll_deg
        self.filtered_roll_deg = 0.0
        self.command_roll_deg = 0.0
        return True

    def reset(self):
        self.neutral_raw_deg = None
        self.raw_roll_deg = None
        self.filtered_roll_deg = 0.0
        self.command_roll_deg = 0.0
        self.has_signal = False

    def snapshot(self):
        return {
            "has_signal": self.has_signal,
            "raw_roll_deg": self.raw_roll_deg,
            "neutral_raw_deg": self.neutral_raw_deg,
            "command_roll_deg": self.command_roll_deg,
            "min_roll_deg": self.min_roll_deg,
            "max_roll_deg": self.max_roll_deg,
        }


class RobotArmIsoView:
    def __init__(self, width=420):
        self.width = int(width)

    def draw(self, height, state):
        panel = np.full((height, self.width, 3), PANEL_BG, dtype=np.uint8)
        self._draw_grid(panel)
        self._draw_robot(panel, state["command_roll_deg"])
        self._draw_roll_gauge(panel, state)
        self._draw_labels(panel, state)
        return panel

    def _project(self, point, center, scale):
        x, y, z = point
        sx = center[0] + scale * (0.866 * x - 0.866 * y)
        sy = center[1] + scale * (0.50 * x + 0.50 * y - z)
        return (int(round(sx)), int(round(sy)))

    def _draw_grid(self, panel):
        height, width = panel.shape[:2]
        origin = (width // 2, int(height * 0.76))
        scale = min(width, height) * 0.18
        for offset in np.linspace(-1.6, 1.6, 7):
            a = self._project((-1.8, offset, 0), origin, scale)
            b = self._project((1.8, offset, 0), origin, scale)
            c = self._project((offset, -1.8, 0), origin, scale)
            d = self._project((offset, 1.8, 0), origin, scale)
            cv2.line(panel, a, b, PANEL_GRID, 1, cv2.LINE_AA)
            cv2.line(panel, c, d, PANEL_GRID, 1, cv2.LINE_AA)

    def _draw_segment(self, panel, start, end, center, scale, color, thickness=10):
        a = self._project(start, center, scale)
        b = self._project(end, center, scale)
        cv2.line(panel, a, b, (30, 33, 42), thickness + 5, cv2.LINE_AA)
        cv2.line(panel, a, b, color, thickness, cv2.LINE_AA)
        cv2.circle(panel, a, max(4, thickness // 2), color, -1, cv2.LINE_AA)
        cv2.circle(panel, b, max(4, thickness // 2), color, -1, cv2.LINE_AA)

    def _draw_robot(self, panel, roll_deg):
        height, width = panel.shape[:2]
        center = (width // 2 + 18, int(height * 0.76))
        scale = min(width, height) * 0.19

        base = [(-0.7, -0.45, 0.0), (0.7, -0.45, 0.0), (0.7, 0.45, 0.0), (-0.7, 0.45, 0.0)]
        base_points = np.array([self._project(p, center, scale) for p in base], dtype=np.int32)
        cv2.fillConvexPoly(panel, base_points, (44, 48, 60), cv2.LINE_AA)
        cv2.polylines(panel, [base_points], True, ROBOT_LIMIT, 2, cv2.LINE_AA)

        self._draw_segment(panel, (0.0, 0.0, 0.0), (0.0, 0.0, 1.85), center, scale, ROBOT_BLUE, 13)
        self._draw_segment(panel, (0.0, 0.0, 1.85), (0.0, 1.05, 1.85), center, scale, ROBOT_BLUE, 12)

        wrist = (0.0, 1.05, 1.85)
        wrist_tip = (0.0, 1.27, 1.85)
        self._draw_segment(panel, wrist, wrist_tip, center, scale, ROBOT_ORANGE, 12)

        theta = math.radians(roll_deg)
        sep = 0.30
        finger_len = 0.58
        ux = math.sin(theta) * sep
        uz = math.cos(theta) * sep
        p1 = (ux, 1.28, 1.85 + uz)
        p2 = (ux, 1.28 + finger_len, 1.85 + uz)
        p3 = (-ux, 1.28, 1.85 - uz)
        p4 = (-ux, 1.28 + finger_len, 1.85 - uz)

        self._draw_segment(panel, p1, p2, center, scale, ROBOT_GREEN, 8)
        self._draw_segment(panel, p3, p4, center, scale, ROBOT_GREEN, 8)
        self._draw_segment(panel, p1, p3, center, scale, ROBOT_ORANGE, 6)

        axis_start = self._project((0.0, 1.05, 1.85), center, scale)
        axis_end = self._project((0.0, 1.80, 1.85), center, scale)
        cv2.arrowedLine(panel, axis_start, axis_end, WARNING, 2, cv2.LINE_AA, tipLength=0.18)

    def _draw_roll_gauge(self, panel, state):
        height, width = panel.shape[:2]
        center = (width - 72, 104)
        radius = 48
        min_roll = int(round(state["min_roll_deg"]))
        max_roll = int(round(state["max_roll_deg"]))
        roll = state["command_roll_deg"]

        cv2.ellipse(panel, center, (radius, radius), 0, 210, 330, ROBOT_LIMIT, 3, cv2.LINE_AA)
        clamped_fraction = (roll - min_roll) / max(1.0, max_roll - min_roll)
        clamped_fraction = _clamp(clamped_fraction, 0.0, 1.0)
        pointer_angle = math.radians(210.0 + 120.0 * clamped_fraction)
        pointer = (
            int(center[0] + math.cos(pointer_angle) * (radius - 7)),
            int(center[1] + math.sin(pointer_angle) * (radius - 7)),
        )
        cv2.line(panel, center, pointer, ROBOT_GREEN, 3, cv2.LINE_AA)
        cv2.circle(panel, center, 5, PANEL_TEXT, -1, cv2.LINE_AA)
        cv2.putText(panel, f"{min_roll}", (center[0] - radius - 14, center[1] + 68), cv2.FONT_HERSHEY_SIMPLEX, 0.45, PANEL_MUTED, 1, cv2.LINE_AA)
        cv2.putText(panel, f"{max_roll}", (center[0] + radius - 18, center[1] + 68), cv2.FONT_HERSHEY_SIMPLEX, 0.45, PANEL_MUTED, 1, cv2.LINE_AA)

    def _draw_labels(self, panel, state):
        roll = state["command_roll_deg"]
        status = "TRACKING" if state["has_signal"] else "HOLDING LAST"
        status_color = ROBOT_GREEN if state["has_signal"] else WARNING

        cv2.putText(panel, "ROBOT ROLL VIEW", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.72, PANEL_TEXT, 2, cv2.LINE_AA)
        cv2.putText(panel, "fixed base + vertical arm", (24, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.48, PANEL_MUTED, 1, cv2.LINE_AA)
        cv2.putText(panel, status, (24, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.60, status_color, 2, cv2.LINE_AA)
        cv2.putText(panel, f"roll command: {roll:+05.1f} deg", (24, 146), cv2.FONT_HERSHEY_SIMPLEX, 0.58, PANEL_TEXT, 2, cv2.LINE_AA)
        cv2.putText(panel, "translation locked", (24, 186), cv2.FONT_HERSHEY_SIMPLEX, 0.50, PANEL_MUTED, 1, cv2.LINE_AA)
        cv2.putText(panel, "c calibrate   r reset", (24, panel.shape[0] - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.50, PANEL_MUTED, 1, cv2.LINE_AA)
