"""Offline regression checks: no YouTube calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import collect_radiology_video_library as collector

class UpdateSafety(unittest.TestCase):
    def test_atomic_save_retains_previous_json_when_serialization_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'catalog.json'
            collector.save(target,{'good':True})
            with self.assertRaises(TypeError):
                collector.save(target,{'bad':object()})
            self.assertEqual(json.loads(target.read_text()),{'good':True})
            self.assertEqual(list(Path(directory).glob('*.tmp')),[])

    def test_playlist_failure_does_not_replace_catalog(self):
        def extract(url,flat=True):
            if url.endswith('/playlists'):
                raise RuntimeError('Simulated playlist failure')
            return {'entries':[]}
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'catalog.json'
            collector.save(target,{'videos':[],'preserved':True})
            with patch.object(collector,'CATALOG',target),patch.object(collector,'extract',extract):
                with self.assertRaisesRegex(RuntimeError,'Existing catalog retained'):
                    collector.inventory()
            self.assertTrue(json.loads(target.read_text())['preserved'])

if __name__=='__main__':unittest.main()
