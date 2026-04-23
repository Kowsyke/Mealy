"""
Mealy desktop launcher — native PyQt6 WebEngine window.

Usage:
    venv_archive/bin/python3 launch.py
"""
import os
import sys
import threading

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

PORT = 5001
URL  = f"http://localhost:{PORT}"


def run_flask():
    """Start Flask unless something is already listening on PORT."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", PORT)) == 0:
            print(f"[launch] API already running on port {PORT} — reusing it")
            return
    from app import app
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def wait_for_api():
    """Block until /health responds or print a dot every 2 seconds."""
    import urllib.request, time
    print(f"[launch] Waiting for API at {URL}/health", end="", flush=True)
    while True:
        try:
            urllib.request.urlopen(URL + "/health", timeout=2)
            print(" ready.", flush=True)
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(2)


def main():
    # Flask starts instantly now (no TF at module level)
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Poll until /health responds (no hard timeout — TF load can take minutes)
    wait_for_api()

    # Open the native window on the main thread
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
    from PyQt6.QtCore import QUrl

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Mealy")

    view = QWebEngineView()
    view.setWindowTitle("Mealy")
    view.resize(1280, 820)

    # Enable screen capture and remote URL access in settings
    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

    # Auto-grant camera/mic permissions via the permission signal
    page = view.page()
    def grant_permission(origin, feature):
        page.setFeaturePermission(
            origin, feature,
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        )
    page.featurePermissionRequested.connect(grant_permission)

    view.load(QUrl(URL))
    view.show()

    print(f"[launch] Window open → {URL}")
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
