# Pencil Sketch Studio

A local Flask web application that turns JPG, JPEG, PNG, BMP, and WebP photos into grayscale pencil sketches. It shows the original and result side by side and provides a PNG download.

## Requirements

- Python 3.10 or newer
- pip

## Install and run

Open a terminal in this project directory.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. Alternatively, use Command Prompt and activate with `.venv\Scripts\activate.bat`.

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. The development server is started with debug mode disabled.

## Use

1. Select a JPG, JPEG, PNG, BMP, or WebP image.
2. Adjust the Gaussian blur kernel from 5 to 51. The value is always odd; larger values produce broader, softer shading.
3. Select **Generate Pencil Sketch** to see both images.
4. Select **Download Sketch (PNG)** to save the generated image.

Uploads are limited to 10 MB and 20 megapixels. The original photo is decoded and previewed in memory; it is not written to disk. Generated PNGs are written to the `generated` directory with random UUID-based names.

## Troubleshooting

- **`pip` or package installation fails:** Confirm that Python 3.10+ is installed and that the virtual environment is active. Upgrade pip with `python -m pip install --upgrade pip`, then retry `pip install -r requirements.txt`.
- **OpenCV cannot be imported:** Install dependencies in the same active environment used to run the app. The project uses the headless OpenCV package, which does not require desktop GUI libraries.
- **An image is rejected:** Confirm that its file extension matches a real, readable JPG/JPEG, PNG, BMP, or WebP image. Animated or damaged images may not decode as a standard still image. Reduce the image to no more than 20 megapixels and 10 MB.
- **The upload is too large:** Resize or recompress the source photo before uploading. The web server also applies a request-size limit.
- **Port 5000 is in use:** Stop the other process using that port, or run the app with a different port by changing the `app.run` call at the bottom of `app.py`.

## Deployment and maintenance

For production, run Flask behind a production WSGI server and HTTPS reverse proxy; do not use Flask's development server. Configure the proxy and WSGI server upload limits consistently with the application's limit. Add per-client rate limiting (for example, with Flask-Limiter), request timeouts, and monitoring before exposing the app publicly. The `generated` directory can grow over time: schedule a cleanup job that removes old generated PNGs according to your retention policy, taking care not to delete files currently being downloaded. Keep the directory non-public and writable only by the application account.
