"""Pure attention policy. No camera, GUI, or biometric persistence."""
from dataclasses import dataclass
from enum import Enum
import math

class Signal(Enum):
    LOOKING = "Looking at screen"
    AWAY = "Looking away"
    BLINK = "Eyes closed"
    MISSING = "No face detected"
    UNCERTAIN = "Uncertain / low light"
    FAILURE = "Camera unavailable"

@dataclass(frozen=True)
class Observation:
    signal: Signal
    features: tuple | None = None  # yaw, pitch, horizontal iris ratio, vertical iris ratio

class AttentionPolicy:
    def __init__(self, settings):
        self.settings = settings
        self.covered = False
        self.pending = None
        self.since = 0.0
        self.blink_since = None

    def update(self, observation, now):
        signal = observation.signal
        if signal == Signal.BLINK:
            if self.blink_since is None:
                self.blink_since = now
            if now - self.blink_since < .45:
                # A blink cannot complete either a hide or reveal transition.
                self.pending = None
                return self.covered
            target = True
        else:
            self.blink_since = None
            target = {
                Signal.LOOKING: False, Signal.AWAY: True,
                Signal.MISSING: self.settings.missing_face_protect,
                Signal.UNCERTAIN: self.settings.uncertain_protect,
                Signal.FAILURE: self.settings.camera_failure_protect,
            }[signal]
        if target == self.covered:
            self.pending = None
        elif self.pending != target:
            self.pending, self.since = target, now
        elif now - self.since >= (self.settings.away_delay if target else self.settings.return_delay):
            self.covered, self.pending = target, None
        return self.covered

class Classifier:
    def __init__(self, settings):
        self.settings = settings
        self.smoothed = None
        self.was_looking = False

    def classify(self, features, blink=False):
        if not all(math.isfinite(x) for x in features):
            return Observation(Signal.UNCERTAIN)
        if blink:
            return Observation(Signal.BLINK)
        self.smoothed = features if self.smoothed is None else tuple(.65*n + .35*o for n,o in zip(features,self.smoothed))
        base = self.settings.calibration or (0, 0, .5, .5)
        limits = (24, 20, .19, .23)
        margin = 1.15 if self.was_looking else .9
        looking = all(abs(v-b) < limit * margin / self.settings.sensitivity
                      for v,b,limit in zip(self.smoothed,base,limits))
        self.was_looking = looking
        return Observation(Signal.LOOKING if looking else Signal.AWAY, features)
