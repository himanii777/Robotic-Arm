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
HANDSHAKE_ROLL_OFFSET_DEG = -90.0

FINGER_CHAINS = (
    ("thumb", ("THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP")),
    ("index", ("INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP")),
    ("middle", ("MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP")),
    ("ring", ("RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP")),
    ("pinky", ("PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP")),
)

FINGER_RENDER_SPEC = {
    "thumb": {"base": (-0.42, -0.06), "splay": -44.0, "lengths": (0.24, 0.21, 0.18)},
    "index": {"base": (-0.28, 0.20), "splay": -9.0, "lengths": (0.27, 0.23, 0.19)},
    "middle": {"base": (0.0, 0.28), "splay": 0.0, "lengths": (0.30, 0.25, 0.20)},
    "ring": {"base": (0.25, 0.22), "splay": 7.0, "lengths": (0.28, 0.23, 0.18)},
    "pinky": {"base": (0.46, 0.10), "splay": 15.0, "lengths": (0.23, 0.19, 0.16)},
}


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


def estimate_wrist_yaw_deg(hand_landmarks, hand_enum):
    lm = hand_landmarks.landmark
    wrist = lm[hand_enum.WRIST]
    middle_mcp = lm[hand_enum.MIDDLE_FINGER_MCP]

    dx = middle_mcp.x - wrist.x
    dy = middle_mcp.y - wrist.y
    if abs(dx) + abs(dy) < 1e-6:
        return None

    return math.degrees(math.atan2(dx, -dy))


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
        min_yaw_deg=-60.0,
        max_yaw_deg=60.0,
        yaw_gain=1.0,
        yaw_translation_gain=140.0,
        yaw_wrist_gain=0.85,
        smoothing=0.22,
        yaw_smoothing=None,
        finger_smoothing=0.35,
        deadband_deg=1.5,
    ):
        self.min_roll_deg = float(min_roll_deg)
        self.max_roll_deg = float(max_roll_deg)
        self.min_yaw_deg = float(min_yaw_deg)
        self.max_yaw_deg = float(max_yaw_deg)
        self.yaw_gain = float(yaw_gain)
        self.yaw_translation_gain = float(yaw_translation_gain)
        self.yaw_wrist_gain = float(yaw_wrist_gain)
        self.smoothing = _clamp(float(smoothing), 0.01, 1.0)
        if yaw_smoothing is None:
            yaw_smoothing = smoothing
        self.yaw_smoothing = _clamp(float(yaw_smoothing), 0.01, 1.0)
        self.finger_smoothing = _clamp(float(finger_smoothing), 0.01, 1.0)
        self.deadband_deg = max(0.0, float(deadband_deg))
        self.neutral_raw_deg = None
        self.neutral_wrist_x = None
        self.neutral_wrist_yaw_deg = None
        self.raw_roll_deg = None
        self.raw_wrist_x = None
        self.raw_wrist_yaw_deg = None
        self.filtered_roll_deg = 0.0
        self.filtered_yaw_deg = 0.0
        self.command_roll_deg = 0.0
        self.command_yaw_deg = 0.0
        self.yaw_translation_component = 0.0
        self.yaw_wrist_component = 0.0
        self.finger_pose = None
        self.has_signal = False

    def update(self, hand_landmarks, hand_enum):
        raw_deg = None
        wrist_x = None
        wrist_yaw_deg = None
        if hand_landmarks is not None:
            raw_deg = estimate_hand_roll_deg(hand_landmarks, hand_enum)
            wrist_x = hand_landmarks.landmark[hand_enum.WRIST].x
            wrist_yaw_deg = estimate_wrist_yaw_deg(hand_landmarks, hand_enum)

        self.has_signal = raw_deg is not None and wrist_x is not None and wrist_yaw_deg is not None
        if not self.has_signal:
            return self.snapshot()

        self.raw_roll_deg = raw_deg
        self.raw_wrist_x = wrist_x
        self.raw_wrist_yaw_deg = wrist_yaw_deg
        if self.neutral_raw_deg is None:
            self.neutral_raw_deg = raw_deg
        if self.neutral_wrist_x is None:
            self.neutral_wrist_x = wrist_x
        if self.neutral_wrist_yaw_deg is None:
            self.neutral_wrist_yaw_deg = wrist_yaw_deg

        # The camera image is mirrored before MediaPipe runs, so roll deltas need
        # the opposite sign to make the robot visually mirror the user's wrist.
        target_roll = _clamp(
            _wrap_degrees(self.neutral_raw_deg - raw_deg),
            self.min_roll_deg,
            self.max_roll_deg,
        )
        self.filtered_roll_deg += self.smoothing * (target_roll - self.filtered_roll_deg)

        self.yaw_translation_component = (
            wrist_x - self.neutral_wrist_x
        ) * self.yaw_translation_gain
        self.yaw_wrist_component = _wrap_degrees(
            wrist_yaw_deg - self.neutral_wrist_yaw_deg
        ) * self.yaw_wrist_gain
        target_yaw = _clamp(
            (self.yaw_translation_component + self.yaw_wrist_component) * self.yaw_gain,
            self.min_yaw_deg,
            self.max_yaw_deg,
        )
        self.filtered_yaw_deg += self.yaw_smoothing * (target_yaw - self.filtered_yaw_deg)

        if abs(self.filtered_roll_deg) < self.deadband_deg:
            self.command_roll_deg = 0.0
        else:
            self.command_roll_deg = self.filtered_roll_deg

        if abs(self.filtered_yaw_deg) < self.deadband_deg:
            self.command_yaw_deg = 0.0
        else:
            self.command_yaw_deg = self.filtered_yaw_deg

        self.finger_pose = smooth_finger_pose(
            self.finger_pose,
            extract_finger_pose(hand_landmarks, hand_enum),
            self.finger_smoothing,
        )

        return self.snapshot()

    def calibrate_to_current(self):
        if (
            self.raw_roll_deg is None
            or self.raw_wrist_x is None
            or self.raw_wrist_yaw_deg is None
        ):
            return False

        self.neutral_raw_deg = self.raw_roll_deg
        self.neutral_wrist_x = self.raw_wrist_x
        self.neutral_wrist_yaw_deg = self.raw_wrist_yaw_deg
        self.filtered_roll_deg = 0.0
        self.filtered_yaw_deg = 0.0
        self.command_roll_deg = 0.0
        self.command_yaw_deg = 0.0
        self.yaw_translation_component = 0.0
        self.yaw_wrist_component = 0.0
        return True

    def reset(self):
        self.neutral_raw_deg = None
        self.neutral_wrist_x = None
        self.neutral_wrist_yaw_deg = None
        self.raw_roll_deg = None
        self.raw_wrist_x = None
        self.raw_wrist_yaw_deg = None
        self.filtered_roll_deg = 0.0
        self.filtered_yaw_deg = 0.0
        self.command_roll_deg = 0.0
        self.command_yaw_deg = 0.0
        self.yaw_translation_component = 0.0
        self.yaw_wrist_component = 0.0
        self.finger_pose = None
        self.has_signal = False

    def snapshot(self):
        return {
            "has_signal": self.has_signal,
            "raw_roll_deg": self.raw_roll_deg,
            "raw_wrist_x": self.raw_wrist_x,
            "raw_wrist_yaw_deg": self.raw_wrist_yaw_deg,
            "neutral_raw_deg": self.neutral_raw_deg,
            "neutral_wrist_x": self.neutral_wrist_x,
            "neutral_wrist_yaw_deg": self.neutral_wrist_yaw_deg,
            "command_roll_deg": self.command_roll_deg,
            "command_yaw_deg": self.command_yaw_deg,
            "yaw_translation_component": self.yaw_translation_component,
            "yaw_wrist_component": self.yaw_wrist_component,
            "min_roll_deg": self.min_roll_deg,
            "max_roll_deg": self.max_roll_deg,
            "min_yaw_deg": self.min_yaw_deg,
            "max_yaw_deg": self.max_yaw_deg,
            "finger_pose": self.finger_pose,
        }


def extract_finger_pose(hand_landmarks, hand_enum):
    lm = hand_landmarks.landmark
    wrist = lm[hand_enum.WRIST]
    index_mcp = lm[hand_enum.INDEX_FINGER_MCP]
    middle_mcp = lm[hand_enum.MIDDLE_FINGER_MCP]
    pinky_mcp = lm[hand_enum.PINKY_MCP]

    palm = max(math.hypot(middle_mcp.x - wrist.x, middle_mcp.y - wrist.y), 1e-6)
    across_x = pinky_mcp.x - index_mcp.x
    across_y = pinky_mcp.y - index_mcp.y
    across_len = max(math.hypot(across_x, across_y), 1e-6)
    side_axis = (across_x / across_len, across_y / across_len)

    palm_x = middle_mcp.x - wrist.x
    palm_y = middle_mcp.y - wrist.y
    side_component = palm_x * side_axis[0] + palm_y * side_axis[1]
    reach_axis = (
        palm_x - side_component * side_axis[0],
        palm_y - side_component * side_axis[1],
    )
    reach_len = math.hypot(reach_axis[0], reach_axis[1])
    if reach_len < 1e-6:
        reach_axis = (-side_axis[1], side_axis[0])
    else:
        reach_axis = (reach_axis[0] / reach_len, reach_axis[1] / reach_len)

    curls = {}
    for finger_name, chain in FINGER_CHAINS:
        points = []
        for landmark_name in chain:
            point = lm[getattr(hand_enum, landmark_name)]
            rel_x = point.x - wrist.x
            rel_y = point.y - wrist.y
            local_side = (rel_x * side_axis[0] + rel_y * side_axis[1]) / palm
            local_reach = (rel_x * reach_axis[0] + rel_y * reach_axis[1]) / palm
            points.append((local_side, local_reach))
        curls[finger_name] = estimate_finger_curl(finger_name, points)
    return curls


def estimate_finger_curl(finger_name, points):
    base = points[0]
    pip = points[1]
    dip = points[2]
    tip = points[-1]
    chain_len = 0.0
    for start, end in zip(points, points[1:]):
        chain_len += math.hypot(end[0] - start[0], end[1] - start[1])

    direct_len = math.hypot(tip[0] - base[0], tip[1] - base[1])
    straightness = direct_len / max(chain_len, 1e-6)
    bend = (
        joint_curl(base, pip, dip)
        + joint_curl(pip, dip, tip)
    ) / 2.0

    if finger_name == "thumb":
        extension = _clamp((direct_len - 0.12) / 0.62, 0.0, 1.0)
        raw_curl = max(1.0 - extension, bend)
    else:
        reach = tip[1] - base[1]
        reach_curl = 1.0 - _clamp((reach - 0.16) / 0.78, 0.0, 1.0)
        straight_curl = 1.0 - _clamp(straightness, 0.0, 1.0)
        raw_curl = max(reach_curl, bend, straight_curl)

    return _clamp(raw_curl * 1.35, 0.0, 1.0)


def joint_curl(a, b, c):
    first = (a[0] - b[0], a[1] - b[1])
    second = (c[0] - b[0], c[1] - b[1])
    first_len = math.hypot(first[0], first[1])
    second_len = math.hypot(second[0], second[1])
    if first_len < 1e-6 or second_len < 1e-6:
        return 0.0

    dot = (
        first[0] * second[0] + first[1] * second[1]
    ) / (first_len * second_len)
    angle = math.degrees(math.acos(_clamp(dot, -1.0, 1.0)))
    return _clamp((180.0 - angle) / 95.0, 0.0, 1.0)


def smooth_finger_pose(previous, current, smoothing):
    if previous is None:
        return current

    return {
        finger_name: previous.get(finger_name, curl)
        + smoothing * (curl - previous.get(finger_name, curl))
        for finger_name, curl in current.items()
    }


class RobotArmIsoView:
    def __init__(self, width=420):
        self.width = int(width)

    def draw(self, height, state):
        panel = np.full((height, self.width, 3), PANEL_BG, dtype=np.uint8)
        self._draw_grid(panel)
        self._draw_robot(panel, state)
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

    def _point_add(self, *vectors):
        return tuple(sum(vector[i] for vector in vectors) for i in range(3))

    def _point_scale(self, vector, scale):
        return (vector[0] * scale, vector[1] * scale, vector[2] * scale)

    def _draw_robot(self, panel, state):
        roll_deg = state["command_roll_deg"]
        yaw_deg = state["command_yaw_deg"]
        height, width = panel.shape[:2]
        center = (width // 2 + 18, int(height * 0.76))
        scale = min(width, height) * 0.19

        base = [(-0.7, -0.45, 0.0), (0.7, -0.45, 0.0), (0.7, 0.45, 0.0), (-0.7, 0.45, 0.0)]
        base_points = np.array([self._project(p, center, scale) for p in base], dtype=np.int32)
        cv2.fillConvexPoly(panel, base_points, (44, 48, 60), cv2.LINE_AA)
        cv2.polylines(panel, [base_points], True, ROBOT_LIMIT, 2, cv2.LINE_AA)

        elbow = (0.0, 0.0, 1.85)
        yaw = math.radians(yaw_deg)
        forward = (math.sin(yaw), math.cos(yaw), 0.0)
        right = (math.cos(yaw), -math.sin(yaw), 0.0)
        up = (0.0, 0.0, 1.0)
        wrist = self._point_add(elbow, self._point_scale(forward, 1.05))
        wrist_tip = self._point_add(wrist, self._point_scale(forward, 0.22))

        self._draw_segment(panel, (0.0, 0.0, 0.0), elbow, center, scale, ROBOT_BLUE, 13)
        self._draw_segment(panel, elbow, wrist, center, scale, ROBOT_BLUE, 12)
        self._draw_segment(panel, wrist, wrist_tip, center, scale, ROBOT_ORANGE, 12)

        elbow_px = self._project(elbow, center, scale)
        yaw_axis_end = self._project((0.0, 0.0, 2.30), center, scale)
        cv2.arrowedLine(panel, elbow_px, yaw_axis_end, WARNING, 2, cv2.LINE_AA, tipLength=0.18)

        roll = math.radians(roll_deg + HANDSHAKE_ROLL_OFFSET_DEG)
        hand_right = self._point_add(
            self._point_scale(right, math.cos(roll)),
            self._point_scale(up, math.sin(roll)),
        )
        hand_up = self._point_add(
            self._point_scale(right, -math.sin(roll)),
            self._point_scale(up, math.cos(roll)),
        )
        self._draw_fingers(panel, wrist_tip, forward, hand_right, hand_up, center, scale, state["finger_pose"])

    def _draw_fingers(self, panel, palm_origin, forward, hand_right, hand_up, center, scale, finger_pose):
        palm_base = self._point_add(palm_origin, self._point_scale(forward, 0.04))
        if not finger_pose:
            finger_pose = {finger_name: 0.12 for finger_name in FINGER_RENDER_SPEC}

        for finger_name, spec in FINGER_RENDER_SPEC.items():
            curl = _clamp(finger_pose.get(finger_name, 0.12), 0.0, 1.0)
            visual_curl = visual_finger_curl(finger_name, curl)
            base_side, base_height = spec["base"]
            base = self._point_add(
                palm_base,
                self._point_scale(hand_right, base_side),
                self._point_scale(hand_up, base_height),
            )
            points = [base]
            for segment_index, length in enumerate(spec["lengths"]):
                direction = self._finger_segment_direction(
                    finger_name,
                    spec["splay"],
                    visual_curl,
                    segment_index,
                    forward,
                    hand_right,
                    hand_up,
                )
                points.append(
                    self._point_add(points[-1], self._point_scale(direction, length))
                )

            for start, end in zip(points, points[1:]):
                self._draw_segment(panel, start, end, center, scale, ROBOT_GREEN, 5)

        wrist_left = self._point_add(palm_base, self._point_scale(hand_right, -0.34))
        wrist_right = self._point_add(palm_base, self._point_scale(hand_right, 0.34))
        palm_top = self._point_add(palm_base, self._point_scale(hand_up, 0.34))
        self._draw_segment(panel, wrist_left, wrist_right, center, scale, ROBOT_ORANGE, 6)
        self._draw_segment(panel, palm_base, palm_top, center, scale, ROBOT_ORANGE, 6)

    def _finger_segment_direction(
        self,
        finger_name,
        base_splay_deg,
        curl,
        segment_index,
        forward,
        hand_right,
        hand_up,
    ):
        if finger_name == "thumb":
            curl_angles = (18.0, 64.0, 108.0)
        else:
            curl_angles = (12.0, 78.0, 138.0)
        splay = math.radians(base_splay_deg)
        curl_angle = math.radians(curl * curl_angles[segment_index])

        curl_axis = hand_right if finger_name == "thumb" else hand_up
        curl_sign = 1.0 if finger_name == "thumb" else -1.0
        direction = self._point_add(
            self._point_scale(forward, math.cos(splay) * math.cos(curl_angle)),
            self._point_scale(hand_right, math.sin(splay) * math.cos(curl_angle)),
            self._point_scale(curl_axis, curl_sign * 0.72 * math.sin(curl_angle)),
        )
        length = max(
            math.sqrt(direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2),
            1e-6,
        )
        return (direction[0] / length, direction[1] / length, direction[2] / length)

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
        yaw = state["command_yaw_deg"]
        status = "TRACKING" if state["has_signal"] else "HOLDING LAST"
        status_color = ROBOT_GREEN if state["has_signal"] else WARNING

        cv2.putText(panel, "ROBOT ARM VIEW", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.72, PANEL_TEXT, 2, cv2.LINE_AA)
        cv2.putText(panel, "elbow yaw + wrist roll", (24, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.48, PANEL_MUTED, 1, cv2.LINE_AA)
        cv2.putText(panel, status, (24, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.60, status_color, 2, cv2.LINE_AA)
        cv2.putText(panel, f"roll command: {roll:+05.1f} deg", (24, 146), cv2.FONT_HERSHEY_SIMPLEX, 0.58, PANEL_TEXT, 2, cv2.LINE_AA)
        cv2.putText(panel, f"yaw command:  {yaw:+05.1f} deg", (24, 176), cv2.FONT_HERSHEY_SIMPLEX, 0.58, PANEL_TEXT, 2, cv2.LINE_AA)
        cv2.putText(panel, "vertical translation locked", (24, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.50, PANEL_MUTED, 1, cv2.LINE_AA)
        cv2.putText(panel, "c calibrate   r reset", (24, panel.shape[0] - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.50, PANEL_MUTED, 1, cv2.LINE_AA)


def visual_finger_curl(finger_name, curl):
    neutral_slack = 0.26 if finger_name == "thumb" else 0.22
    return _clamp((curl - neutral_slack) / (1.0 - neutral_slack), 0.0, 1.0)
