"""Boundary tests for the optional endpoint; real rendering is covered by the demo job."""
import asyncio,io,json,unittest,wave
from unittest.mock import patch
from fastapi import HTTPException,UploadFile
from server.main import render_video_3d


def audio():
    stream=io.BytesIO()
    with wave.open(stream,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0\0'*24000)
    return UploadFile(filename='voice.wav',file=io.BytesIO(stream.getvalue()))

class RenderBoundaryTests(unittest.TestCase):
    def call(self,quality='preview',performance=''):
        return asyncio.run(render_video_3d(audio(),'Hello',quality,performance))
    def test_unavailable(self):
        with patch('server.main.renderer3d_available',return_value=False):
            with self.assertRaises(HTTPException) as ctx:self.call()
        self.assertEqual(ctx.exception.status_code,503)
    def test_bad_quality_and_timing(self):
        with patch('server.main.renderer3d_available',return_value=True):
            for quality,timing in [('unbounded',''),('draft','[]'),('draft',json.dumps({'duration':9}))]:
                with self.assertRaises(HTTPException) as ctx:self.call(quality,timing)
                self.assertEqual(ctx.exception.status_code,422)
    def test_mp4_response_contract(self):
        with patch('server.main.renderer3d_available',return_value=True),patch('server.main.render_3d_mp4',return_value=b'tested-by-render-job') as renderer:
            result=self.call()
        self.assertEqual(result.media_type,'video/mp4');self.assertEqual(result.headers['cache-control'],'no-store')
        self.assertEqual(renderer.call_args.args[2],'preview')

if __name__=='__main__':unittest.main()
