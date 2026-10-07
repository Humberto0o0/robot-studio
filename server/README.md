# Robot Studio API

Backend for the autonomous Robot Studio pipeline.

- `GET /health`
- `GET /capabilities`
- `POST /analyze`: uploaded audio -> speech, pauses, emphasis and audio gestures
- `POST /director`: uploaded audio + optional script/headline -> Director JSON v2

Uploads are size-limited and are not persisted. M4A/MP4 audio is decoded through a short-lived temporary file because those containers may require seeking.

The included Dockerfile is ready for a future Cloud Run deployment. The next backend milestones are self-hosted transcription and deterministic 1080x1920 MP4 rendering.
