import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('motion',Path(__file__).parents[1]/'motion.py')
motion=importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)


class MotionTests(unittest.TestCase):
    def test_music_drives_clock_and_bass_folds(self):
        quiet=motion.MusicMotion()
        music=motion.MusicMotion()
        for i in range(240):
            now=i/30
            q=quiet.feed(now,{'energy':0,'bass':0})
            m=music.feed(now,{'energy':.03,'bass':.025,'hit_id':i//15+1})
        self.assertGreater(m['flow_time'],q['flow_time']*3)
        self.assertGreater(m['music_bass'],.4)
        self.assertGreater(m['music_level'],.4)

    def test_silence_settles_after_attack(self):
        driver=motion.MusicMotion()
        driver.feed(0,{'energy':.04,'bass':.03,'hit_id':1})
        for i in range(1,100):
            state=driver.feed(i/30,{'energy':0,'bass':0,'hit_id':1})
        self.assertLess(state['music_push'],.001)
        self.assertAlmostEqual(state['flow_rate'],.10,delta=.001)

    def test_same_timestamp_does_not_advance_shared_clock(self):
        driver=motion.MusicMotion()
        driver.feed(0,{'energy':.03,'bass':.02})
        first=driver.feed(1/30,{'energy':.03,'bass':.02})
        repeated=driver.feed(1/30,{'energy':.03,'bass':.02})
        self.assertEqual(first['flow_time'],repeated['flow_time'])

    def test_particle_clocks_and_camera_never_reverse_on_kicks(self):
        driver=motion.MusicMotion();previous=None
        for i in range(600):
            loud=i%15<3
            state=driver.feed(i/60,{'energy':.04 if loud else .001,'bass':.03 if loud else .0001,'hit_id':i//15+1,'bands':[.03 if loud else .0001]*8})
            if previous:
                self.assertTrue(all(a>=b for a,b in zip(state['particle_phases'],previous['particle_phases'])))
                self.assertGreaterEqual(state['camera_phase'],previous['camera_phase'])
            previous=state

    def test_bands_drive_different_particle_groups(self):
        driver=motion.MusicMotion()
        for i in range(240):state=driver.feed(i/30,{'energy':.02,'bass':.01,'bands':[.03]+[0]*7})
        self.assertGreater(state['particle_phases'][0],state['particle_phases'][7]*3)


if __name__=='__main__':
    unittest.main()
