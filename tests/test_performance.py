import unittest
from blender.performance import normalize,shape_at,pose_at
from server.render3d import write_captions
from pathlib import Path
from tempfile import TemporaryDirectory

class PerformanceTests(unittest.TestCase):
    def test_browser_and_server_contract(self):
        a=normalize({'duration':2,'words':[{'word':'Hi','time':.1}], 'cues':[{'t':0,'pose':'wave'}], 'visemes':[{'time':.1,'end':.4,'shape':'A'}]})
        b=normalize({'duration':2,'words':[{'text':'Hi','start':.1}], 'gestures':[{'time':0,'type':'wave'}], 'visemes':[{'time':.1,'end':.4,'shape':'A'}]})
        self.assertEqual(a,b);self.assertEqual(shape_at(a,.5),'REST');self.assertEqual(shape_at(a,.2),'A')
        self.assertEqual(pose_at(a,1.9),('neutral',0))
    def test_invalid_timelines(self):
        for data in [{'duration':2,'words':'bad'},{'duration':2,'visemes':[1]},{'duration':float('nan')},{'duration':2,'visemes':[{'time':-1,'end':1,'shape':'A'}]},{'duration':2,'visemes':[{'time':0,'end':1,'shape':'CODE'}]}]:
            with self.assertRaises(ValueError):normalize(data)
    def test_caption_output(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'caption.srt';write_captions({'duration':2,'words':[{'word':'Hello','time':.2}]},p)
            self.assertIn('00:00:00,200 --> 00:00:02,000',p.read_text());self.assertIn('Hello',p.read_text())

if __name__=='__main__':unittest.main()
