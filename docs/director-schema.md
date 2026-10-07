# Robot Studio Director schema

Current schema id: `robot-studio-director/v1`

The Director JSON is the stable boundary between story/audio intelligence and rendering. The browser preview and future server renderer should consume the same structure.

```json
{
  "schema": "robot-studio-director/v1",
  "createdAt": "ISO timestamp",
  "duration": 20.4,
  "script": "Optional exact spoken script",
  "settings": {
    "energy": 0.62,
    "mouth": true,
    "head": true,
    "gestures": true,
    "captions": true,
    "camera": true
  },
  "speech": [
    { "start": 0.42, "end": 3.91 }
  ],
  "pauses": [
    { "start": 3.91, "end": 4.38 }
  ],
  "emphasis": [
    { "time": 6.12, "strength": 0.84 }
  ],
  "gestures": [
    {
      "time": 6.12,
      "type": "excited",
      "duration": 0.72,
      "source": "audio"
    }
  ],
  "words": [
    {
      "text": "incredible",
      "clean": "incredible",
      "start": 5.70,
      "end": 6.29
    }
  ],
  "visemes": [
    {
      "time": 5.70,
      "end": 5.78,
      "shape": "E",
      "word": 3
    }
  ]
}
```

## Gesture vocabulary

- `present`
- `open-hand`
- `mic-in`
- `lean`
- `nod`
- `emphasis`
- `excited`

Every production gesture must return to the neutral pose so cues can be chained in any order.

## Mouth vocabulary

The current bridge renderer uses:

- `REST`
- `M` — closed / M-B-P family
- `F` — F-V family
- `A`
- `E`
- `O`
- `S` — general consonant / transition shape

A future phoneme aligner may produce more precise timing without changing the renderer contract.

## Production renderer target

- 1080x1920
- 30 fps
- H.264/AAC MP4
- captions rendered into the frame
- deterministic output from a Director JSON + audio + media assets
