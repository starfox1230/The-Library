"""One shared music-driven flow clock for every pane of the Anki window."""
import math


class MusicMotion:
    def __init__(self):
        self.last = None
        self.gain = .02
        self.level = self.bass = self.push = self.phase = 0.0
        self.hit = 0
        self.camera = self.camera_goal = 0.0
        self.band_levels = [0.0]*8
        self.band_phases = [0.0]*8
        self.band_rates = [.1]*8
        self.club_phase = 0.0

    def feed(self, now, sound, impact=.8):
        impact=min(1,max(0,impact))
        dt = min(.1, max(0, now-self.last)) if self.last is not None else 0
        self.last = now
        energy = max(0, sound.get('energy', 0))
        self.gain = max(.00005, self.gain+(energy-self.gain)*(1-math.exp(-dt*.7)))
        target = min(1, energy/(self.gain*1.7)) if energy > .00003 else 0
        bass = min(1, sound.get('bass', 0)/(self.gain*1.4)) if energy > .00003 else 0
        self.level += (target-self.level)*(1-math.exp(-dt*7))
        self.bass += (bass-self.bass)*(1-math.exp(-dt*6))
        self.push *= math.exp(-dt*10)
        hit = sound.get('hit_id', 0)
        if hit and hit != self.hit:
            self.push = 1
            self.camera_goal += .28*impact
        self.hit = hit
        # A calm drift in silence, with actual sound accelerating and folding it.
        rate = .10 + self.level*.48 + self.bass*.22 + self.push*.16
        self.phase += dt*rate
        club_rate=.12+self.level*.5+self.push*impact*3.8
        self.club_phase+=dt*club_rate
        self.camera_goal += dt*.025
        self.camera += (self.camera_goal-self.camera)*(1-math.exp(-dt*2.4))
        bands=sound.get('bands') or [energy]*8
        for i in range(8):
            target=min(1,max(0,bands[i] if i<len(bands) else 0)/max(.00005,self.gain*.65)) if energy>.00003 else 0
            response=12 if target>self.band_levels[i] else 5
            self.band_levels[i]+=(target-self.band_levels[i])*(1-math.exp(-dt*response))
            # Kicks accelerate forward travel. Decaying sound never rewinds it.
            self.band_rates[i]=.10+self.band_levels[i]*.65+self.push*impact*(1.8 if i<3 else .85)
            self.band_phases[i]+=dt*self.band_rates[i]
        return dict(flow_time=self.phase, flow_rate=rate, club_time=self.club_phase,club_rate=club_rate,music_level=self.level,
                    music_bass=self.bass, music_push=self.push,
                    particle_phases=list(self.band_phases),particle_rates=list(self.band_rates),
                    camera_phase=self.camera,camera_rate=(self.camera_goal-self.camera)*2.4)
