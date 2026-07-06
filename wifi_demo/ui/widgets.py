from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QFontMetrics
from ui import styles
# ── Horizontal rule ───────────────────────────────────────────────────────────
class HLine(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setFixedHeight(1)
        self.setStyleSheet(f"color: {styles.ACCENT_DARK};")  # #025091
# ── Section header label ──────────────────────────────────────────────────────
class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setObjectName("section_header")
        # section_header in QSS already sets color: ACCENT (#71C5EE)
# ── Metric card ───────────────────────────────────────────────────────────────
class MetricCard(QWidget):
    """
    A small card showing a single KPI.
    Supported style_name values:
      "metric_card"        — blue border-top (default)
      "metric_card_pass"   — green
      "metric_card_fail"   — red
      "metric_card_accent" — light-blue (Saint Petersburg)
    """
    def __init__(self, label: str, value: str = "—",
                 sub: str = "", style_name: str = "metric_card",
                 value_name: str = "metric_value",
                 parent=None):
        super().__init__(parent)
        self.setObjectName(style_name)
        self.setMinimumWidth(130)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)
        self._lbl = QLabel(label.upper())
        self._lbl.setObjectName("metric_label")
        self._val = QLabel(value)
        self._val.setObjectName(value_name)
        self._sub = QLabel(sub)
        self._sub.setObjectName("metric_sub")
        layout.addWidget(self._lbl)
        layout.addWidget(self._val)
        layout.addWidget(self._sub)
    def set_value(self, value: str):
        self._val.setText(value)
    def set_sub(self, sub: str):
        self._sub.setText(sub)
# ── File path picker ──────────────────────────────────────────────────────────
class FilePathPicker(QWidget):
    path_changed = pyqtSignal(str)
    def __init__(self, label: str, placeholder: str = "",
                 filter_str: str = "Log files (*.log);;All files (*)",
                 parent=None):
        super().__init__(parent)
        self._filter = filter_str
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFixedWidth(90)
        lbl.setObjectName("metric_label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setReadOnly(True)
        btn = QPushButton("Browse…")
        btn.setFixedWidth(90)
        btn.clicked.connect(self._browse)
        row.addWidget(lbl)
        row.addWidget(self._edit, 1)
        row.addWidget(btn)
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select log file", "", self._filter
        )
        if path:
            self._edit.setText(path)
            self.path_changed.emit(path)
    def path(self) -> str:
        return self._edit.text()
    def set_path(self, path: str):
        self._edit.setText(path)
# ── Band badge label ──────────────────────────────────────────────────────────
def make_band_item(band_value: str) -> QTableWidgetItem:
    item = QTableWidgetItem(band_value)
    item.setForeground(styles.band_color(band_value))
    item.setFont(QFont("Cascadia Code, JetBrains Mono, Consolas", 11))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item
# ── Monospace data cell ───────────────────────────────────────────────────────
def mono_item(text: str,
              align=Qt.AlignmentFlag.AlignCenter,
              color: QColor = None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFont(QFont("Cascadia Code, JetBrains Mono, Consolas", 11))
    item.setTextAlignment(align)
    if color:
        item.setForeground(color)
    return item
# ── Status cell (PASS / FAIL / WARN / N/A) ───────────────────────────────────
def status_item(status_str: str) -> QTableWidgetItem:
    item = QTableWidgetItem(status_str)
    item.setFont(QFont("Cascadia Code, JetBrains Mono, Consolas", 11, QFont.Weight.Bold))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    s = status_str.upper()
    if "PASS" in s or s == "OK":
        item.setForeground(styles.cell_color_pass())
        item.setBackground(styles.cell_bg_pass())
    elif "FAIL" in s:
        item.setForeground(styles.cell_color_fail())
        item.setBackground(styles.cell_bg_fail())
    elif "CORR" in s or "WARN" in s:
        # Now blue instead of amber
        item.setForeground(styles.cell_color_warn())   # #71C5EE
        item.setBackground(styles.cell_bg_warn())      # #021830
    else:
        item.setForeground(styles.cell_color_invalid())
    return item
# ── Delta cell (coloured by sign / magnitude) ─────────────────────────────────
def delta_item(delta: float, threshold: float = 0.5) -> QTableWidgetItem:
    sign = "+" if delta >= 0 else ""
    text = f"{sign}{delta:.3f}"
    item = QTableWidgetItem(text)
    item.setFont(QFont("Cascadia Code, JetBrains Mono, Consolas", 11))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    abs_d = abs(delta)
    if abs_d > threshold:
        # Out of tolerance → light blue highlight (was amber)
        item.setForeground(styles.cell_color_warn())   # #71C5EE
        item.setBackground(styles.cell_bg_warn())      # #021830
    elif abs_d > threshold * 0.5:
        item.setForeground(QColor(styles.TEXT_PRI))
    else:
        item.setForeground(QColor(styles.TEXT_SEC))
    return item
# ── Base calibration table ────────────────────────────────────────────────────
class CalibrationTable(QTableWidget):
    def __init__(self, columns: list[str], parent=None):
        super().__init__(0, len(columns), parent)
        self.setHorizontalHeaderLabels(columns)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.setShowGrid(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        self.setWordWrap(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    def clear_rows(self):
        self.setRowCount(0)
    def add_row(self, cells: list[QTableWidgetItem]):
        row = self.rowCount()
        self.insertRow(row)
        for col, item in enumerate(cells):
            if item is not None:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row, col, item)
        self.setRowHeight(row, 30)

