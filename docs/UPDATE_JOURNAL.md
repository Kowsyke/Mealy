# Mealy Development Journal

---

## v1.0 — Live Server Deployment (2026-04-23)

**Status: Live at https://56-228-34-22.sslip.io/mealy/**

### What was deployed
- Flask API running locally on Fedora Linux (port 5001)
- SSH reverse tunnel (`mealy-tunnel.service`) forwards EC2 port 5001 → local Flask
- Nginx on EC2 proxies `/mealy/` to the tunnel, `/` to the Kowsite Node.js server
- HTTPS via Let's Encrypt certificate for `56-228-34-22.sslip.io` (auto-renews every 90 days)
- HTTP → HTTPS redirect for all incoming traffic
- AWS Security Group updated to allow inbound TCP 443

### Kowsite integration
- MEALY node card added to Kowsite sidebar under "Clients" section
- Full-screen iframe panel (below 48px header) loads `/mealy/` on first click
- `allow="camera;microphone"` on iframe enables camera delegation over HTTPS
- Fedora agent (`kowsite-agent.service`) updated to connect via `wss://` (required after HTTPS)

### Services (all systemd user units, auto-start on login)
| Service | Purpose |
|---------|---------|
| `mealy-api.service` | Starts the Flask API on port 5001 |
| `mealy-tunnel.service` | Opens the SSH reverse tunnel to EC2 |
| `kowsite-agent.service` | Sends Fedora system metrics to Kowsite dashboard |

### Camera permission fix
- Root cause: `getUserMedia()` requires HTTPS — was silently blocked on plain HTTP
- Fix: sslip.io wildcard DNS (`56-228-34-22.sslip.io` → `56.228.34.22`) + certbot

### UI improvements
- Camera status pill in System section is now a toggle button (click on/off)
- Camera container height constrained so controls never get pushed off screen
- Left panel uses `overflow-y: auto` so it scrolls on short viewports
- Footer kowsite link updated to the HTTPS URL

### Documentation generated
- `docs/mealy_project_guide.docx` — 16-step teacher guide (~22 pages)
  - Covers: setup, datasets, data pipeline, model, training, API, frontend,
    SSH tunnel, systemd, nginx, HTTPS, Kowsite integration, glossary, screenshot list

---

## v0.9 — Full Pipeline Complete (2026-04-22)

### Model & training
- `train_optimized.py` — full-resolution Food-101 retrain (was previously upscaled 64px HDF5)
- Two-phase training: Phase 1 (20 epochs, frozen base, lr=1e-3) + Phase 2 (30 epochs, top-30 unfrozen, lr=1e-5)
- Fixed `preprocess.py`: removed `.numpy()` call inside `tf.data.Dataset.map()` (graph mode incompatibility)
- Fixed `load_data.py`: replaced `tf.keras.layers.RandomRotation/Zoom` (create tf.Variables in tf.function → forbidden) with stateless `tf.image.random_crop` + `tf.image.resize`
- Training running in tmux session `mealy-train` on Fedora

### API
- Dual-model system: `/detect` (Food-101), `/detect_fruit` (Fruit-360), `/detect_combined` (both)
- Lazy model loading — Flask starts in ~0.35s, models load on first request
- `/health` endpoint returns model load status and class counts

### Frontend
- Three-column glass UI: left panel (system/model/stats), centre (camera feed), right (detection cards)
- Auto-scan mode (2s interval)
- Session stats (scans, items found, average confidence)
- Calorie total counter

### Kowsite (first integration attempt)
- Mealy panel and card added to Kowsite frontend
- Initial iframe pointed to `http://localhost:5001` — fixed to `/mealy/` (relative, inherits HTTPS)

### Git cleanup
- Stripped all "Co-Authored-By: Claude Sonnet" lines from every commit using `git filter-branch`
- Force-pushed; all commits show only Kowsyke | abirmia205@gmail.com

---

## v0.5 — Dual Model System (2026-04-22)

- Added Fruit-360 subset (36 classes) alongside Food-101
- `fruit_classes.py`, `fruit_classes.json`, `fruit_calories.py` added
- Combined detection mode merges results from both models
- Fine-tuned fruit model achieves 96.7% top-1 accuracy
- Desktop launcher (`launch.py`) using PyQt6 WebEngine

---

## v0.4 — Flask API & Web UI (2026-04-22)

- `app.py` — Flask REST API with CORS, image upload, JSON response
- `detect.py` — inference wrapper, top-k filtering above 15% confidence
- `calories.py` — 101-entry calorie lookup table
- `ui/index.html` — single-file web frontend (camera + detection cards)
- `start_api.sh` — tmux-based API keepalive script

---

## v0.3 — Dataset Setup

- Downloaded Food-101 dataset (~5 GB, 101,000 JPEG images)
- Confirmed dataset structure: `images/`, `meta/classes.txt`, `meta/train.txt`, `meta/test.txt`
- 75,750 training images, 25,250 test images across 101 classes

---

## v0.2 — Environment Setup

- Python 3.12.13 virtualenv at `venv_archive/`
- TensorFlow 2.21.0, Keras 3.13.2, Flask, Flask-CORS, Pillow, OpenCV, NumPy
- `requirements.txt` generated (pinned versions)

---

## v0.1 — Project Setup

- Created project directory structure
- Initialised Git repository, connected to GitHub
- Added documentation files and project plan
