"""
styles.py — Global QSS stylesheet with dark/light theme support.
"""
import json, os

# ── Theme persistence ─────────────────────────────────────────────────────────
_PREFS_FILE = os.path.join(os.path.dirname(__file__), "..", "app_config.json")
_DARK_MODE  = True  # default

def load_theme_pref():
    global _DARK_MODE
    try:
        with open(_PREFS_FILE) as f:
            _DARK_MODE = json.load(f).get("dark_mode", True)
    except Exception:
        _DARK_MODE = True

def save_theme_pref(dark: bool):
    global _DARK_MODE
    _DARK_MODE = dark
    try:
        data = {}
        try:
            with open(_PREFS_FILE) as f:
                data = json.load(f)
        except Exception:
            pass
        data["dark_mode"] = dark
        with open(_PREFS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def is_dark() -> bool:
    return _DARK_MODE

load_theme_pref()

# ── Dark theme tokens ─────────────────────────────────────────────────────────
DARK = dict(
    BG_BASE      = "#060D18",
    BG_SURFACE   = "#0A1628",
    BG_RAISED    = "#0F1F3D",
    BG_HOVER     = "#163060",
    BORDER       = "#1A3A6A",
    BORDER_LO    = "#0D2040",
    ACCENT       = "#71C5EE",
    ACCENT_DIM   = "#042A50",
    ACCENT_DARK  = "#025091",
    TEXT_PRI     = "#E0EFFF",
    TEXT_SEC     = "#5A8AB0",
    TEXT_DIM     = "#1A3050",
    C_PASS       = "#2ECC71",
    C_PASS_BG    = "#0A2018",
    C_FAIL       = "#E74C3C",
    C_FAIL_BG    = "#220A0A",
    C_WARN       = "#71C5EE",
    C_WARN_BG    = "#021830",
    C_INVALID    = "#2A4A6A",
    C_INVALID_BG = "#080F20",
    C_5G         = "#71C5EE",
    C_2G         = "#2ECC71",
    C_6G         = "#025091",
)

# ── Light theme tokens ────────────────────────────────────────────────────────
LIGHT = dict(
    BG_BASE      = "#F0F4F8",
    BG_SURFACE   = "#FFFFFF",
    BG_RAISED    = "#E2EAF4",
    BG_HOVER     = "#C8D8EE",
    BORDER       = "#B0C4DE",
    BORDER_LO    = "#D0DFF0",
    ACCENT       = "#025091",
    ACCENT_DIM   = "#C8DEFF",
    ACCENT_DARK  = "#1A6AAA",
    TEXT_PRI     = "#0A1628",
    TEXT_SEC     = "#3A5A80",
    TEXT_DIM     = "#8AAAC8",
    C_PASS       = "#1A8A4A",
    C_PASS_BG    = "#D4F4E2",
    C_FAIL       = "#C0392B",
    C_FAIL_BG    = "#FAD7D4",
    C_WARN       = "#025091",
    C_WARN_BG    = "#D0E8FF",
    C_INVALID    = "#7A9ABE",
    C_INVALID_BG = "#EAF0F8",
    C_5G         = "#025091",
    C_2G         = "#1A8A4A",
    C_6G         = "#6A3AAA",
)

FONT_MONO = "Cascadia Code, Consolas, Courier New, monospace"
FONT_UI   = "Segoe UI, Arial, sans-serif"

def _tokens():
    return DARK if _DARK_MODE else LIGHT

# ── Expose flat tokens (always current theme) ─────────────────────────────────
def _t(key): return _tokens()[key]

BG_BASE      = property(lambda: _t("BG_BASE"))
BG_SURFACE   = property(lambda: _t("BG_SURFACE"))

# For backward compat — used as strings in f-strings elsewhere:
def get_tokens():
    return _tokens()

# ── Build QSS ─────────────────────────────────────────────────────────────────
def build_style() -> str:
    t = _tokens()
    BG_BASE      = t["BG_BASE"]
    BG_SURFACE   = t["BG_SURFACE"]
    BG_RAISED    = t["BG_RAISED"]
    BG_HOVER     = t["BG_HOVER"]
    BORDER       = t["BORDER"]
    BORDER_LO    = t["BORDER_LO"]
    ACCENT       = t["ACCENT"]
    ACCENT_DIM   = t["ACCENT_DIM"]
    ACCENT_DARK  = t["ACCENT_DARK"]
    TEXT_PRI     = t["TEXT_PRI"]
    TEXT_SEC     = t["TEXT_SEC"]
    TEXT_DIM     = t["TEXT_DIM"]
    C_PASS       = t["C_PASS"]
    C_PASS_BG    = t["C_PASS_BG"]
    C_FAIL       = t["C_FAIL"]
    C_FAIL_BG    = t["C_FAIL_BG"]
    C_WARN       = t["C_WARN"]
    C_WARN_BG    = t["C_WARN_BG"]

    return f"""
QWidget {{
    background-color: {BG_BASE};
    color: {TEXT_PRI};
    font-family: {FONT_UI};
    font-size: 13px;
    selection-background-color: {ACCENT_DIM};
    selection-color: {ACCENT};
}}
QMainWindow {{ background-color: {BG_BASE}; }}
#sidebar {{
    background-color: {BG_SURFACE};
    border-right: 1px solid {BORDER};
    min-width: 220px; max-width: 220px;
}}
#logo_label {{
    color: {ACCENT}; font-size: 11px;
    font-family: {FONT_MONO}; letter-spacing: 3px;
    padding: 20px 16px 4px 16px;
}}
#product_label {{
    color: {TEXT_PRI}; font-size: 15px;
    font-weight: 600; padding: 0px 16px 2px 16px;
}}
#serial_label {{
    color: {TEXT_SEC}; font-size: 11px;
    font-family: {FONT_MONO}; padding: 0px 16px 16px 16px;
}}
#nav_btn {{
    background: transparent; border: none;
    border-left: 3px solid transparent;
    color: {TEXT_SEC}; text-align: left;
    padding: 10px 16px 10px 13px; font-size: 13px;
}}
#nav_btn:hover {{ background-color: {BG_RAISED}; color: {TEXT_PRI}; }}
#nav_btn[active="true"] {{
    background-color: {BG_RAISED};
    border-left: 3px solid {ACCENT};
    color: {ACCENT}; font-weight: 600;
}}
#topbar {{
    background-color: {BG_SURFACE};
    border-bottom: 1px solid {BORDER};
    min-height: 52px; max-height: 52px;
}}
#page_title {{ color: {TEXT_PRI}; font-size: 15px; font-weight: 600; }}
#status_badge {{
    font-size: 11px; font-weight: 700;
    letter-spacing: 1px; padding: 4px 12px; border-radius: 2px;
}}
#status_badge[status="pass"] {{
    background-color: {C_PASS_BG}; color: {C_PASS}; border: 1px solid {C_PASS};
}}
#status_badge[status="fail"] {{
    background-color: {C_FAIL_BG}; color: {C_FAIL}; border: 1px solid {C_FAIL};
}}
#status_badge[status="none"] {{
    background-color: {ACCENT_DIM}; color: {ACCENT}; border: 1px solid {ACCENT_DARK};
}}
#metric_card {{
    background-color: {BG_SURFACE}; border: 1px solid {BORDER};
    border-top: 2px solid {ACCENT_DARK};
}}
#metric_card_pass {{
    background-color: {C_PASS_BG}; border: 1px solid {C_PASS};
    border-top: 2px solid {C_PASS};
}}
#metric_card_fail {{
    background-color: {C_FAIL_BG}; border: 1px solid {C_FAIL};
    border-top: 2px solid {C_FAIL};
}}
#metric_card_accent {{
    background-color: {ACCENT_DIM}; border: 1px solid {ACCENT_DARK};
    border-top: 2px solid {ACCENT};
}}
#metric_label {{
    color: {TEXT_SEC}; font-size: 10px;
    letter-spacing: 1.5px; font-family: {FONT_MONO};
}}
#metric_value {{ color: {TEXT_PRI}; font-size: 26px; font-family: {FONT_MONO}; font-weight: 600; }}
#metric_value_pass {{ color: {C_PASS}; font-size: 26px; font-family: {FONT_MONO}; font-weight: 600; }}
#metric_value_fail {{ color: {C_FAIL}; font-size: 26px; font-family: {FONT_MONO}; font-weight: 600; }}
#metric_value_accent {{ color: {ACCENT}; font-size: 26px; font-family: {FONT_MONO}; font-weight: 600; }}
#metric_sub {{ color: {TEXT_DIM}; font-size: 11px; }}
QTableWidget {{
    background-color: {BG_SURFACE}; alternate-background-color: {BG_RAISED};
    border: 1px solid {BORDER}; gridline-color: {BORDER_LO};
    color: {TEXT_PRI}; font-size: 12px;
    selection-background-color: {ACCENT_DIM}; selection-color: {ACCENT};
}}
QTableWidget::item {{ padding: 5px 10px; border: none; }}
QTableWidget::item:selected {{ background-color: {ACCENT_DIM}; color: {ACCENT}; }}
QHeaderView::section {{
    background-color: {ACCENT_DARK}; color: {TEXT_PRI};
    border: none; border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    padding: 6px 10px; font-size: 11px;
    letter-spacing: 0.8px; font-family: {FONT_MONO}; font-weight: 600;
}}
QTabWidget::pane {{
    background-color: {BG_SURFACE}; border: 1px solid {BORDER}; border-top: none;
}}
QTabBar::tab {{
    background-color: {BG_BASE}; color: {TEXT_SEC};
    border: 1px solid {BORDER}; border-bottom: none;
    padding: 8px 20px; margin-right: 2px;
    font-size: 12px; font-family: {FONT_MONO};
}}
QTabBar::tab:selected {{
    background-color: {BG_SURFACE}; color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{ background-color: {BG_RAISED}; color: {TEXT_PRI}; }}
QPushButton {{
    background-color: {BG_RAISED}; color: {TEXT_PRI};
    border: 1px solid {BORDER}; padding: 8px 18px; font-size: 12px;
}}
QPushButton:hover {{ background-color: {BG_HOVER}; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:pressed {{ background-color: {ACCENT_DIM}; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:disabled {{ color: {TEXT_DIM}; border-color: {BORDER_LO}; }}
#btn_primary {{
    background-color: {ACCENT_DARK}; color: {ACCENT};
    border: 1px solid {ACCENT}; font-weight: 600;
}}
#btn_primary:hover {{ background-color: {ACCENT}; color: {BG_BASE}; }}
#btn_primary:disabled {{
    background-color: {BG_RAISED}; color: {TEXT_DIM}; border-color: {BORDER_LO};
}}
QLineEdit {{
    background-color: {BG_RAISED}; border: 1px solid {BORDER};
    color: {TEXT_PRI}; padding: 6px 10px;
    font-family: {FONT_MONO}; font-size: 12px;
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit:read-only {{ color: {TEXT_SEC}; }}
QComboBox {{
    background-color: {BG_RAISED}; border: 1px solid {BORDER};
    color: {TEXT_PRI}; padding: 5px 10px; font-size: 12px;
}}
QComboBox::drop-down {{ border-left: 1px solid {BORDER}; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {BG_RAISED}; border: 1px solid {BORDER};
    color: {TEXT_PRI}; selection-background-color: {ACCENT_DIM};
    selection-color: {ACCENT};
}}
QScrollBar:vertical {{
    background-color: {BG_BASE}; width: 8px; border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {ACCENT_DARK}; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background-color: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background-color: {BG_BASE}; height: 8px; border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {ACCENT_DARK}; min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background-color: {ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QGroupBox {{
    border: 1px solid {BORDER}; margin-top: 16px; padding-top: 8px;
    font-size: 11px; color: {ACCENT}; letter-spacing: 1px; font-family: {FONT_MONO};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 0 6px; color: {ACCENT}; background-color: {BG_BASE};
}}
QSplitter::handle {{ background-color: {ACCENT_DARK}; width: 1px; height: 1px; }}
#section_header {{
    color: {ACCENT}; font-size: 10px; letter-spacing: 2px;
    font-family: {FONT_MONO}; font-weight: 600;
    padding: 4px 0px 2px 0px; border-bottom: 1px solid {ACCENT_DARK};
}}
QDoubleSpinBox {{
    background-color: {BG_RAISED}; border: 1px solid {BORDER};
    color: {ACCENT}; padding: 5px 8px; font-family: {FONT_MONO};
    font-size: 13px; font-weight: 600;
}}
QDoubleSpinBox:focus {{ border-color: {ACCENT}; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {BG_HOVER}; border: none; width: 18px;
}}
QStatusBar {{
    background-color: {ACCENT_DARK}; color: {ACCENT};
    border-top: 1px solid {BORDER}; font-family: {FONT_MONO}; font-size: 11px;
}}
QStatusBar::item {{ border: none; }}
QToolTip {{
    background-color: {BG_RAISED}; color: {TEXT_PRI};
    border: 1px solid {ACCENT}; font-size: 12px; padding: 4px 8px;
}}
QProgressBar {{
    background-color: {BG_RAISED}; border: 1px solid {BORDER};
    color: transparent; height: 4px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ACCENT_DARK}, stop:1 {ACCENT});
}}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {BORDER}; }}
"""

# Keep APP_STYLE for backward compat (login dialog uses it)
APP_STYLE = build_style()

# ── Flat token access (backward compat) ───────────────────────────────────────
def _flat():
    return _tokens()

BG_BASE      = DARK["BG_BASE"]
BG_SURFACE   = DARK["BG_SURFACE"]
BG_RAISED    = DARK["BG_RAISED"]
BG_HOVER     = DARK["BG_HOVER"]
BORDER       = DARK["BORDER"]
BORDER_LO    = DARK["BORDER_LO"]
ACCENT       = DARK["ACCENT"]
ACCENT_DIM   = DARK["ACCENT_DIM"]
ACCENT_DARK  = DARK["ACCENT_DARK"]
TEXT_PRI     = DARK["TEXT_PRI"]
TEXT_SEC     = DARK["TEXT_SEC"]
TEXT_DIM     = DARK["TEXT_DIM"]
C_PASS       = DARK["C_PASS"]
C_PASS_BG    = DARK["C_PASS_BG"]
C_FAIL       = DARK["C_FAIL"]
C_FAIL_BG    = DARK["C_FAIL_BG"]
C_WARN       = DARK["C_WARN"]
C_WARN_BG    = DARK["C_WARN_BG"]
C_INVALID    = DARK["C_INVALID"]
C_INVALID_BG = DARK["C_INVALID_BG"]
C_5G         = DARK["C_5G"]
C_2G         = DARK["C_2G"]
C_6G         = DARK["C_6G"]

def cell_color_pass():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_PASS"])

def cell_color_fail():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_FAIL"])

def cell_color_warn():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_WARN"])

def cell_color_invalid():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_INVALID"])

def cell_bg_pass():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_PASS_BG"])

def cell_bg_fail():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_FAIL_BG"])

def cell_bg_warn():
    from PyQt6.QtGui import QColor
    return QColor(_tokens()["C_WARN_BG"])

def band_color(band_value: str):
    from PyQt6.QtGui import QColor
    t = _tokens()
    mapping = {"5 GHz": t["C_5G"], "2.4 GHz": t["C_2G"], "6 GHz": t["C_6G"]}
    return QColor(mapping.get(band_value, t["TEXT_SEC"]))