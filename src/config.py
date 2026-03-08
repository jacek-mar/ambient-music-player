import sys
import os
from pathlib import Path

APP_NAME = "Ambient Music Player"
APP_INTERNAL_NAME = "AmbientMusicPlayer"
APP_VERSION = "1.0.0"

def _get_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_INTERNAL_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

DATA_DIR = _get_data_dir()
DB_PATH = DATA_DIR / "music.db"
LOG_PATH = DATA_DIR / "app.log"

DEFAULT_VOLUME = 0.7
DEFAULT_SERVER_PORT = 8080

STATE_SAVE_INTERVAL = 5

STYLE_DARK = """
QMainWindow {
    background-color: #1E1E2E;
    color: #E5E7EB;
}
QWidget {
    background-color: #1E1E2E;
    color: #E5E7EB;
}
QPushButton {
    background-color: #2A2A3E;
    border: 1px solid #4B5563;
    border-radius: 4px;
    padding: 6px 12px;
    color: #E5E7EB;
}
QPushButton:hover {
    background-color: #7C3AED;
}
QPushButton:pressed {
    background-color: #6D28D9;
}
QSlider::groove:horizontal {
    background: #2A2A3E;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #7C3AED;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background: #7C3AED;
    border-radius: 3px;
}
QComboBox {
    background-color: #2A2A3E;
    border: 1px solid #4B5563;
    border-radius: 4px;
    padding: 4px 8px;
    color: #E5E7EB;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #9CA3AF;
}
QLabel {
    color: #E5E7EB;
}
QProgressBar {
    background-color: #2A2A3E;
    border: none;
    border-radius: 3px;
    height: 8px;
}
QProgressBar::chunk {
    background-color: #7C3AED;
    border-radius: 3px;
}
"""
