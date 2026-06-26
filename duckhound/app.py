"""GUI entry point for DuckHound."""
from __future__ import annotations

import datetime as _dt
import faulthandler
import sys
import traceback

from PySide6.QtCore import Qt, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .config import Settings, _config_dir

LOG_PATH = _config_dir() / "duckhound.log"


def _log(line: str) -> None:
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(f"{_dt.datetime.now().isoformat(timespec='seconds')}  {line}\n")
    except Exception:
        pass


def _install_diagnostics() -> None:
    """Make crashes leave a trace instead of vanishing."""
    try:
        faulthandler.enable(open(LOG_PATH, "a"))
    except Exception:
        pass

    def _excepthook(exc_type, exc, tb):
        _log("UNCAUGHT EXCEPTION:\n" + "".join(
            traceback.format_exception(exc_type, exc, tb)))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook

    def _qt_handler(mode, _ctx, message):
        _log(f"Qt[{int(mode)}]: {message}")

    qInstallMessageHandler(_qt_handler)
    _log(f"--- DuckHound {__version__} starting (py{sys.version_info.major}."
         f"{sys.version_info.minor}, {sys.platform}) ---")


def main() -> int:
    demo = "--demo" in sys.argv
    _install_diagnostics()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)

    from .ui.main_window import build_window
    settings = Settings.load()
    try:
        win = build_window(settings, demo=demo)
        win.show()
    except Exception:
        _log("FATAL during startup:\n" + traceback.format_exc())
        raise
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
