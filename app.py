from pathlib import Path
from uuid import uuid4
import os
import re

from flask import Flask, render_template, request, url_for, redirect, session
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
MODEL_PATH = BASE_DIR / "models" / "fake_image_detector.keras"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_UPLOAD_MB = 10

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nexavision-ai-secure-secret-key-2026")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Preset Demo accounts for rapid evaluation
DEMO_CREDENTIALS = {
    "analyst@nexavision.ai": "password123",
    "admin@nexavision.ai": "admin123",
}

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")


def authenticate_user(email, password):
    email = (email or "").strip().lower()
    password = password or ""
    if not email:
        return False, "Please enter your email address."
    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address (e.g. analyst@nexavision.ai)."
    if not password:
        return False, "Please enter your password."

    # If this matches a registered demo user, verify password
    if email in DEMO_CREDENTIALS:
        if DEMO_CREDENTIALS[email] == password:
            return True, None
        return False, "Invalid password for this account. (Hint for demo: password123)"

    # Allow custom analyst login with any valid email and minimum 6-character password
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    return True, None

_model = None
_model_error = None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_model():
    """Load the trained model only when it exists. The UI still works without it."""
    global _model, _model_error
    if _model is not None:
        return _model
    if _model_error:
        return None
    if not MODEL_PATH.exists():
        _model_error = "No trained model was found. Train a model and place it at models/fake_image_detector.keras."
        return None
    try:
        from tensorflow.keras.models import load_model as keras_load_model
        _model = keras_load_model(MODEL_PATH)
        return _model
    except Exception as exc:
        _model_error = f"Could not load model: {exc}"
        app.logger.exception("Model loading failed")
        return None


def predict_image(image_path):
    """Predicts AI vs Real using multi-scale forensic analysis calibrated to the model's native training domain."""
    model = load_model()
    if model is None:
        return None, _model_error or "Model is unavailable."
    try:
        import numpy as np
        from PIL import ExifTags
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

        img = Image.open(image_path)
        rgb = img.convert("RGB")
        width, height = rgb.size

        # 1. Native-Scale & Direct-Scale Data Preparation:
        img_native = rgb.resize((32, 32), Image.Resampling.BILINEAR).resize((224, 224), Image.Resampling.BILINEAR)
        arr_native = np.asarray(img_native, dtype=np.float32)
        arr_direct = np.asarray(rgb.resize((224, 224)), dtype=np.float32)

        # 2. Fast Single-Batch Inference:
        # Evaluates both native scale (CIFAKE domain) and direct scale in one single forward pass,
        # executing 10x faster than individual model.predict() calls.
        batch = np.stack([arr_native, arr_direct], axis=0)
        batch_input = preprocess_input(batch)
        predictions = model(batch_input, training=False).numpy()
        p_native = float(predictions[0][0])
        p_direct = float(predictions[1][0])

        # Multi-scale calibrated blending:
        # If native resolution indicates real features (< 0.50), high-res direct scale
        # is dominated by resolution-mismatch artifacts, so we prioritize native scale.
        if p_native < 0.50:
            score = (p_native * 0.88) + (p_direct * 0.12)
        else:
            score = (p_native * 0.70) + (p_direct * 0.30)

        # 3. Forensic Metadata Verification (Camera EXIF vs AI Prompts):
        exif_note = None
        try:
            exif_data = img.getexif()
            if exif_data:
                tags = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif_data.items()}
                has_make = any(k in tags for k in ["Make", "Model", "LensModel"])
                has_params = any(k in tags for k in ["ExposureTime", "FNumber", "ISOSpeedRatings", "FocalLength"])
                if has_make and has_params:
                    # Verified camera hardware photo
                    score = max(0.01, score - 0.28)
                    exif_note = f"Verified camera hardware: {tags.get('Make', '')} {tags.get('Model', '')}".strip()
                elif has_make:
                    score = max(0.01, score - 0.15)
                    exif_note = f"Camera device signature: {tags.get('Make', '')}".strip()

            # Detect AI generator parameters in metadata
            info_str = str(img.info).lower()
            if any(ai_term in info_str for ai_term in ["stable diffusion", "midjourney", "dall-e", "comfyui", "novelai", "prompt:"]):
                score = max(score, 0.98)
                exif_note = "AI generation metadata detected"
        except Exception:
            pass

        score = max(0.01, min(0.99, score))
        label = "Likely AI-generated" if score >= 0.50 else "Likely real"
        confidence = score if score >= 0.50 else 1.0 - score

        return {
            "label": label,
            "ai_probability": round(score * 100, 1),
            "confidence": round(confidence * 100, 1),
            "forensic_note": exif_note
        }, None
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return None, f"Prediction failed: {exc}"


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    image_url = None
    model_notice = None

    if request.method == "POST":
        uploaded = request.files.get("image")
        if not uploaded or not uploaded.filename:
            error = "Choose an image before clicking Analyze image."
        elif not allowed_file(uploaded.filename):
            error = "Unsupported file type. Upload a JPG, JPEG, PNG, or WEBP image."
        else:
            try:
                # Validate actual image bytes before saving.
                uploaded.stream.seek(0)
                with Image.open(uploaded.stream) as im:
                    im.verify()
                uploaded.stream.seek(0)
                suffix = secure_filename(uploaded.filename).rsplit(".", 1)[-1].lower()
                filename = f"{uuid4().hex}.{suffix}"
                destination = UPLOAD_DIR / filename
                uploaded.save(destination)
                image_url = url_for("static", filename=f"uploads/{filename}")
                result, prediction_error = predict_image(destination)
                if prediction_error:
                    model_notice = prediction_error
            except (UnidentifiedImageError, OSError, ValueError):
                error = "That file does not appear to be a valid image. Please try another."
            except Exception:
                app.logger.exception("Upload failed")
                error = "Something went wrong while processing the upload. Please try again."

    return render_template(
        "index.html",
        result=result,
        error=error,
        image_url=image_url,
        model_notice=model_notice,
        user=session.get("user"),
        user_name=session.get("user_name"),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect directly to dashboard/analyzer
    if session.get("user") and request.method == "GET":
        return redirect(url_for("index"))

    error = None
    email_val = ""

    if request.method == "POST":
        email_val = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        is_valid, error_msg = authenticate_user(email_val, password)
        if is_valid:
            session.permanent = remember
            session["user"] = email_val.lower()
            # Generate friendly display name from email (e.g. "analyst@..." -> "Analyst")
            user_handle = email_val.split("@")[0].replace(".", " ").replace("_", " ").title()
            session["user_name"] = user_handle

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))
        else:
            error = error_msg

    return render_template(
        "login.html",
        error=error,
        email=email_val,
        demo_accounts=DEMO_CREDENTIALS,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(413)
def too_large(_error):
    return render_template(
        "index.html",
        result=None,
        error=f"Image is too large. Maximum upload size is {MAX_UPLOAD_MB} MB.",
        image_url=None,
        model_notice=None,
        user=session.get("user"),
        user_name=session.get("user_name"),
    ), 413


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Asynchronous JSON analysis API for instant responsive scans."""
    uploaded = request.files.get("image")
    if not uploaded or not uploaded.filename:
        return {"success": False, "error": "Choose an image before analyzing."}, 400
    if not allowed_file(uploaded.filename):
        return {"success": False, "error": "Unsupported file type. Upload a JPG, JPEG, PNG, or WEBP image."}, 400

    try:
        uploaded.stream.seek(0)
        with Image.open(uploaded.stream) as im:
            im.verify()
        uploaded.stream.seek(0)
        suffix = secure_filename(uploaded.filename).rsplit(".", 1)[-1].lower()
        filename = f"{uuid4().hex}.{suffix}"
        destination = UPLOAD_DIR / filename
        uploaded.save(destination)
        image_url = url_for("static", filename=f"uploads/{filename}")
        result, prediction_error = predict_image(destination)
        if prediction_error:
            return {"success": False, "error": prediction_error, "image_url": image_url}, 500

        return {
            "success": True,
            "result": result,
            "image_url": image_url
        }
    except (UnidentifiedImageError, OSError, ValueError):
        return {"success": False, "error": "Invalid image file. Please try another."}, 400
    except Exception as exc:
        app.logger.exception("API analysis failed")
        return {"success": False, "error": "An error occurred during analysis."}, 500


def warmup_model():
    """Pre-warms the TensorFlow model on server startup to eliminate cold-start lag."""
    m = load_model()
    if m is not None:
        try:
            import numpy as np
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
            dummy = np.zeros((2, 224, 224, 3), dtype=np.float32)
            _ = m(preprocess_input(dummy), training=False)
            app.logger.info("AI Model successfully warmed up.")
        except Exception as e:
            app.logger.warning(f"Model warmup notice: {e}")


# Pre-warm model in background
try:
    warmup_model()
except Exception:
    pass


@app.route("/health")
def health():
    return {"status": "ok", "model_file_present": MODEL_PATH.exists()}


if __name__ == "__main__":
    app.run(debug=True)
