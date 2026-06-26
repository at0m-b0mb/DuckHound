"""Central palette + global stylesheet — "Aurora Glass" theme.

Deep near-black canvas lit by a soft cyan→indigo→violet aurora (painted by the
main window), with translucent frosted-glass cards floating over it. One source
of truth so every widget — hand-painted or QSS-styled — stays consistent.
"""
from __future__ import annotations

from PySide6.QtGui import QColor

COLORS = {
    "bg":          "#070A12",
    "bg_grad_a":   "#0C1430",
    "bg_grad_b":   "#05070E",
    "surface":     "#121A2C",
    "surface2":    "#18223A",
    "surface3":    "#212E4D",
    "stroke":      "#2B3A5A",
    "stroke_soft": "#1E2840",
    "glass":       "rgba(22, 30, 52, 0.55)",
    "glass_soft":  "rgba(28, 38, 64, 0.45)",
    "glass_brd":   "rgba(255, 255, 255, 0.08)",
    "text":        "#EAF0FB",
    "text_dim":    "#9AA8C4",
    "text_faint":  "#606E8C",
    "accent":      "#22D3EE",
    "accent2":     "#7C7BFF",
    "accent3":     "#B57BFF",
    "accent_soft": "#0E3A47",
    "ok":          "#34E1B0",
    "warn":        "#FBBF24",
    "danger":      "#FF6B86",
    "critical":    "#FF3D6A",
    "shadow":      "#04060C",
}

SEVERITY = {
    "info":     "#60A5FA",
    "low":      "#34E1B0",
    "medium":   "#FBBF24",
    "high":     "#FB923C",
    "critical": "#FF3D6A",
}

STATE_COLOR = {
    "trusted": "#34E1B0",
    "known":   "#60A5FA",
    "new":     "#FBBF24",
    "suspect": "#FB923C",
    "blocked": "#FF3D6A",
}


def c(name: str) -> QColor:
    val = COLORS.get(name, name)
    return QColor(val) if isinstance(val, str) and val.startswith("#") else QColor(name)


def rgba(name: str, alpha: float) -> str:
    """Stylesheet-safe translucent colour (Qt parses 8-digit hex as #AARRGGBB)."""
    col = c(name)
    return f"rgba({col.red()}, {col.green()}, {col.blue()}, {alpha:.3f})"


def sev_color(name: str) -> QColor:
    return QColor(SEVERITY.get(name, "#60A5FA"))


def accent_gradient(x1: float = 0, y1: float = 0, x2: float = 1, y2: float = 0) -> str:
    """The signature cyan→indigo→violet sweep, as a QSS gradient string."""
    k = COLORS
    return (f"qlineargradient(x1:{x1}, y1:{y1}, x2:{x2}, y2:{y2}, "
            f"stop:0 {k['accent']}, stop:0.55 {k['accent2']}, stop:1 {k['accent3']})")


def build_qss() -> str:
    k = COLORS
    grad = accent_gradient()
    return f"""
    * {{
        font-family: -apple-system, 'SF Pro Display', 'Segoe UI', 'Inter',
                     'Helvetica Neue', Arial, sans-serif;
        color: {k['text']};
        outline: none;
    }}
    QWidget#Root {{ background: transparent; }}

    QLabel {{ background: transparent; }}
    QLabel[role="h1"]   {{ font-size: 27px; font-weight: 800; letter-spacing: -0.3px; }}
    QLabel[role="h2"]   {{ font-size: 17px; font-weight: 700; }}
    QLabel[role="muted"]{{ color: {k['text_dim']}; font-size: 13px; }}
    QLabel[role="faint"]{{ color: {k['text_faint']}; font-size: 12px;
                           font-weight: 700; letter-spacing: 1px; }}
    QLabel[role="metric"]{{ font-size: 32px; font-weight: 800; }}

    /* Frosted-glass card surfaces */
    QFrame[card="true"] {{
        background: {k['glass']};
        border: 1px solid {k['glass_brd']};
        border-radius: 20px;
    }}
    QFrame[card="soft"] {{
        background: {k['glass_soft']};
        border: 1px solid {k['glass_brd']};
        border-radius: 16px;
    }}

    /* Buttons */
    QPushButton {{
        background: {rgba('surface2', 0.85)};
        border: 1px solid {k['stroke']};
        border-radius: 12px;
        padding: 9px 16px;
        font-size: 13px; font-weight: 600;
        color: {k['text']};
    }}
    QPushButton:hover  {{ background: {rgba('surface3', 0.9)}; border-color: {rgba('accent', 0.5)}; }}
    QPushButton:pressed{{ background: {rgba('surface', 0.9)}; }}
    QPushButton[accent="true"] {{
        background: {grad}; border: none; color: #051018; font-weight: 800;
    }}
    QPushButton[accent="true"]:hover {{ color: #000; }}
    QPushButton[danger="true"] {{
        background: {rgba('critical', 0.14)}; border: 1px solid {rgba('critical', 0.8)};
        color: {k['danger']};
    }}
    QPushButton[danger="true"]:hover {{ background: {rgba('critical', 0.26)}; }}
    QPushButton[ghost="true"] {{ background: {rgba('surface2', 0.4)};
                                 border: 1px solid {k['stroke']}; }}
    QPushButton:disabled {{ color: {k['text_faint']}; border-color: {k['stroke_soft']}; }}

    /* Inputs */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background: {rgba('surface2', 0.85)};
        border: 1px solid {k['stroke']};
        border-radius: 10px; padding: 8px 12px; selection-background-color: {k['accent']};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border-color: {k['accent']};
    }}

    QToolTip {{
        background: {k['surface3']}; color: {k['text']};
        border: 1px solid {k['stroke']}; border-radius: 8px; padding: 6px 9px;
    }}

    QMenu {{
        background: {k['surface']}; border: 1px solid {k['stroke']};
        border-radius: 10px; padding: 6px;
    }}
    QMenu::item {{ padding: 7px 18px; border-radius: 7px; }}
    QMenu::item:selected {{ background: {rgba('accent', 0.18)}; }}

    /* Scrollbars */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
    QScrollBar::handle:vertical {{
        background: {rgba('stroke', 0.9)}; border-radius: 5px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {k['accent']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
