# 3D performance pipeline

The browser and Blender now animate named speech shapes on the same procedural robot. Both hands retain their V15 geometry.

## Browser preview

Upload voice audio and paste its exact words. The local director estimates word and mouth timing inside detected speech regions, leaving pauses closed. This is **text-derived timing, not phoneme recognition or forced alignment**. Without text, audio energy selects a simple fallback mouth pose.

Under **Director → Expression**, choose automatic, attentive or friendly eyes. Expand **Speech preview and timing** to inspect Ah, Ee, Oh, Oo, closed M/B/P, F/V, consonants and smile while paused. Returning to automatic restores voice-driven speech.

For accurate timing supplied by a voice/alignment service, load the matching audio, then import:

```json
{
  "schema": "robot-studio-timing/v1",
  "duration": 2.0,
  "visemes": [
    {"time": 0.1, "end": 0.3, "shape": "M"},
    {"time": 0.3, "end": 0.6, "shape": "A"}
  ],
  "words": [{"text": "Example", "start": 0.1, "end": 0.6}]
}
```

Allowed shapes: `A E O U M F S SMILE`. Silence is an absent cue. Cues must be ordered, non-overlapping and within the audio duration. Word timings are optional. Applying a new script regenerates estimates; loading new audio clears old timing.

**Export → Director JSON** emits `robot-studio-performance/v3`, including the speech cues, words, audio envelope, gestures and timing source. The Blender adapter also understands the existing server director representation.

## Automated Blender rendering

The API's existing `/render` remains the older 2D renderer. `/render3d` uses the actual `.blend` file and fixed render script. It is available only in an environment with Blender, FFmpeg and the model installed. GitHub Pages does not run this API.

```bash
docker build -f server/Dockerfile.3d -t robot-studio-3d .
docker run --rm -p 8080:8080 -e ROBOT_STUDIO_API_KEY=your-private-key robot-studio-3d
curl --fail http://localhost:8080/render3d \
  -H 'X-Robot-Studio-Key: your-private-key' \
  -F 'audio=@voice.wav' -F 'script=The exact spoken words.' \
  -F 'quality=preview' -o performance.mp4
```

Optional form field `performance` accepts a complete exported performance JSON. Its duration must match the audio. Presets: draft (360×640), preview (540×960), fullhd (1080×1920). The synchronous endpoint limits takes to 30 seconds and one render at a time per process. Run a single API worker. No service has been provisioned automatically; this is a deployable renderer and a tested Actions demonstration.

Offline use, after installing the server requirements and Blender/FFmpeg:

```python
from pathlib import Path
import json
from server.render3d import render_3d_file
render_3d_file(Path('voice.wav'), json.loads(Path('director.json').read_text()),
               Path('performance.mp4'), quality='fullhd')
```

The compositor adds narration and captions. Story-image composition is still implemented only in the browser/legacy renderer; it is not yet in the Blender pass. Automatic transcription, forced alignment, voice generation via a provider, job queues and social publishing are not included.

## Reproducible diagnostic clip

Run **Build 3D Robot with Blender** manually in GitHub Actions, or use a commit message containing `[demo]`. After model/mobile validation, a separate job renders a short spoken test with the actual robot and uploads `robot-speaking-demo`.

The diagnostic voice is eSpeak, not the intended brand voice. The clip uses 360×640 at 12 fps for economical software-rendered inspection. The renderer supports larger presets, but full-HD offline performance is not established by this draft test. Mobile browser recording remains separately tested at 1080×1920.
