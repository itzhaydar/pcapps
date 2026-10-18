from dataclasses import dataclass, asdict, fields
import json
import os
from pathlib import Path

@dataclass
class Settings:
    camera: int = 0
    sensitivity: float = 1.0
    away_delay: float = 0.8
    return_delay: float = 0.3
    missing_face_protect: bool = True
    camera_failure_protect: bool = True
    uncertain_protect: bool = True
    all_monitors: bool = True
    appearance: str = "Midnight"
    startup: bool = False
    fps: int = 10
    calibration: list | None = None

    def validate(self):
        if type(self.camera) is not int or not 0 <= self.camera <= 20:
            raise ValueError("Camera index must be between 0 and 20")
        for name, low, high in [("sensitivity", .5, 2), ("away_delay", .1, 10),
                                ("return_delay", .1, 5), ("fps", 3, 20)]:
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not low <= value <= high:
                raise ValueError(f"Invalid {name}")
        if type(self.fps) is not int:
            raise ValueError("FPS must be an integer")
        for name in ("missing_face_protect", "camera_failure_protect", "uncertain_protect",
                     "all_monitors", "startup"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"Invalid {name}")
        if self.appearance not in ("Midnight", "Graphite", "Black"):
            raise ValueError("Invalid appearance")
        if self.calibration is not None:
            if not isinstance(self.calibration, (list, tuple)):
                raise ValueError("Invalid calibration")
            import math
            if len(self.calibration) != 4 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in self.calibration):
                raise ValueError("Invalid calibration")
        return self

    @classmethod
    def load(cls, path):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Settings must be an object")
            return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data}).validate()
        except FileNotFoundError:
            return cls()

    def save(self, path):
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        temporary.replace(path)

def data_directory():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local/share"))) / "GlanceGuard"
