"""
Mealy desktop launcher — native PyQt6 WebEngine window.

The QtWebEngine V4L2 camera path crashes on many Linux webcam drivers.
This launcher bypasses it by:
  1. Capturing frames with OpenCV (reliable on Linux).
  2. Serving each frame as a JPEG at http://localhost:5002/frame.jpg.
  3. Passing ?_cam=ocv in the URL so index.html's inline override script
     replaces navigator.mediaDevices.getUserMedia with a canvas.captureStream
     fed by those snapshots.  No QWebEngineScript injection — the inline
     script is simpler and guaranteed to run before startCamera().

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
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-dev-shm-usage --disable-gpu-sandbox",
)

import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl

PORT_FLASK = 5001
PORT_CAM   = 5002

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
            time.sleep(0.05)   # cap at ~20 FPS, leaves CPU headroom for Flask
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
        self.send_header("Content-Type",                  "image/jpeg")
        self.send_header("Content-Length",                str(len(data)))
        self.send_header("Cache-Control",                 "no-store")
        self.send_header("Access-Control-Allow-Origin",   "*")
        self.send_header("Access-Control-Allow-Methods",  "GET")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


# ── Flask ─────────────────────────────────────────────────────────────────────
def _flask_thread() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", PORT_FLASK)) == 0:
            print(f"[launch] API already running on port {PORT_FLASK} — reusing it")
            return
    print(f"[launch] Starting Flask on port {PORT_FLASK}")
    from app import app
    app.run(host="0.0.0.0", port=PORT_FLASK, debug=False, use_reloader=False)


def _wait_for_flask(timeout: float = 20.0) -> None:
    """Block until Flask is accepting TCP connections (max timeout seconds)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", PORT_FLASK)) == 0:
                print(f"[launch] Flask ready on port {PORT_FLASK}")
                return
        time.sleep(0.05)
    print(f"[launch] WARNING: Flask did not respond within {timeout}s")


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

    # Wait until Flask is accepting connections before Qt tries to load the page.
    # This prevents "api offline" caused by a race between Flask startup and the
    # initial health check that fires as soon as the page JS runs.
    _wait_for_flask()

    # Qt runs on the main thread
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Mealy")

    view = QWebEngineView()
    view.setWindowTitle("Mealy")
    view.resize(1280, 820)

    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled,            True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,  True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,               True)

    # ?_cam=ocv tells the inline override script in index.html to activate.
    # The inline script runs before startCamera() so the override is in place.
    url = f"http://localhost:{PORT_FLASK}/?_cam=ocv"
    view.load(QUrl(url))
    view.show()

    print(f"[launch] Window open → {url}")
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
