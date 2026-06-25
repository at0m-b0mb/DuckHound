"""Central palette + global stylesheet for the DuckHound UI.

A single source of truth so every widget — hand-painted or QSS-styled — shares
the same dark "security operations" look: near-black canvas, cyan→indigo
accent, and a clear severity colour ramp.
"""
from __future__ import annotations

from PySide6.QtGui import QColor

COLORS = {
    "bg":          "#0A0E17",
    "bg_grad_a":   "#0B1020",
    "bg_grad_b":   "#090C14",
    "surface":     "#111827",
    "surface2":    "#161F30",
    "surface3":    "#1C2740",
    "stroke":      "#243149",
    "stroke_soft": "#1A2335",
    "text":        "#E9EEF9",
    "text_dim":    "#94A2BC",
    "text_faint":  "#5E6C86",
    "accent":      "#22D3EE",
    "accent2":     "#6366F1",
    "accent_soft": "#0E3A47",
    "ok":          "#34D399",
    "warn":        "#FBBF24",
    "danger":      "#FF5C7A",
    "critical":    "#FF3860",
    "shadow":      "#05070C",
}

SEVERITY = {
    "info":     "#60A5FA",
    "low":      "#34D399",
    "medium":   "#FBBF24",
    "high":     "#FB923C",
    "critical": "#FF3860",
}

STATE_COLOR = {
    "trusted": "#34D399",
    "known":   "#60A5FA",
    "new":     "#FBBF24",
    "suspect": "#FB923C",
    "blocked": "#FF3860",
}


def c(name: str) -> QColor:
    return QColor(COLORS.get(name, name))


def rgba(name: str, alpha: float) -> str:
    """Stylesheet-safe translucent colour.

    Qt parses 8-digit hex as #AARRGGBB (alpha first), which silently mangles
    ``#RRGGBBAA`` tints — so always go through rgba() for transparency.
    """
    col = c(name)
    return f"rgba({col.red()}, {col.green()}, {col.blue()}, {alpha:.3f})"


def sev_color(name: str) -> QColor:
    return QColor(SEVERITY.get(name, "#60A5FA"))


def build_qss() -> str:
    k = COLORS
    return f"""
    * {{
        font-family: -apple-system, 'SF Pro Display', 'Segoe UI', 'Inter',
                     'Helvetica Neue', Arial, sans-serif;
        color: {k['text']};
        outline: none;
    }}
    QWidget#Root {{ background: {k['bg']}; }}

    QLabel {{ background: transparent; }}
    QLabel[role="h1"]   {{ font-size: 26px; font-weight: 800; }}
    QLabel[role="h2"]   {{ font-size: 17px; font-weight: 700; }}
    QLabel[role="muted"]{{ color: {k['text_dim']}; font-size: 13px; }}
    QLabel[role="faint"]{{ color: {k['text_faint']}; font-size: 12px;
                           font-weight: 600; letter-spacing: 1px; }}
    QLabel[role="metric"]{{ font-size: 32px; font-weight: 800; }}

    /* Card surfaces */
    QFrame[card="true"] {{
        background: {k['surface']};
        border: 1px solid {k['stroke_soft']};
        border-radius: 18px;
    }}
    QFrame[card="soft"] {{
        background: {k['surface2']};
        border: 1px solid {k['stroke_soft']};
        border-radius: 14px;
    }}

    /* Buttons */
    QPushButton {{
        background: {k['surface2']};
        border: 1px solid {k['stroke']};
        border-radius: 11px;
        padding: 9px 16px;
        font-size: 13px; font-weight: 600;
        color: {k['text']};
    }}
    QPushButton:hover  {{ background: {k['surface3']}; border-color: {k['accent']}; }}
    QPushButton:pressed{{ background: {k['surface']}; }}
    QPushButton[accent="true"] {{
        background: {k['accent']}; border: none; color: #04222B; font-weight: 800;
    }}
    QPushButton[accent="true"]:hover {{ background: #46E0F2; }}
    QPushButton[danger="true"] {{
        background: rgba(255,56,96,0.14); border: 1px solid {k['critical']};
        color: {k['danger']};
    }}
    QPushButton[danger="true"]:hover {{ background: rgba(255,56,96,0.24); }}
    QPushButton[ghost="true"] {{ background: transparent; border: 1px solid {k['stroke']}; }}
    QPushButton:disabled {{ color: {k['text_faint']}; border-color: {k['stroke_soft']}; }}

    /* Inputs */
    QLineEdit, QSpinBox, QComboBox {{
        background: {k['surface2']};
        border: 1px solid {k['stroke']};
        border-radius: 10px; padding: 8px 12px; selection-background-color: {k['accent']};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {k['accent']}; }}

    QToolTip {{
        background: {k['surface3']}; color: {k['text']};
        border: 1px solid {k['stroke']}; border-radius: 8px; padding: 6px 9px;
    }}

    /* Scrollbars */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
    QScrollBar::handle:vertical {{
        background: {k['stroke']}; border-radius: 5px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {k['accent']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
