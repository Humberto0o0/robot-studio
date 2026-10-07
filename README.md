# Robot Studio

Robot Studio is an audio-driven animation engine for the recurring robot host.

## V4 status

The current web build is mobile-first and self-contained. It can:

- accept MP3, WAV, M4A or AAC voice audio
- analyze speech energy, pauses and emphasis in the browser
- switch among multiple animated mouth states from the audio alone
- use an optional exact script to estimate word timing, captions and semantic gestures
- animate idle float, head motion, eye reactions, emphasis and camera movement
- show Studio, Director and Rig views
- export a reusable Director JSON timeline
- record the canvas preview on browsers that support MediaRecorder + canvas capture

The master robot image is embedded into the V4 page so the character loads without a separate image request.

## Architecture

Voice audio -> audio analysis -> director timeline -> character renderer -> captions / gestures -> video renderer.

The same Director JSON is intended to drive both the browser preview and the future server-side 1080x1920 MP4 renderer.

## Current limitation

The polished robot is still a bridge rig: the master artwork is one image, while face/mouth/eye states and whole-character movement are layered on top. The next visual milestone is replacing the microphone arm and presenting arm with separate transparent assets while preserving the same Director timeline.

## GitHub Pages

The repository includes a Pages deployment workflow in `.github/workflows/pages.yml`.

GitHub Pages must be enabled once in repository Settings -> Pages with **Source: GitHub Actions**. After that, pushes to `main` deploy automatically.
