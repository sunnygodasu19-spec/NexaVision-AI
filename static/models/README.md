# 3D Human Model Support for NexaVision AI Hologram

The NexaVision AI cinematic intro can optionally load a custom 3D human adult male model in GLTF / GLB format.

## Recommended Model Specifications:
- File name: `male_bust.glb` or `human.glb`
- Placement: `AI_Fake_Image_Detection_Complete/static/models/`
- Subject: Adult male bust (head, neck, shoulders, upper torso)
- Format: Binary GLTF (`.glb`) or standard `.gltf` with embedded buffers
- Orientation: Facing away from camera (towards -Z, back facing +Z)
- Polycount: 10,000 to 50,000 vertices for optimal real-time particle sampling

## Built-in Procedural Hologram:
If no external `.glb` file is present in this directory, the application automatically uses its built-in high-density 15,000-point adult male anatomical particle engine in Three.js (with canvas fallback), ensuring consistent, photorealistic red/orange particle hologram rendering without requiring external downloads.

