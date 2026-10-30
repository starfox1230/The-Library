import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('beat', Path(__file__).parents[1] / 'beat.py')
beat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(beat)


class BeatTests(unittest.TestCase):
    def rhythm(self, tracker, bpm, start=0, duration=12):
        period = 60 / bpm
        for i in range(int(duration / .02)):
            t = start + i * .02
            attack = (i * .02) % period < .02
            tracker.feed(t, .08 if attack else .01, .10 if attack else .005)
        return start + duration - .02

    def test_locks_and_predicts_future_beats(self):
        for bpm in (90, 120, 128, 150, 170):
            tracker = beat.BeatTracker()
            now = self.rhythm(tracker, bpm)
            state = tracker.snapshot(now, 0)
            self.assertAlmostEqual(state['bpm'], bpm, delta=3)
            self.assertGreaterEqual(state['next_in'], 0)
            self.assertLessEqual(state['next_in'], state['period'])

    def test_advance_shifts_prediction(self):
        tracker = beat.BeatTracker()
        now = self.rhythm(tracker, 120) - .15
        regular, advanced = tracker.snapshot(now, 0), tracker.snapshot(now, 40)
        self.assertAlmostEqual((regular['next_in'] - advanced['next_in']) % regular['period'], .04, places=5)

    def test_silence_unlocks(self):
        tracker = beat.BeatTracker()
        now = self.rhythm(tracker, 128)
        for i in range(1, 151):
            tracker.feed(now + i * .02, 0, 0)
        self.assertEqual(tracker.snapshot(now + 3)['period'], 0)

    def test_new_track_reacquires(self):
        tracker = beat.BeatTracker()
        self.rhythm(tracker, 120)
        now = self.rhythm(tracker, 150, start=12, duration=15)
        self.assertAlmostEqual(tracker.snapshot(now)['bpm'], 150, delta=3)

    def test_quiet_music_with_eighth_note_attacks(self):
        tracker = beat.BeatTracker()
        period = 60/128
        for i in range(650):
            t=i*.02
            onbeat=t%period<.02
            offbeat=(t-period/2)%period<.02
            strength=.0007 if onbeat else .00035 if offbeat else .00001
            tracker.feed(t,strength,strength)
        self.assertAlmostEqual(tracker.snapshot(t)['bpm'],128,delta=3)


if __name__ == '__main__':
    unittest.main()
