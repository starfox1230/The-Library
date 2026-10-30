"""Streaming tempo/phase tracker. No Anki, network, or third-party dependencies."""
from collections import deque
import math


class BeatTracker:
    def __init__(self):
        self.history = deque(maxlen=400)
        self.onsets = deque(maxlen=40)
        self.period = 0.0
        self.phase = 0.0
        self.confidence = 0.0
        self.last_onset = -100.0
        self.last_fit = -100.0
        self.last_sound = -100.0
        self.mean = 0.0
        self.previous = 0.0

    def feed(self, now, energy, bass):
        # Positive changes emphasize drum attacks instead of sustained bass notes.
        level = max(0.0, bass * .8 + energy * .2)
        flux = max(0.0, level - self.previous)
        self.previous = level
        self.mean = self.mean * .97 + flux * .03
        self.history.append((now, flux))
        if energy > .001:
            self.last_sound = now
        if flux > max(.0008, self.mean * 2.4) and now - self.last_onset > .20:
            self.last_onset = now
            self.onsets.append((now, flux))
            if self.period:
                error = (now - self.phase + self.period / 2) % self.period - self.period / 2
                if abs(error) < self.period * .18:
                    self.phase += error * .16
        if now - self.last_fit > .8:
            self.last_fit = now
            self._fit(now)

    def _fit(self, now):
        recent = [(t, v) for t, v in self.onsets if now - t < 8]
        if len(recent) < 5 or now - self.last_onset > 2:
            self.confidence *= .65
            return
        candidates = []
        for a in range(len(recent)):
            for b in range(a + 1, min(a + 5, len(recent))):
                delta = recent[b][0] - recent[a][0]
                for beats in range(1, 5):
                    p = delta / beats
                    if 60 / 180 <= p <= 60 / 75:
                        candidates.append(p)
        if not candidates:
            return
        # Score phase agreement AND occupancy; subdivisions alone must not win.
        def score(p):
            origin = recent[-1][0]
            errors = [abs((t - origin + p / 2) % p - p / 2) / p for t, _ in recent]
            aligned = sum(e < .12 for e in errors)
            occupancy = min(1, aligned / max(1, (recent[-1][0] - recent[0][0]) / p))
            continuity = .04 * math.exp(-abs(p - self.period) * 30) if self.period else 0
            return sum(math.exp(-(e / .12) ** 2) for e in errors) / len(errors) * (.65 + .35 * occupancy) + continuity
        chosen = max(candidates, key=score)
        confidence = min(1.0, score(chosen))
        if confidence < .6:
            self.confidence *= .8
            return
        if not self.period or abs(chosen - self.period) > .05:
            self.period, self.phase = chosen, recent[-1][0]
        else:
            self.period = self.period * .8 + chosen * .2
        self.confidence = confidence

    def snapshot(self, now, lead_ms=35):
        fresh = now - self.last_onset < 2 and now - self.last_sound < .6
        locked = self.period > 0 and self.confidence > .64 and fresh
        # Next visual peak, advanced by the calibrated capture/render delay.
        phase = self.phase - lead_ms / 1000
        next_beat = phase + math.ceil((now - phase) / self.period) * self.period if locked else now
        return {"bpm": round(60 / self.period, 1) if locked else 0,
                "confidence": round(self.confidence, 3) if fresh else 0,
                "period": self.period if locked else 0,
                "next_in": max(0, next_beat - now) if locked else 0}
