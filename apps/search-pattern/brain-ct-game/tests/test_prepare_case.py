import unittest, tempfile, gzip, json, hashlib
from pathlib import Path
import numpy as np
from tools.prepare_case import normalize_volume, write_case, stack_slices

class PrepareTests(unittest.TestCase):
    def test_reversed_axis_preserves_patient_position(self):
        a = np.diag([-1., 2., 3., 1.]); a[0,3] = 10
        v,s,o = normalize_volume(np.array([[[11]],[[22]],[[33]]]), a)
        self.assertEqual(v[:,0,0].tolist(), [33,22,11])
        np.testing.assert_allclose(s,[1,2,3]); np.testing.assert_allclose(o,[8,0,0])

    def test_singular_or_nonfinite_affine_rejected(self):
        for a in [np.zeros((4,4)),np.full((4,4),np.nan)]:
            with self.assertRaises(ValueError): normalize_volume(np.zeros((2,2,2)),a)

    def test_oblique_affine_resamples_linear_hu_field(self):
        v=np.indices((5,5,5)).sum(axis=0)*10.
        a=np.eye(4);a[0,1]=0.5
        out,s,o=normalize_volume(v,a,spacing=[1,1,1])
        self.assertAlmostEqual(out[3,2,2],60,places=4)

    def test_serialization_x_fastest_little_endian_and_checksum(self):
        v=np.array([[[-1000,200]],[[40,1000]]])
        with tempfile.TemporaryDirectory() as d:
            write_case(v,[1,2,3],[0,0,0],{'id':'test'},d)
            raw=gzip.decompress(Path(d,'volume.i16.gz').read_bytes())
            self.assertEqual(np.frombuffer(raw,dtype='<i2').tolist(),[-1000,40,200,1000])
            self.assertEqual(json.loads(Path(d,'manifest.json').read_text())['sha256'],hashlib.sha256(raw).hexdigest())

    def test_overflow_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):write_case(np.full((1,1,1),40000),[1,1,1],[0,0,0],{},d)

    def slices(self,positions):
        from types import SimpleNamespace as S
        return [S(ImagePositionPatient=[0,0,z], ImageOrientationPatient=[1,0,0,0,1,0],
                  PixelSpacing=[2,3],pixel_array=np.full((2,2),i),RescaleSlope=2,
                  RescaleIntercept=-1000,SeriesInstanceUID='test') for i,z in enumerate(positions)]

    def test_slice_geometry_and_rescale(self):
        v,a=stack_slices(self.slices([5,10,15]))
        self.assertEqual(v[0,0,:].tolist(),[-1000,-998,-996])
        np.testing.assert_allclose(a,np.array([[3,0,0,0],[0,2,0,0],[0,0,5,5],[0,0,0,1]]))

    def test_nonuniform_slice_spacing_rejected(self):
        with self.assertRaises(ValueError):stack_slices(self.slices([5,10,19]))

if __name__=='__main__':unittest.main()
