"""
ui/pages/path_loss_page.py
--------------------------
Path Loss Viewer page.

Features:
  - Load a path_loss.csv file via Browse button or drag-and-drop
  - Display all entries in a styled table (FREQ, ANT1, ANT2, ANT3, ANT4)
  - Metric cards: total entries, 2.4 GHz count, 5 GHz count, 6 GHz count
  - Inline editing of loss values (double-click a cell)
  - Save changes back to the CSV
  - Export a copy to a new location
  - Color-code rows by frequency band
  - Status bar shows the loaded file path
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QLineEdit, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QDragEnterEvent, QDropEvent

from ui import styles
from ui.widgets import MetricCard


# ---------------------------------------------------------------------------
# Column layout
# ---------------------------------------------------------------------------

_COLUMNS = ["FREQ (MHz)", "ANT1 (dB)", "ANT2 (dB)", "ANT3 (dB)", "ANT4 (dB)", "BAND"]
_COL_FREQ  = 0
_COL_ANT1  = 1
_COL_ANT2  = 2
_COL_ANT3  = 3
_COL_ANT4  = 4
_COL_BAND  = 5

_MONO = QFont("Cascadia Code, JetBrains Mono, Consolas", 11)
_MONO_BOLD = QFont("Cascadia Code, JetBrains Mono, Consolas", 11, QFont.Weight.Bold)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _band_from_freq(freq: int) -> str:
    if 2400 <= freq <= 2500:
        return "2.4 GHz"
    if 4900 <= freq <= 5900:
        return "5 GHz"
    if 5925 <= freq <= 7125:
        return "6 GHz"
    return "Unknown"


def _band_color(band: str) -> QColor:
    mapping = {
        "2.4 GHz": QColor(styles.C_2G),
        "5 GHz":   QColor(styles.C_5G),
        "6 GHz":   QColor(styles.C_6G),
    }
    return mapping.get(band, QColor(styles.TEXT_SEC))


def _loss_color(value: float) -> QColor:
    """Color-code loss value: green=low, yellow=mid, red=high."""
    if value < 4.0:
        return QColor(styles.C_PASS)
    if value < 7.0:
        return QColor(styles.C_WARN)
    return QColor(styles.C_FAIL)


def _make_item(text: str, editable: bool = False,
               color: Optional[QColor] = None,
               bold: bool = False,
               align=Qt.AlignmentFlag.AlignCenter) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFont(_MONO_BOLD if bold else _MONO)
    item.setTextAlignment(align)
    if color:
        item.setForeground(color)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


# ---------------------------------------------------------------------------
# PathLossPage
# ---------------------------------------------------------------------------

class PathLossPage(QWidget):
    """
    Standalone page for viewing, editing and saving path_loss.csv.
    Emits ``file_loaded(path)`` whenever a new file is successfully loaded,
    so CorrectionsPage can be notified automatically.
    """

    file_loaded = pyqtSignal(str)   # absolute path to the loaded CSV

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._filepath: str = ""
        self._rows: list[dict] = []   # list of {freq, ant1..4}
        self._unsaved: bool = False
        self.setAcceptDrops(True)
        self._build_ui()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)

        # ── Top toolbar ──────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText(
            "No file loaded — click Browse or drag & drop a path_loss.csv here"
        )
        self._path_edit.setFont(QFont("Cascadia Code, Consolas", 10))
        self._path_edit.setStyleSheet(
            f"background: {styles.BG_RAISED}; "
            f"color: {styles.TEXT_SEC}; "
            f"border: 1px solid {styles.BORDER}; "
            f"padding: 5px 10px;"
        )
        toolbar.addWidget(self._path_edit, 1)

        self._browse_btn = QPushButton("📂  Browse…")
        self._browse_btn.setFixedHeight(34)
        self._browse_btn.setToolTip("Open a path_loss.csv file")
        self._browse_btn.clicked.connect(self._browse)
        toolbar.addWidget(self._browse_btn)

        self._save_btn = QPushButton("💾  Save")
        self._save_btn.setFixedHeight(34)
        self._save_btn.setEnabled(False)
        self._save_btn.setObjectName("btn_primary")
        self._save_btn.setToolTip("Save changes back to the loaded file")
        self._save_btn.clicked.connect(self._save)
        toolbar.addWidget(self._save_btn)

        self._export_btn = QPushButton("⬆  Export CSV")
        self._export_btn.setFixedHeight(34)
        self._export_btn.setEnabled(False)
        self._export_btn.setToolTip("Save a copy to a new location")
        self._export_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(self._export_btn)

        self._add_btn = QPushButton("＋  Add Row")
        self._add_btn.setFixedHeight(34)
        self._add_btn.setEnabled(False)
        self._add_btn.setToolTip("Insert a new frequency row")
        self._add_btn.clicked.connect(self._add_row)
        toolbar.addWidget(self._add_btn)

        self._del_btn = QPushButton("✕  Delete Row")
        self._del_btn.setFixedHeight(34)
        self._del_btn.setEnabled(False)
        self._del_btn.setToolTip("Delete the selected row")
        self._del_btn.clicked.connect(self._delete_row)
        toolbar.addWidget(self._del_btn)

        root.addLayout(toolbar)

        # ── Drag hint label ──────────────────────────────────────────────────
        self._drag_hint = QLabel(
            "⬇  Drag & drop a  path_loss.csv  file anywhere on this page"
        )
        self._drag_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drag_hint.setStyleSheet(
            f"color: {styles.TEXT_DIM}; "
            f"font-size: 11px; "
            f"border: 1px dashed {styles.BORDER_LO}; "
            f"padding: 6px;"
        )
        root.addWidget(self._drag_hint)

        # ── Metric cards ─────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self._c_total = MetricCard("TOTAL ENTRIES", "0", "frequencies")
        self._c_2g    = MetricCard("2.4 GHz", "0", "entries", "metric_card_pass",
                                   "metric_value_pass")
        self._c_5g    = MetricCard("5 GHz",   "0", "entries", "metric_card_accent",
                                   "metric_value_accent")
        self._c_6g    = MetricCard("6 GHz",   "0", "entries")

        for card in [self._c_total, self._c_2g, self._c_5g, self._c_6g]:
            cards_row.addWidget(card)
        cards_row.addStretch()

        self._unsaved_lbl = QLabel("")
        self._unsaved_lbl.setStyleSheet(
            f"color: {styles.C_WARN}; font-size: 11px; font-weight: bold;"
        )
        cards_row.addWidget(self._unsaved_lbl)

        root.addLayout(cards_row)

        # ── Section header ───────────────────────────────────────────────────
        hdr = QLabel("PATH LOSS TABLE")
        hdr.setObjectName("section_header")
        root.addWidget(hdr)

        # ── Info label ───────────────────────────────────────────────────────
        info = QLabel(
            "💡  Double-click any ANT cell to edit its loss value.  "
            "Click  Save  to persist changes."
        )
        info.setStyleSheet(
            f"color: {styles.TEXT_SEC}; font-size: 11px; padding: 2px 0;"
        )
        root.addWidget(info)

        # ── Main table ───────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked
        )
        self._table.setShowGrid(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.setWordWrap(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._table.setSortingEnabled(True)
        self._table.itemChanged.connect(self._on_item_changed)

        # Column widths
        col_widths = [130, 110, 110, 110, 110, 120]
        for i, w in enumerate(col_widths):
            self._table.setColumnWidth(i, w)

        root.addWidget(self._table, 1)

        # ── Status bar ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {styles.BORDER_LO};")
        root.addWidget(sep)

        self._status_lbl = QLabel("No file loaded.")
        self._status_lbl.setStyleSheet(
            f"color: {styles.TEXT_SEC}; font-size: 10px; "
            f"font-family: Cascadia Code, Consolas; padding: 2px 0;"
        )
        root.addWidget(self._status_lbl)

    # -----------------------------------------------------------------------
    # Drag & drop
    # -----------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".csv"):
                event.acceptProposedAction()
                self._drag_hint.setStyleSheet(
                    f"color: {styles.ACCENT}; "
                    f"font-size: 11px; "
                    f"border: 1px dashed {styles.ACCENT}; "
                    f"padding: 6px;"
                )
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._drag_hint.setStyleSheet(
            f"color: {styles.TEXT_DIM}; "
            f"font-size: 11px; "
            f"border: 1px dashed {styles.BORDER_LO}; "
            f"padding: 6px;"
        )

    def dropEvent(self, event: QDropEvent) -> None:
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(".csv"):
                self._load_file(path)

    # -----------------------------------------------------------------------
    # File I/O
    # -----------------------------------------------------------------------

    def _browse(self) -> None:
        start = str(Path(self._filepath).parent) if self._filepath else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open path_loss.csv", start,
            "CSV files (*.csv);;All files (*.*)"
        )
        if path:
            self._load_file(path)

    def load_file(self, path: str) -> None:
        """Public API — load a file programmatically."""
        self._load_file(path)

    def _load_file(self, path: str) -> None:
        """Parse and display the CSV."""
        rows: list[dict] = []
        warnings: list[str] = []

        try:
            with open(path, newline="", encoding="utf-8-sig") as fh:
                reader = csv.reader(fh)
                for lineno, raw in enumerate(reader, start=1):
                    # Strip blanks / comments
                    row = [c.strip() for c in raw]
                    # Drop trailing empty fields
                    while row and row[-1] == "":
                        row.pop()
                    if not row:
                        continue
                    # Skip comment lines
                    if row[0].startswith("#"):
                        continue
                    # First column must be a frequency integer
                    try:
                        freq = int(row[0])
                    except ValueError:
                        warnings.append(
                            f"Line {lineno}: skipped (freq not integer): {row}"
                        )
                        continue
                    # Parse up to 4 antenna losses
                    losses: list[Optional[float]] = []
                    for i in range(1, 5):
                        if i < len(row):
                            try:
                                losses.append(float(row[i]))
                            except ValueError:
                                losses.append(None)
                        else:
                            losses.append(None)
                    rows.append({
                        "freq": freq,
                        "ant1": losses[0],
                        "ant2": losses[1],
                        "ant3": losses[2],
                        "ant4": losses[3],
                    })

        except Exception as exc:
            QMessageBox.critical(self, "Load error",
                                 f"Could not read file:\n{exc}")
            return

        if not rows:
            QMessageBox.warning(
                self, "Empty file",
                "The selected CSV contains no valid data rows."
            )
            return

        self._filepath = path
        self._rows     = rows
        self._unsaved  = False

        self._path_edit.setText(path)
        self._path_edit.setStyleSheet(
            f"background: {styles.BG_RAISED}; "
            f"color: {styles.TEXT_PRI}; "
            f"border: 1px solid {styles.BORDER}; "
            f"padding: 5px 10px;"
        )

        self._populate_table()
        self._update_metrics()
        self._update_buttons(enabled=True)
        self._unsaved_lbl.setText("")

        n = len(rows)
        warn_txt = f"  ⚠ {len(warnings)} line(s) skipped" if warnings else ""
        self._status_lbl.setText(
            f"Loaded: {path}  •  {n} entr{'y' if n == 1 else 'ies'}{warn_txt}"
        )

        # Notify other pages
        self.file_loaded.emit(path)

    def _save(self) -> None:
        """Flush table edits back to self._rows then write to CSV."""
        if not self._filepath:
            self._export_csv()
            return

        self._flush_table_to_rows()

        try:
            self._write_csv(self._filepath)
        except Exception as exc:
            QMessageBox.critical(self, "Save error",
                                 f"Could not write file:\n{exc}")
            return

        self._unsaved = False
        self._unsaved_lbl.setText("")
        self._save_btn.setEnabled(False)
        self._status_lbl.setText(f"Saved: {self._filepath}")

    def _export_csv(self) -> None:
        start = str(Path(self._filepath).parent) if self._filepath else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export path_loss.csv", start or "path_loss.csv",
            "CSV files (*.csv)"
        )
        if not path:
            return
        self._flush_table_to_rows()
        try:
            self._write_csv(path)
        except Exception as exc:
            QMessageBox.critical(self, "Export error",
                                 f"Could not write file:\n{exc}")
            return
        self._status_lbl.setText(f"Exported to: {path}")

    def _write_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([
                "# path_loss.csv",
            ])
            writer.writerow([
                "# freq_mhz", "loss_ant1(dB)", "loss_ant2(dB)",
                "loss_ant3(dB)", "loss_ant4(dB)"
            ])
            for r in sorted(self._rows, key=lambda x: x["freq"]):
                writer.writerow([
                    r["freq"],
                    _fmt(r["ant1"]),
                    _fmt(r["ant2"]),
                    _fmt(r["ant3"]),
                    _fmt(r["ant4"]),
                ])

    # -----------------------------------------------------------------------
    # Table population
    # -----------------------------------------------------------------------

    def _populate_table(self) -> None:
        # Block signals while repopulating to avoid spurious _on_item_changed
        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for r in self._rows:
            self._insert_row(r)

        self._table.setSortingEnabled(True)
        self._table.blockSignals(False)

    def _insert_row(self, r: dict) -> int:
        """Insert one data row; return the row index."""
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setRowHeight(row, 32)

        freq = r["freq"]
        band = _band_from_freq(freq)
        bc   = _band_color(band)

        # FREQ — not editable
        freq_item = _make_item(str(freq), editable=False,
                               color=bc, bold=True)
        self._table.setItem(row, _COL_FREQ, freq_item)

        # ANT1..ANT4 — editable
        for col, key in [(_COL_ANT1, "ant1"), (_COL_ANT2, "ant2"),
                         (_COL_ANT3, "ant3"), (_COL_ANT4, "ant4")]:
            val = r.get(key)
            txt = f"{val:.2f}" if val is not None else "—"
            color = _loss_color(val) if val is not None else QColor(styles.TEXT_DIM)
            item = _make_item(txt, editable=True, color=color)
            self._table.setItem(row, col, item)

        # BAND — not editable
        band_item = _make_item(band, editable=False, color=bc)
        self._table.setItem(row, _COL_BAND, band_item)

        return row

    # -----------------------------------------------------------------------
    # Metrics
    # -----------------------------------------------------------------------

    def _update_metrics(self) -> None:
        total = len(self._rows)
        n2g = sum(1 for r in self._rows if _band_from_freq(r["freq"]) == "2.4 GHz")
        n5g = sum(1 for r in self._rows if _band_from_freq(r["freq"]) == "5 GHz")
        n6g = sum(1 for r in self._rows if _band_from_freq(r["freq"]) == "6 GHz")

        self._c_total.set_value(str(total))
        self._c_2g.set_value(str(n2g))
        self._c_5g.set_value(str(n5g))
        self._c_6g.set_value(str(n6g))

    # -----------------------------------------------------------------------
    # Row add / delete
    # -----------------------------------------------------------------------

    def _add_row(self) -> None:
        """Append a blank editable row."""
        new = {"freq": 0, "ant1": 0.0, "ant2": 0.0, "ant3": 0.0, "ant4": 0.0}
        self._rows.append(new)
        self._table.blockSignals(True)
        self._insert_row(new)
        self._table.blockSignals(False)

        # Make the freq cell editable for the new row so user can type it
        last = self._table.rowCount() - 1
        freq_item = self._table.item(last, _COL_FREQ)
        if freq_item:
            freq_item.setFlags(freq_item.flags() | Qt.ItemFlag.ItemIsEditable)

        self._table.scrollToBottom()
        self._table.setCurrentCell(last, _COL_FREQ)
        self._table.editItem(self._table.item(last, _COL_FREQ))
        self._mark_unsaved()
        self._update_metrics()

    def _delete_row(self) -> None:
        rows_selected = sorted(
            {idx.row() for idx in self._table.selectedIndexes()},
            reverse=True
        )
        if not rows_selected:
            return

        reply = QMessageBox.question(
            self, "Delete rows",
            f"Delete {len(rows_selected)} selected row(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._table.blockSignals(True)
        for row in rows_selected:
            self._table.removeRow(row)
        self._table.blockSignals(False)

        self._flush_table_to_rows()
        self._update_metrics()
        self._mark_unsaved()

    # -----------------------------------------------------------------------
    # Edit handling
    # -----------------------------------------------------------------------

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        col = item.column()
        if col == _COL_BAND:
            return   # auto-computed, ignore

        # Validate numeric input for ANT columns
        if col in (_COL_ANT1, _COL_ANT2, _COL_ANT3, _COL_ANT4):
            try:
                val = float(item.text().replace(",", "."))
                item.setText(f"{val:.2f}")
                item.setForeground(_loss_color(val))
            except ValueError:
                item.setText("—")
                item.setForeground(QColor(styles.TEXT_DIM))

        # Update BAND cell if FREQ changed
        if col == _COL_FREQ:
            try:
                freq = int(item.text())
                band = _band_from_freq(freq)
                bc   = _band_color(band)
                item.setForeground(bc)
                band_item = self._table.item(item.row(), _COL_BAND)
                if band_item:
                    band_item.setText(band)
                    band_item.setForeground(bc)
            except ValueError:
                pass

        self._mark_unsaved()

    def _flush_table_to_rows(self) -> None:
        """Read current table content back into self._rows."""
        self._rows.clear()
        for row in range(self._table.rowCount()):
            def cell(col) -> str:
                item = self._table.item(row, col)
                return item.text().strip() if item else ""

            try:
                freq = int(cell(_COL_FREQ))
            except ValueError:
                continue

            def parse_loss(col) -> Optional[float]:
                txt = cell(col)
                try:
                    return float(txt)
                except ValueError:
                    return None

            self._rows.append({
                "freq": freq,
                "ant1": parse_loss(_COL_ANT1),
                "ant2": parse_loss(_COL_ANT2),
                "ant3": parse_loss(_COL_ANT3),
                "ant4": parse_loss(_COL_ANT4),
            })

    # -----------------------------------------------------------------------
    # State helpers
    # -----------------------------------------------------------------------

    def _mark_unsaved(self) -> None:
        self._unsaved = True
        self._unsaved_lbl.setText("⚠  Unsaved changes")
        self._save_btn.setEnabled(bool(self._filepath))

    def _update_buttons(self, enabled: bool) -> None:
        self._save_btn.setEnabled(False)   # only enabled after edits
        self._export_btn.setEnabled(enabled)
        self._add_btn.setEnabled(enabled)
        self._del_btn.setEnabled(enabled)

    # -----------------------------------------------------------------------
    # Public helpers
    # -----------------------------------------------------------------------

    def current_filepath(self) -> str:
        """Return the path of the currently loaded file (or empty string)."""
        return self._filepath


# ---------------------------------------------------------------------------
# Small formatting helper
# ---------------------------------------------------------------------------

def _fmt(val: Optional[float]) -> str:
    return f"{val:.2f}" if val is not None else ""
