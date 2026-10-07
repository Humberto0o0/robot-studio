# Robot Studio API

Backend for the autonomous Robot Studio pipeline.

## Endpoints

- `GET /health` — service health
- `GET /capabilities` — current engine features
- `POST /analyze` — voice audio → speech, pauses, emphasis and audio gestures
- `POST /director` — voice audio + optional script/headline → Director JSON v2
- `POST /render` — voice audio + optional script/headline/story image → vertical H.264/AAC MP4

## Current render target

The tested preview renderer outputs 540×960 at 24 fps with H.264 video and AAC audio. It burns captions into the frame, animates the robot from the Director timeline and can reveal an uploaded story image.

The production target is 1080×1920 after the rig and performance quality are locked.

## Privacy / upload handling

Audio uploads are size-limited to 20 MB and story images to 10 MB. Files are decoded/rendered through short-lived temporary storage and are not intentionally persisted by the API.

## Docker

Build from the repository root:

```bash
docker build -f server/Dockerfile -t robot-studio-api .
docker run --rm -p 8080:8080 robot-studio-api
```

The image includes FFmpeg and is ready for a future Cloud Run deployment.

## Next backend milestone

Add local/self-hosted transcription or forced alignment so arbitrary uploaded audio can produce true word/phoneme timing without requiring the exact script.


## Hosted API protection

For a public deployment, set the environment variable `ROBOT_STUDIO_API_KEY`. When set, `/analyze`, `/director` and `/render` require the header:

```
X-Robot-Studio-Key: <your secret>
```

Do not embed this secret in a public GitHub Pages frontend. It is intended for the private bot/backend workflow. Browser access to hosted rendering should later use user authentication or a short-lived token.

The API also caps audio at 120 seconds to protect render time and memory.
