"""
Mealy desktop launcher — native PyQt6 WebEngine window.

Camera starts automatically on launch with no permission dialog.
Flask is reused if already running on port 5001 (e.g. via systemd).

Usage:
    venv_archive/bin/python3 launch.py
"""
import os
import sys
import socket
import threading

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Fix V4L2 corrupt-buffer camera crash on Linux and speed up WebEngine init.
# Must be set before any Qt import.
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-dev-shm-usage --disable-gpu-sandbox --disable-setuid-sandbox",
)

# Import Qt at module level so it initialises in parallel while Flask is
# being checked / started in the background thread below.
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QUrl

PORT = 5001
URL  = f"http://localhost:{PORT}"


def _flask_thread():
    """Start Flask only if nothing is already on PORT."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", PORT)) == 0:
            print(f"[launch] API already running on port {PORT} — reusing it")
            return
    print(f"[launch] Starting Flask API on port {PORT}")
    from app import app
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def main():
    # Flask starts in background; Qt init happens on main thread simultaneously.
    threading.Thread(target=_flask_thread, daemon=True).start()

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Mealy")

    view = QWebEngineView()
    view.setWindowTitle("Mealy")
    view.resize(1280, 820)

    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

    # Auto-grant camera and microphone without a dialog box.
    page = view.page()
    def _grant(origin, feature):
        page.setFeaturePermission(
            origin, feature,
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
        )
    page.featurePermissionRequested.connect(_grant)

    # Open immediately — the JS health check handles the brief offline period.
    view.load(QUrl(URL))
    view.show()

    print(f"[launch] Window open → {URL}")
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
