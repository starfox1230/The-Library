import importlib.util
import unittest
from pathlib import Path
s = importlib.util.spec_from_file_location('helper', Path(__file__).parent.parent / 'extension/helper/server.py')
helper = importlib.util.module_from_spec(s)
s.loader.exec_module(helper)
class Validation(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(helper.validate({'page':'https://medality.com/unit/demo/', 'video':'https://player.vimeo.com/video/123?h=abc'})[0], 'https://player.vimeo.com/video/123?h=abc')
    def test_rejects_other_hosts_and_schemes(self):
        for page in ['https://medality.com.evil.test/', 'http://medality.com/', 'file:///tmp/demo']:
            with self.assertRaises(ValueError): helper.validate({'page':page, 'video':'https://player.vimeo.com/video/123'})
        for video in ['https://evil.test/', 'https://player.vimeo.com/video/123?other=1', 'file:///tmp/demo']:
            with self.assertRaises(ValueError): helper.validate({'page':'https://medality.com/', 'video':video})
if __name__ == '__main__': unittest.main()
