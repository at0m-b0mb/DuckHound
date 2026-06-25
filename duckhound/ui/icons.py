"""Tiny SVG icon factory.

Icons are stroke-based (Feather/Lucide style) drawn at a 24x24 viewBox and
recoloured on demand, so the whole UI can share one crisp, theme-aware set
without shipping any binary assets.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# path/markup fragments rendered inside a stroked <g>.
_PATHS: dict[str, str] = {
    "shield":  "<path d='M12 3l7 3v5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6z'/>"
               "<path d='M9 12l2 2 4-4'/>",
    "radar":   "<circle cx='12' cy='12' r='8.5'/><circle cx='12' cy='12' r='4.5'/>"
               "<path d='M12 12L18.5 7.5'/><circle cx='12' cy='12' r='1.2' fill='currentColor'/>",
    "usb":     "<path d='M12 21V5'/><path d='M9 8l3-4 3 4'/>"
               "<path d='M12 13l4-2v-2'/><circle cx='16' cy='8' r='1.4' fill='currentColor'/>"
               "<path d='M12 16l-4-2v-2'/><rect x='6.6' y='10.6' width='2.8' height='2.8' rx='.6' fill='currentColor' stroke='none'/>",
    "alert":   "<path d='M12 4l9 16H3z'/><path d='M12 10v4'/>"
               "<circle cx='12' cy='17' r='.4' fill='currentColor'/>",
    "gear":    "<circle cx='12' cy='12' r='3'/>"
               "<path d='M12 3v2.5M12 18.5V21M21 12h-2.5M5.5 12H3M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8M18.4 18.4l-1.8-1.8M7.4 7.4L5.6 5.6'/>",
    "bell":    "<path d='M6 9a6 6 0 0112 0c0 5 2 6 2 6H4s2-1 2-6z'/>"
               "<path d='M10 20a2 2 0 004 0'/>",
    "lock":    "<rect x='5' y='11' width='14' height='9' rx='2.2'/>"
               "<path d='M8 11V8a4 4 0 018 0v3'/>",
    "power":   "<path d='M12 4v7'/><path d='M7.5 7a7 7 0 109 0'/>",
    "activity":"<path d='M3 12h4l3 7 4-14 3 7h4'/>",
    "chip":    "<rect x='7' y='7' width='10' height='10' rx='2'/>"
               "<path d='M10 3v2M14 3v2M10 19v2M14 19v2M3 10h2M3 14h2M19 10h2M19 14h2'/>",
    "check":   "<path d='M5 12.5l4.5 4.5L19 7'/>",
    "x":       "<path d='M6 6l12 12M18 6L6 18'/>",
    "eye":     "<path d='M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z'/>"
               "<circle cx='12' cy='12' r='2.6'/>",
    "duck":    "<path d='M15.5 7.2a3 3 0 10-4.7 3.6c-2.8.4-5 2-5.6 4.6-.2.9.4 1.6 1.3 1.6h7.2c3 0 5.4-2.1 5.4-5.1 0-1.6-.7-3-1.8-3.9z'/>"
               "<path d='M15.8 7.4l2.6-.6-1.7 2'/>"
               "<circle cx='13.2' cy='6.7' r='.5' fill='currentColor' stroke='none'/>",
    "scan":    "<path d='M4 8V5a1 1 0 011-1h3M20 8V5a1 1 0 00-1-1h-3M4 16v3a1 1 0 001 1h3M20 16v3a1 1 0 01-1 1h-3'/>"
               "<path d='M4 12h16'/>",
}


def svg_markup(name: str, color: str = "#E9EEF9", stroke: float = 1.8) -> str:
    body = _PATHS.get(name, "")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
        f"<g fill='none' stroke='{color}' stroke-width='{stroke}' "
        f"stroke-linecap='round' stroke-linejoin='round'>{body}</g></svg>"
    )


def pixmap(name: str, color: str = "#E9EEF9", size: int = 22, stroke: float = 1.8) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg_markup(name, color, stroke).encode()))
    dpr = 2.0
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    renderer.render(p)
    p.end()
    return pm


def icon(name: str, color: str = "#E9EEF9", size: int = 22, stroke: float = 1.8) -> QIcon:
    ic = QIcon()
    ic.addPixmap(pixmap(name, color, size, stroke))
    return ic
