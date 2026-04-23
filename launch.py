"""
Mealy desktop launcher — native PyQt6 WebEngine window.

The QtWebEngine V4L2 camera path crashes on many Linux drivers with
"corrupt buffer" errors. This launcher bypasses it entirely:

  1. OpenCV opens /dev/video0 in a background thread (always works).
  2. A tiny HTTP server on port 5002 serves each frame as a JPEG snapshot.
  3. A script injected at DocumentCreation overrides navigator.mediaDevices
     .getUserMedia to return a canvas.captureStream() fed by those snapshots.
  4. The rest of the UI (video element, scan function, live badge) works
     unchanged — it receives a real MediaStream from the canvas.

Flask is reused if already running on port 5001 (e.g. via systemd).

Usage:
    venv_archive/bin/python3 launch.py
"""
import os
import sys
import socket
import threading
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
# Keep WebEngine from touching the real camera device at all.
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-dev-shm-usage --disable-gpu-sandbox --use-fake-ui-for-media-stream",
)

import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler

# Qt imports at module level so they initialise while Flask/camera start up.
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineScript
from PyQt6.QtCore import QUrl

PORT_FLASK = 5001
PORT_CAM   = 5002
URL        = f"http://localhost:{PORT_FLASK}"

# ── shared camera frame ───────────────────────────────────────────────────────
_frame_lock = threading.Lock()
_frame_jpeg: bytes | None = None


def _capture_loop() -> None:
    global _frame_jpeg
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if cap.isOpened():
        print("[cam] Webcam opened via OpenCV")
    else:
        print("[cam] WARNING: could not open webcam")
    while True:
        ret, frame = cap.read()
        if ret:
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if ok:
                with _frame_lock:
                    _frame_jpeg = jpeg.tobytes()
        else:
            time.sleep(0.05)


# ── JPEG snapshot server ──────────────────────────────────────────────────────
class _FrameHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        with _frame_lock:
            data = _frame_jpeg
        if data is None:
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type",   "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control",  "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass  # silence request logs


# ── camera override injected into every page before scripts run ───────────────
_CAM_JS = f"""
(function () {{
  const SNAP = 'http://localhost:{PORT_CAM}/frame.jpg';
  const FPS  = 25;

  const canvas = document.createElement('canvas');
  canvas.width  = 1280;
  canvas.height = 720;
  const ctx = canvas.getContext('2d');

  let active = true;
  function poll() {{
    if (!active) return;
    const img = new Image();
    img.onload = function () {{
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      setTimeout(poll, Math.round(1000 / FPS));
    }};
    img.onerror = function () {{ setTimeout(poll, 200); }};
    img.src = SNAP + '?t=' + Date.now();
  }}
  poll();

  // Return a fresh captureStream each time so stopCamera() + restart works.
  navigator.mediaDevices.getUserMedia = async function () {{
    return canvas.captureStream(FPS);
  }};
}})();
"""


# ── Flask ─────────────────────────────────────────────────────────────────────
def _flask_thread() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", PORT_FLASK)) == 0:
            print(f"[launch] API already running on port {PORT_FLASK} — reusing it")
            return
    print(f"[launch] Starting Flask on port {PORT_FLASK}")
    from app import app
    app.run(host="0.0.0.0", port=PORT_FLASK, debug=False, use_reloader=False)


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    # Camera capture (OpenCV, background thread)
    threading.Thread(target=_capture_loop, daemon=True).start()

    # JPEG snapshot server (background thread)
    cam_server = HTTPServer(("127.0.0.1", PORT_CAM), _FrameHandler)
    threading.Thread(target=cam_server.serve_forever, daemon=True).start()
    print(f"[cam] Snapshot server → http://localhost:{PORT_CAM}/frame.jpg")

    # Flask API (background thread)
    threading.Thread(target=_flask_thread, daemon=True).start()

    # Qt — runs on the main thread
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Mealy")

    view = QWebEngineView()
    view.setWindowTitle("Mealy")
    view.resize(1280, 820)

    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled,           True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,              True)

    # Inject camera override at DocumentCreation so it runs before the page's
    # own scripts (which call startCamera() at the bottom).
    script = QWebEngineScript()
    script.setName("mealy-cam")
    script.setSourceCode(_CAM_JS)
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    view.page().scripts().insert(script)

    view.load(QUrl(URL))
    view.show()

    print(f"[launch] Window open → {URL}")
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
