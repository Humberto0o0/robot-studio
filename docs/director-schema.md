# Robot Studio Director schema

Current schema id: `robot-studio-director/v2`

The Director JSON is the stable boundary between audio/story intelligence and rendering. Both the browser preview and the server-side MP4 renderer use the same concepts.

```json
{
  "schema": "robot-studio-director/v2",
  "duration": 20.4,
  "script": "Optional exact spoken script",
  "story": {
    "headline": "Clean energy breakthrough",
    "cues": [
      {
        "time": 5.1,
        "duration": 5.2,
        "type": "story-reveal"
      }
    ]
  },
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

Production gestures should return to the neutral pose so cues can be chained safely.

## Mouth vocabulary

The bridge renderer supports:

- `REST`
- `M` — M/B/P family
- `F` — F/V family
- `A`
- `E`
- `O`
- `S` — general consonant/transition

Exact scripts currently produce estimated word/viseme timing aligned to detected speech regions. A future forced aligner can improve timing precision without changing this renderer vocabulary.

## Story cues

A `story-reveal` cue tells the renderer when to reveal the story card. The current composition shifts/scales the robot left while story media appears on the right and then returns the robot to neutral.

## Renderer target

Current tested server preview:

- 540×960
- 24 fps
- H.264/AAC MP4
- captions burned into video frames
- optional uploaded story image

Production target after character rig quality is locked:

- 1080×1920
- 30 fps
- H.264/AAC MP4
