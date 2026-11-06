# NexaVision AI — AI-Based Fake Image Detection System

A beginner-friendly Flask project with a cinematic responsive interface, drag-and-drop image upload, animated entry/scan/result transitions, a MobileNetV2 transfer-learning training script, and a prediction endpoint. The upload interface accepts people, pets, products, vehicles, landscapes, food, objects, and artwork.

## Important model note

This ZIP contains the full source code, **not a pretrained detector model or image dataset**. A meaningful prediction requires you to train the model using appropriately labeled, legally obtained images. Until `models/fake_image_detector.keras` exists, the website will display a model-not-ready notice instead of inventing a prediction.

A detector score is an estimate, not proof that an image is real or AI-generated. Do not use this demo alone for high-stakes decisions.

## 1. Requirements

- Python 3.10 or 3.11 recommended for TensorFlow compatibility
- Internet connection for the first TensorFlow/Keras model training run (MobileNetV2 ImageNet weights are downloaded)
- A dataset organized as described below

## 2. Create a virtual environment

Windows PowerShell:

```powershell
cd path\to\AI_Fake_Image_Detection_Complete
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

## 3. Run the website

```bash
python app.py
```

Open http://127.0.0.1:5000

You can explore the UI without a model. To receive predictions, complete the dataset and training steps below.

## 4. Prepare a dataset

Create this folder structure and add images with verified labels:

```text
raw_dataset/
  real/
    real_photo_001.jpg
  ai/
    generated_image_001.png
```

Use a diverse, balanced dataset and confirm that the labels are accurate. Avoid near-duplicates across train and validation splits, and check licenses and usage permissions.

Then run:

```bash
python prepare_dataset.py --source raw_dataset --output dataset
```

The helper copies image files only; it does not download, label, or verify images.

## 5. Train the model

```bash
python train.py --data dataset --epochs 5
```

The script saves:

- `models/fake_image_detector.keras`
- `models/evaluation_metrics.json`

Training may take a long time and requires enough RAM/compute. Increase epochs only after validating the pipeline. The provided script uses a simple 80/20 split; for serious evaluation, use a separate test set and evaluate for dataset leakage and bias.

## 6. Deployment (Render example)

1. Push the source to a Git repository.
2. Create a Render **Web Service** connected to the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Ensure the trained model is available to the deployed service. Large model files may exceed Git hosting limits; use an appropriate model artifact/storage solution if needed.
6. Deploy and check `/health`.

TensorFlow deployments can require substantial build time and memory. If deployment fails due to memory or dependency constraints, use a compatible Python/runtime and an instance with sufficient resources.

## Project structure

```text
AI_Fake_Image_Detection_Complete/
├── app.py
├── train.py
├── prepare_dataset.py
├── requirements.txt
├── README.md
├── .gitignore
├── models/
│   └── .gitkeep
├── static/
│   ├── style.css
│   ├── app.js
│   └── uploads/
│       └── .gitkeep
└── templates/
    └── index.html
```

## Classes and score interpretation

The training script defines class names `real` and `ai`, where the sigmoid output represents the `ai` class probability. Include diverse subjects in both classes if you want the model to generalize across people, objects, pets, products, scenes, and artwork; the interface itself does not restrict subjects. The app assumes the first/only output is AI probability. If you use a different model architecture or label mapping, update `predict_image()` accordingly.

## Security and privacy notes

- Uploaded images are saved under `static/uploads/` for preview. Add an upload-retention cleanup policy before using this beyond a local demo.
- This is a project starter, not a production forensic service.
- Do not upload private or sensitive images to a deployment you do not control.


## Ultimate UI update
- Added a dark/light appearance toggle (saved in the browser).
- Added an exact cinematic hologram intro animation (8-second sequence with smooth fade-away transition):
  - **0–1.5s**: Full-screen dark navy/black background with slowly revealing metallic `DEVELOPERZ-AREA` text across the middle background.
  - **1.5–3.0s**: Realistic 3D adult male human model (viewed from behind: head, neck, broad shoulders, upper torso) gradually materializes in glowing red/orange digital particles from `static/models/male-hologram.glb`.
  - **3.0–5.5s**: Glowing orange/red scanning laser beam sweeps slowly from the head down to the upper torso, illuminating the particles with warm amber flares as it passes.
  - **5.5–7.0s**: Fully illuminated male hologram and `DEVELOPERZ-AREA` text remain held firmly and clearly visible. Minimal `NEXAVISION AI` title and `THE FUTURE OF IMAGE INTELLIGENCE` subtitle appear.
  - **7.0–8.0s**: Brief hold, followed by a smooth cinematic **fade-away transition** (`is-fading-out`) that smoothly fades out the intro over 1.2s to reveal the homepage underneath with a gentle zoom-out.
  - **3D Asset Support**: Three.js particle system with surface vertex sampling from `static/models/male-hologram.glb` (~37,000 anatomical surface points), normal-based Fresnel rim lighting, mathematical anti-blowout color clamping (preventing solid white blobs), and an offline canvas fallback.
  - **Controls**: `ENTER SITE / SKIP INTRO [ESC]` for immediate reveal, `✦ 3D Intro` replay button in the navigation header, and `sessionStorage` support to play once per session.
- Added a cinematic full-screen scan HUD with a floating image preview, rotating rings, moving scan beam, pixel grid, live analysis-stage titles, and progress indicator.
- Added an animated result image reveal.
- Updated header branding to NexaVision AI.

To use this UI in an existing copy, replace `templates/index.html`, `static/style.css`, and `static/app.js` with the versions from this project. Keep your existing `app.py` and trained model.
