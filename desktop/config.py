from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    monitor: int = 1
    profile: int = 0
    model: str = "yolo11n.pt"
    class_id: int = -1
    window_title: str = "Retrac"
    confidence: float = 0.20
    fov: int = 1600
    full_screen: bool = True
    smoothing: float = 0.0
    vertical: float = 0.35
    max_step: int = 0
    input_mode: str = "cursor"
    target_max_age: float = 0.25
    aim_key: int = 0x02
    toggle_key: int = 0x75
    aim_enabled: bool = True
    boxes: bool = True
    labels: bool = True
    circle: bool = False
    desktop_detection: bool = True
    automatic: bool = False
    image_size: int = 640
    tiled: bool = False
    exclude_self: bool = True
    exclude_left: int = 15
    exclude_top: int = 40
    exclude_right: int = 50
    exclude_bottom: int = 100
    box_style: str = "corners"
    box_color: str = "#65d5c7"
    uncertain_color: str = "#efb86e"
    line_color: str = "#65d5c7"
    skeleton_color: str = "#b9acff"
    line_width: int = 2
    opacity: int = 90
    fill_opacity: int = 8
    tracers: bool = True
    tracer_origin: str = "bottom"
    skeleton: bool = False
    joints: bool = False
    keypoint_confidence: float = 0.45
    uncertain_threshold: float = 0.45
    target_marker: bool = False


BUILTIN_POSE_MODELS = ("yolo11n-pose.pt", "yolo11m-pose.pt", "yolo11s-pose.pt", "yolo11x-pose.pt")

# Fields that require a fresh inference pass (epoch bump). Cosmetic / targeting
# tweaks are applied live without discarding the latest detections.
INFERENCE_FIELDS = frozenset({
    "model", "class_id", "confidence", "image_size", "tiled", "monitor", "skeleton",
})

SETTINGS_FILE = Path(__file__).resolve().with_name("settings.json")


def load_settings(path: Path | None = None) -> Settings:
    path = path or SETTINGS_FILE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    valid = {f.name for f in fields(Settings)}
    cleaned = {k: v for k, v in raw.items() if k in valid}
    try:
        return Settings(**cleaned)
    except TypeError:
        return Settings()


def save_settings(settings: Settings, path: Path | None = None) -> None:
    path = path or SETTINGS_FILE
    try:
        path.write_text(json.dumps(asdict(settings), indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    except OSError:
        pass
