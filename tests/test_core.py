import csv
import json
from pathlib import Path
import struct
import tempfile
import unittest
import os
import numpy as np
from PIL import Image
from visionprep.geometry import focal_limit,teaching_fov,fit_planar_affine,transform_xy
from visionprep.protocols import read_request,write_request,parse_response,receive_exact,ModbusTcpClient,robot_command,robot_move
from visionprep.inspection import inspect,region,colour_fraction
from visionprep.samples import make_sample,default_rois,calibration_example,CASES
from visionprep.demo import run_demo

def temporary_directory():
    task_dir=os.environ.get('VISIONPREP_TEST_TMP')
    if task_dir:Path(task_dir).mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(dir=task_dir)

class GeometryTests(unittest.TestCase):
    def test_focal_example(self):
        np.testing.assert_allclose(teaching_fov(6.4,4.6,400,16),(160,115),atol=1e-12)
    def test_both_fov_axes(self):
        result=focal_limit(6.4,4.6,150,[16,12])
        self.assertEqual(result['both_axes_limit_mm'],57.5)
        self.assertTrue(teaching_fov(6.4,4.6,150,60)[1]<12)
        self.assertTrue(all(x>=y for x,y in zip(teaching_fov(6.4,4.6,150,50),(16,12))))
    def test_invalid_optics(self):
        for x in [0,-1,float('nan'),float('inf')]:
            with self.subTest(x=x),self.assertRaises(ValueError):teaching_fov(6.4,4.6,150,x)
    def test_nine_point_fit_and_unseen_point(self):
        d=calibration_example();fit=fit_planar_affine(d['pixels'],d['robot_xy_mm'])
        np.testing.assert_allclose(transform_xy(fit['matrix'],[352,267]),[197.6,136.65],atol=1e-9)
    def test_collinear_points_rejected(self):
        with self.assertRaises(ValueError):fit_planar_affine([[0,0],[1,1],[2,2]],[[0,0],[1,0],[2,0]])
    def test_insufficient_points(self):
        with self.assertRaises(ValueError):fit_planar_affine([[0,0],[1,1]],[[0,0],[1,1]])
    def test_nonfinite_points(self):
        with self.assertRaises(ValueError):fit_planar_affine([[0,0],[1,0],[0,float('nan')]],[[0,0],[1,0],[0,1]])
    def test_invalid_transform_shape(self):
        with self.assertRaises(ValueError):transform_xy([[1,0],[0,1]],[1,2])

class ProtocolTests(unittest.TestCase):
    def test_standard_read_vector(self):
        self.assertEqual(read_request(1,1,0).hex(),'000100000006010300000001')
    def test_standard_write_vector(self):
        self.assertEqual(write_request(2,1,1,2).hex(),'000200000006010600010002')
    def test_parse_read(self):
        data=bytes.fromhex('00010000000701030400011234')
        self.assertEqual(parse_response(data,1,1,3,expected_count=2),[1,4660])
    def test_parse_write(self):
        self.assertEqual(parse_response(write_request(2,1,1,2),2,1,6,expected_echo=(1,2)),(1,2))
    def test_mismatched_transaction(self):
        with self.assertRaises(ValueError):parse_response(bytes.fromhex('0001000000050103020001'),2,1,3,expected_count=1)
    def test_nonzero_protocol_id(self):
        with self.assertRaises(ValueError):parse_response(bytes.fromhex('0001000100050103020001'),1,1,3,expected_count=1)
    def test_modbus_exception(self):
        with self.assertRaisesRegex(ValueError,'exception code 2'):parse_response(bytes.fromhex('000100000003018302'),1,1,3,expected_count=1)
    def test_wrong_byte_count(self):
        with self.assertRaises(ValueError):parse_response(bytes.fromhex('0001000000050103020001'),1,1,3,expected_count=2)
    def test_write_echo_validation(self):
        with self.assertRaises(ValueError):parse_response(write_request(2,1,1,2),2,1,6,expected_echo=(1,3))
    def test_register_range(self):
        for address,count in [(65535,2),(0,0),(0,126),(-1,1)]:
            with self.subTest(address=address,count=count),self.assertRaises(ValueError):read_request(1,1,address,count)
    def test_word_ranges(self):
        for x in [-1,65536,True,1.5]:
            with self.subTest(value=x),self.assertRaises(ValueError):write_request(1,1,1,x)
    def test_split_tcp_frame(self):
        class FakeSocket:
            def __init__(self):self.chunks=[b'\0',b'\1\0',b'\0\0\5\1',b'\3\2',b'\0\2']
            def recv(self,n):
                if not self.chunks:return b''
                b=self.chunks.pop(0)
                if len(b)>n:self.chunks.insert(0,b[n:]);b=b[:n]
                return b
        s=FakeSocket();h=receive_exact(s,7);body=receive_exact(s,4)
        self.assertEqual(parse_response(h+body,1,1,3,expected_count=1),[2])
    def test_closed_connection(self):
        class EmptySocket:
            def recv(self,n):return b''
        with self.assertRaises(ConnectionError):receive_exact(EmptySocket(),7)
    def test_no_implicit_network_connection(self):
        c=ModbusTcpClient('192.168.1.20')
        self.assertIsNone(c.connection)
        with self.assertRaises(RuntimeError):c.read_holding()
    def test_robot_instruction_matches_taskbook(self):
        self.assertEqual(robot_command('home'),'$h');self.assertEqual(robot_command('blow'),'M3S500')
    def test_robot_move_format(self):
        self.assertEqual(robot_move(20,20,20,20,[[0,100]]*4),'x20y20z20a20')
    def test_robot_move_rejects_outside_limits(self):
        with self.assertRaises(ValueError):robot_move(500,20,20,0,[[0,100]]*4)
    def test_robot_move_rejects_nan(self):
        with self.assertRaises(ValueError):robot_move(float('nan'),20,20,0,[[0,100]]*4)

class InspectionTests(unittest.TestCase):
    def test_all_synthetic_case_ground_truth(self):
        expected={'ok':set(),'missing_resistor':{'R2'},'missing_capacitor':{'C1'},'wrong_capacitor_colour':{'C2'},'missing_chip':{'U1'},'multiple_defects':{'R2','C1','U1'}}
        for seed in [17,51,2026]:
            for case in CASES:
                with self.subTest(case=case,seed=seed):
                    result=inspect(make_sample(case,seed),default_rois())
                    self.assertEqual({r['id'] for r in result['components'] if not r['passed']},expected[case])
                    self.assertEqual(result['passed'],case=='ok')
    def test_wrong_resolution_is_rejected(self):
        with self.assertRaises(ValueError):inspect(Image.new('RGB',(100,100)),default_rois())
    def test_empty_roi_is_rejected(self):
        with self.assertRaises(ValueError):region(Image.new('RGB',(20,20)),[0,0,0,10])
    def test_outside_roi_is_rejected(self):
        with self.assertRaises(ValueError):region(Image.new('RGB',(20,20)),[-1,0,5,10])
    def test_colour_fraction(self):
        self.assertEqual(colour_fraction(Image.new('RGB',(10,10),'#ef892b'),'orange'),1)
        self.assertEqual(colour_fraction(Image.new('RGB',(10,10),'blue'),'orange'),0)
    def test_no_measurement_components_is_rejected(self):
        with self.assertRaises(ValueError):inspect(Image.new('RGB',(960,640)),{'image_size':[960,640],'components':[]})

class IntegrationTests(unittest.TestCase):
    def test_complete_demo_outputs_are_labelled(self):
        with temporary_directory() as temp:
            out=Path(temp)/'run';summary=run_demo(out)
            self.assertEqual((summary['samples'],summary['passed_samples'],summary['ng_samples']),(6,1,5))
            self.assertTrue(summary['is_synthetic']);self.assertFalse(summary['robot_plan']['sent'])
            self.assertEqual(len(list((out/'images').glob('SourceImage_*.png'))),6)
            self.assertEqual(len(list((out/'images').glob('RecordImage_*.png'))),6)
            with (out/'results.synthetic.csv').open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f));self.assertEqual(len(rows),6);self.assertTrue(all(r['is_synthetic']=='true' for r in rows))
            self.assertIn('离线合成样例',(out/'index.html').read_text(encoding='utf-8'))
    def test_existing_results_are_preserved(self):
        with temporary_directory() as temp:
            out=Path(temp);(out/'existing.txt').write_text('preserve')
            with self.assertRaises(FileExistsError):run_demo(out)

if __name__=='__main__':unittest.main()
