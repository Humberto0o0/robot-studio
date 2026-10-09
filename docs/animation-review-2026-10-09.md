# Animation foundation review — 2026-10-09

## Implemented

- Continuous-topology speech morphs: A, E, O, U, M, F, S and smile, with a closed rest pose.
- Attentive/friendly LED-eye expressions and deterministic blinks.
- Browser audio/text estimates, optional imported speech timing and versioned director export.
- A real Blender render path sharing the speech/performance contract, with narration and captions composed by FFmpeg.
- A reproducible spoken diagnostic take, with fixed portrait framing and restrained gestures.
- Static microphone grille consolidated into one mesh. Both approved hand designs remain unchanged.
- Source-checked asset publishing avoids rebasing generated binary model files.

## Validation and review

The build regenerated both `.blend` and `.glb`. The mobile Chromium suite passed camera rotation, tilt, pinch, zoom controls, top view, reset, shape controls, audio decoding/playback, timing import, director export and 1080×1920 browser recording. This is mobile emulation, not a physical iPhone/Safari test.

Front, three-quarter and side screenshots were inspected. The grip is continuous and the approved presenting hand remains intact. The front emphasizes the curled white finger segments and dark joint accents. The side view exposes remaining garment fit work around the collar and lapels.

The first offline take revealed a cropped raised hand and distracting softbox reflections across the visor. The reviewed take uses wider, horizontally offset framing and lower specular contribution from the studio lights, plus smaller captions.

## Production priorities

1. **Fit the garments.** Conform the collar, shirt and lapels more closely to the body; close visible side gaps and check every arm pose. Avoid changing either hand.
2. **Choose the final voice and align it.** Use exact word/phoneme timings from the voice or an alignment service. Current text-derived estimates are a fallback, not accurate phoneme detection.
3. **Refine motion.** Add gesture anticipation, hold/recovery and phrase-specific gaze. Review a full take at 24–30 fps; the committed draft is only 12 fps.
4. **Compose a news frame.** Reserve space for story imagery, shorter caption groups and a headline. Offline story-image composition is still pending.
5. **Production rendering.** Validate full-HD render time and quality, then provision a queued worker. The optional API is implemented but no hosted render service has been deployed.

The committed diagnostic voice is eSpeak and is not the intended public voice. No automatic news sourcing, provider voice generation or social publishing is claimed by this work.
