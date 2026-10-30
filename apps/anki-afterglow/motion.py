"""One shared music-driven flow clock for every pane of the Anki window."""
import math


class MusicMotion:
    def __init__(self):
        self.last = None
        self.gain = .02
        self.level = self.bass = self.push = self.phase = 0.0
        self.hit = 0

    def feed(self, now, sound):
        dt = min(.1, max(0, now-self.last)) if self.last is not None else 0
        self.last = now
        energy = max(0, sound.get('energy', 0))
        self.gain = max(.00005, self.gain+(energy-self.gain)*(1-math.exp(-dt*.7)))
        target = min(1, energy/(self.gain*1.7)) if energy > .00003 else 0
        bass = min(1, sound.get('bass', 0)/(self.gain*1.4)) if energy > .00003 else 0
        self.level += (target-self.level)*(1-math.exp(-dt*7))
        self.bass += (bass-self.bass)*(1-math.exp(-dt*6))
        self.push *= math.exp(-dt*6)
        hit = sound.get('hit_id', 0)
        if hit and hit != self.hit:
            self.push = 1
        self.hit = hit
        # A calm drift in silence, with actual sound accelerating and folding it.
        rate = .10 + self.level*.48 + self.bass*.22 + self.push*.16
        self.phase += dt*rate
        return dict(flow_time=self.phase, flow_rate=rate, music_level=self.level,
                    music_bass=self.bass, music_push=self.push)
