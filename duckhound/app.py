"""GUI entry point for DuckHound."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .config import Settings


def main() -> int:
    demo = "--demo" in sys.argv

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)

    from .ui.main_window import build_window
    settings = Settings.load()
    win = build_window(settings, demo=demo)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
