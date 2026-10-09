# Robot Studio

## Current 3D work

[Open the live studio](https://humberto0o0.github.io/robot-studio/) · [Watch the speaking demo](https://humberto0o0.github.io/robot-studio/demo.html)

The live studio uses the procedural Blender robot with articulated hands, eight speech/expression morphs, eye expressions and audio-driven direction. See [the 3D performance guide](docs/3d-performance.md) for timing imports, browser controls, the optional Blender rendering API and the diagnostic video workflow. The older 2D renderer below remains available as a legacy path.

Robot Studio is an audio-driven animation and rendering system for a recurring robot news host.

The long-term goal is:

**story → script → voice → robot performance → story media → captions → vertical MP4 → publishing**

## What works now

### Browser studio

The root `index.html` is a mobile-first, self-contained studio designed for iPhone and desktop.

It can:

- upload MP3, WAV, M4A or AAC voice audio
- analyze speech, silence, pauses and emphasis locally in the browser
- drive multiple mouth states and character movement from audio
- accept the exact script for estimated word timing, captions and semantic gestures
- automatically plan gesture cues such as present, open-hand, mic-in, lean, nod and excited
- upload a story image and reveal it during the performance
- move/scale the robot to make room for story media
- burn captions into the canvas preview
- export Director JSON
- record the browser canvas where MediaRecorder/canvas capture are supported
- install as a PWA/Home Screen web app once GitHub Pages is enabled

The current studio renders the actual GLB robot. The older 2D bridge rig remains in the legacy renderer.

### Bot-facing API

The `server/` folder contains a FastAPI + FFmpeg + Pillow renderer.

Endpoints:

- `GET /health`
- `GET /capabilities`
- `POST /analyze`
- `POST /director`
- `POST /render`

The tested `/render` path accepts voice audio, an optional exact script, optional story headline and optional story image, then returns a vertical H.264/AAC MP4.

Current server preview target:

- 540×960
- 24 fps
- H.264 video
- AAC audio
- burned-in captions
- story-image reveal
- deterministic Director timeline

A 15.9-second test voice rendered successfully end-to-end.

## Security

- audio upload limit: 20 MB
- story image limit: 10 MB
- audio duration limit: 120 seconds
- uploads are processed through temporary storage and are not intentionally persisted by the API
- set `ROBOT_STUDIO_API_KEY` in hosted environments to protect `/analyze`, `/director` and `/render`
- never embed that private API key in the public GitHub Pages frontend

## CI

`.github/workflows/server-smoke.yml` builds the Docker container, starts the API, verifies API-key protection, generates a synthetic audio fixture and calls the real MP4 render endpoint.

## GitHub Pages

The frontend deployment workflow is in `.github/workflows/pages.yml`.

GitHub Pages needs to be enabled once in:

**Settings → Pages → Source: GitHub Actions**

After that, pushes to `main` deploy the studio.

Expected URL:

`https://humberto0o0.github.io/robot-studio/`

## Director contract

See `docs/director-schema.md`.

The Director JSON is deliberately separate from rendering so the browser preview, server renderer and future autonomous bot can all use the same animation plan.

## Next visual milestone

Replace the bridge rig with transparent production layers while preserving the existing Director engine:

1. neutral master body
2. head shell / face area
3. microphone arm
4. gesture arm
5. eye states
6. 7–9 mouth shapes

After the layered rig is locked, increase the renderer to 1080×1920.

## Next intelligence milestone

For bot-generated voice, the exact script is already known. The next lipsync improvement is **forced alignment** between that script and the generated audio so word/phoneme timing is precise instead of estimated.

For arbitrary user audio with no script, add self-hosted transcription first.
