from __future__ import annotations

import base64
import re
import uuid
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, abort, render_template_string, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
GENERATED_DIR = Path(__file__).resolve().parent / "generated"

# Leave room for multipart headers while enforcing the exact file limit below.
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES + 64 * 1024

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#111827">
  <title>Pencil Sketch Studio</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #182033;
      background: #f4f5f9;
      font-synthesis: none;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-width: 320px; }
    .topbar { background: #111827; color: #fff; padding: 34px 24px 38px; }
    .topbar-inner, main { width: min(100% - 40px, 1040px); margin: 0 auto; }
    h1 { margin: 0; font-size: clamp(1.65rem, 4vw, 2.25rem); letter-spacing: -.035em; }
    .tagline { color: #c3cad7; margin: 9px 0 0; font-size: 1rem; }
    main { padding: 30px 0 56px; }
    .panel, .preview-card {
      background: #fff;
      border: 1px solid #e7e9ef;
      border-radius: 16px;
      box-shadow: 0 8px 28px rgba(25, 35, 55, .06);
    }
    .upload-panel { padding: clamp(20px, 4vw, 32px); }
    h2 { font-size: 1.15rem; margin: 0 0 7px; }
    .subtext, .help { color: #697386; line-height: 1.55; }
    .subtext { margin: 0 0 22px; }
    label { display: block; font-weight: 650; margin: 18px 0 9px; }
    input[type="file"] {
      display: block;
      width: 100%;
      padding: 13px;
      border: 1px dashed #c9ced9;
      border-radius: 10px;
      background: #fafbfc;
      color: #343d50;
    }
    input[type="file"]:focus-visible, input[type="range"]:focus-visible, button:focus-visible, a:focus-visible {
      outline: 3px solid #a99af9;
      outline-offset: 3px;
    }
    .help { margin: 8px 0 0; font-size: .88rem; }
    .slider-row { display: flex; align-items: center; gap: 16px; }
    input[type="range"] { accent-color: #6e50d8; flex: 1; min-width: 0; }
    output {
      min-width: 44px;
      padding: 5px 9px;
      border-radius: 8px;
      background: #f1efff;
      color: #5139ad;
      text-align: center;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .primary, .download {
      display: inline-flex;
      justify-content: center;
      align-items: center;
      border: 0;
      border-radius: 10px;
      padding: 12px 19px;
      min-height: 46px;
      font: inherit;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      transition: background .15s ease, transform .15s ease;
    }
    .primary { margin-top: 24px; background: #6849d4; color: #fff; }
    .primary:hover { background: #5538bd; }
    .primary:active, .download:active { transform: translateY(1px); }
    .notice {
      margin: 0 0 20px;
      padding: 13px 16px;
      border-radius: 10px;
      line-height: 1.5;
    }
    .error { background: #fff0f0; color: #9b2525; border: 1px solid #f4caca; }
    .success { background: #eef8f1; color: #27613b; border: 1px solid #cce8d4; }
    .previews { margin-top: 30px; }
    .preview-heading { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin-bottom: 13px; }
    .preview-heading h2 { margin: 0; }
    .preview-heading p { color: #697386; margin: 0; font-size: .9rem; }
    .preview-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
    .preview-card { padding: 15px; min-width: 0; }
    .preview-card h3 { font-size: .98rem; margin: 0 0 12px; }
    .image-frame {
      min-height: 180px;
      display: grid;
      place-items: center;
      overflow: hidden;
      border-radius: 9px;
      background: repeating-conic-gradient(#f2f3f6 0% 25%, #fafbfc 0% 50%) 50% / 20px 20px;
    }
    .image-frame img { display: block; width: 100%; height: auto; max-height: 620px; object-fit: contain; }
    .preview-actions { display: flex; justify-content: flex-end; margin-top: 18px; }
    .download { background: #202a3c; color: white; }
    .download:hover { background: #111827; }
    footer { color: #737d8e; font-size: .84rem; text-align: center; padding: 0 20px 28px; }
    @media (max-width: 640px) {
      .topbar { padding: 27px 0 30px; }
      .topbar-inner, main { width: min(100% - 28px, 1040px); }
      main { padding-top: 19px; }
      .preview-grid { grid-template-columns: 1fr; gap: 12px; }
      .preview-card { padding: 12px; }
      .image-frame { min-height: 120px; }
      .preview-heading { align-items: flex-start; flex-direction: column; gap: 4px; }
      .primary, .download { width: 100%; }
      .preview-actions { display: block; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <h1>Pencil Sketch Studio</h1>
      <p class="tagline">Turn a favorite photo into a pencil-style sketch in seconds.</p>
    </div>
  </header>
  <main>
    {% if error %}<div class="notice error" role="alert">{{ error }}</div>{% endif %}
    {% if generated %}<div class="notice success" role="status">Your sketch is ready. Download it below or adjust the blur and generate another.</div>{% endif %}
    <section class="panel upload-panel" aria-labelledby="upload-title">
      <h2 id="upload-title">Create your sketch</h2>
      <p class="subtext">Choose a photo and adjust the pencil shading. Your original image is processed in memory and is not saved on the server.</p>
      <form method="post" enctype="multipart/form-data">
        <label for="image">Photo</label>
        <input id="image" name="image" type="file" accept=".jpg,.jpeg,.png,.bmp,.webp,image/jpeg,image/png,image/bmp,image/webp" required>
        <p class="help">JPG, JPEG, PNG, BMP, or WebP. Maximum file size 10 MB and image size 20 megapixels.</p>
        <label for="blur">Pencil shading (Gaussian blur)</label>
        <div class="slider-row">
          <input id="blur" name="blur" type="range" min="5" max="51" step="2" value="{{ blur }}" aria-describedby="blur-help">
          <output id="blur-value" for="blur">{{ blur }}</output>
        </div>
        <p class="help" id="blur-help">Higher values create softer, broader shading. Choose an odd kernel size from 5 to 51.</p>
        <button class="primary" type="submit">Generate Pencil Sketch</button>
      </form>
    </section>

    {% if generated %}
    <section class="previews" aria-labelledby="preview-title">
      <div class="preview-heading">
        <h2 id="preview-title">Your results</h2>
        <p>Original and pencil sketch</p>
      </div>
      <div class="preview-grid">
        <article class="preview-card">
          <h3>Original photo</h3>
          <div class="image-frame"><img src="{{ original_data }}" alt="Original uploaded photograph"></div>
        </article>
        <article class="preview-card">
          <h3>Pencil sketch</h3>
          <div class="image-frame"><img src="{{ sketch_data }}" alt="Generated grayscale pencil sketch"></div>
        </article>
      </div>
      <div class="preview-actions">
        <a class="download" href="{{ url_for('download_sketch', image_id=image_id) }}">Download Sketch (PNG)</a>
      </div>
    </section>
    {% endif %}
  </main>
  <footer>For best results, use a clear photo with good contrast.</footer>
  <script>
    const blurSlider = document.getElementById("blur");
    const blurValue = document.getElementById("blur-value");
    blurSlider.addEventListener("input", () => { blurValue.value = blurSlider.value; });
  </script>
</body>
</html>
"""


def render_page(
    *,
    blur: int = 21,
    error: str | None = None,
    original_data: str | None = None,
    sketch_data: str | None = None,
    image_id: str | None = None,
):
    return render_template_string(
        PAGE,
        blur=blur,
        error=error,
        generated=bool(image_id),
        original_data=original_data,
        sketch_data=sketch_data,
        image_id=image_id,
    )


def image_data_uri(image: np.ndarray, extension: str, mime_type: str) -> str:
    success, encoded = cv2.imencode(extension, image)
    if not success:
        raise ValueError("The image could not be encoded.")
    payload = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_page()

    uploaded = request.files.get("image")
    if uploaded is None or not uploaded.filename:
        return render_page(error="Choose an image file to continue."), 400

    if Path(uploaded.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        return render_page(error="Unsupported file type. Choose a JPG, JPEG, PNG, BMP, or WebP image."), 400

    try:
        blur = int(request.form.get("blur", "21"))
    except ValueError:
        return render_page(error="Blur size must be an odd number between 5 and 51."), 400
    if blur < 5 or blur > 51 or blur % 2 == 0:
        return render_page(blur=21, error="Blur size must be an odd number between 5 and 51."), 400

    image_bytes = uploaded.stream.read(MAX_UPLOAD_BYTES + 1)
    if not image_bytes:
        return render_page(blur=blur, error="The selected file is empty."), 400
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        return render_page(blur=blur, error="The image file is larger than the 10 MB limit."), 413

    try:
        encoded_input = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(encoded_input, cv2.IMREAD_COLOR)
    except cv2.error:
        app.logger.exception("OpenCV failed to decode an uploaded image.")
        return render_page(blur=blur, error="This image could not be processed. Try saving it as a standard image and uploading it again."), 400

    if image is None or image.size == 0:
        return render_page(blur=blur, error="The selected file is not a valid or supported image."), 400

    height, width = image.shape[:2]
    if width * height > MAX_IMAGE_PIXELS:
        return render_page(blur=blur, error="The image dimensions exceed the 20 megapixel limit."), 400

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        blurred = cv2.GaussianBlur(inverted, (blur, blur), 0)
        inverted_blur = 255 - blurred
        sketch = cv2.divide(gray, inverted_blur, scale=256.0)

        original_data = image_data_uri(image, ".jpg", "image/jpeg")
        sketch_success, sketch_encoded = cv2.imencode(".png", sketch)
        if not sketch_success:
            raise ValueError("The sketch could not be encoded.")
        sketch_data = "data:image/png;base64," + base64.b64encode(sketch_encoded.tobytes()).decode("ascii")

        image_id = uuid.uuid4().hex
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        (GENERATED_DIR / f"{image_id}.png").write_bytes(sketch_encoded.tobytes())
    except (cv2.error, OSError, ValueError):
        app.logger.exception("Failed to process or save the generated sketch.")
        return render_page(blur=blur, error="The sketch could not be generated right now. Please try again."), 500

    return render_page(
        blur=blur,
        original_data=original_data,
        sketch_data=sketch_data,
        image_id=image_id,
    )


@app.route("/download/<image_id>")
def download_sketch(image_id: str):
    if re.fullmatch(r"[0-9a-f]{32}", image_id) is None:
        abort(404)

    generated_root = GENERATED_DIR.resolve()
    sketch_path = GENERATED_DIR / f"{image_id}.png"
    if not sketch_path.is_file() or sketch_path.resolve().parent != generated_root:
        abort(404)
    return send_file(sketch_path, mimetype="image/png", as_attachment=True, download_name=f"pencil-sketch-{image_id}.png")


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return render_page(error="The upload is too large. Please choose an image no larger than 10 MB."), 413


if __name__ == "__main__":
    app.run(debug=False)
