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


if __name__=='__main__':
    unittest.main()
