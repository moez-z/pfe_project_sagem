"""
ui/pages/corrections_page.py
-----------------------------
Corrections page — shows every TX block that requires an EEPROM correction.

The NOTE column now contains an "Apply Correction" button instead of plain
text.  Clicking it:
  1. Opens a file-picker if no path_loss.csv is loaded yet (or re-uses the
     last one).
  2. Looks up the cable / path-loss for the block's frequency + antenna.
  3. Displays a confirmation dialog with the computed corrected value.
  4. On confirmation the button turns into a green "✔ Applied" label and
     the row is updated with the corrected origin value.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QFileDialog, QMessageBox, QTableWidgetItem,
    QSizePolicy,
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

from ui.widgets import (
    CalibrationTable, MetricCard,
    mono_item, make_band_item, status_item,
)
from ui import styles

# Path-loss helper (new module)
try:
    from core.path_loss import PathLossTable
    _PATH_LOSS_AVAILABLE = True
except ImportError:
    _PATH_LOSS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Column layout
# ---------------------------------------------------------------------------

_COLUMNS = [
    "BAND", "BLK", "FREQ (MHz)", "MOD", "BW", "ANT",
    "ORIGIN dBm", "DUT dBm", "DELTA", "CORRECTION TO APPLY", "STATUS", "NOTE",
]

# Convenience indices
_COL_BAND   = 0
_COL_BLK    = 1
_COL_FREQ   = 2
_COL_MOD    = 3
_COL_BW     = 4
_COL_ANT    = 5
_COL_ORIGIN = 6
_COL_DUT    = 7
_COL_DELTA  = 8
_COL_CORR   = 9
_COL_STATUS = 10
_COL_NOTE   = 11


# ---------------------------------------------------------------------------
# Small helper — read-only label used after a correction is applied
# ---------------------------------------------------------------------------

def _applied_label(text: str = "✔ Applied", color: str = "#00C853") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    lbl.setStyleSheet(
        f"color: {color}; background: transparent; padding: 2px 6px;"
    )
    return lbl


# ---------------------------------------------------------------------------
# CorrectionsPage
# ---------------------------------------------------------------------------

class CorrectionsPage(QWidget):
    """Corrections page widget."""

    # Emitted when a correction is successfully applied
    # payload: dict with the same keys as get_corrections() items
    correction_applied = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._corrections: list[dict] = []
        self._path_loss_table: Optional["PathLossTable"] = None
        self._path_loss_path: str = ""
        # Track application state per row: row_index → bool
        self._applied: dict[str, bool] = {}
        self._build_ui()

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)

        # ── Header info row ──────────────────────────────────────────────────
        info_row = QHBoxLayout()
        info_row.setSpacing(10)

        self._c_count = MetricCard("CORRECTIONS", "0", "TX blocks")
        self._c_band5 = MetricCard("5 GHz",  "0", "blocks")
        self._c_band2 = MetricCard("2.4 GHz", "0", "blocks")
        self._c_band6 = MetricCard("6 GHz",  "0", "blocks")
        for card in [self._c_count, self._c_band5, self._c_band2, self._c_band6]:
            info_row.addWidget(card)
        info_row.addStretch()

        # ── Path-loss load button ────────────────────────────────────────────
        self._pl_btn = QPushButton("📂 Load path_loss.csv")
        self._pl_btn.setToolTip("Load the cable/path-loss CSV file used for correction")
        self._pl_btn.setFixedHeight(32)
        self._pl_btn.setStyleSheet(
            "QPushButton {"
            f"  background: black;"
            f"  color: {styles.TEXT_PRI};"
            "  border: 1px solid #444;"
            "  border-radius: 4px;"
            "  padding: 0 12px;"
            "  font-size: 11px;"
            "}"
            "QPushButton:hover { border-color: #00BCD4; color: #00BCD4; }"
        )
        self._pl_btn.clicked.connect(self._load_path_loss)
        info_row.addWidget(self._pl_btn)

        self._pl_status_lbl = QLabel("No path-loss file loaded")
        self._pl_status_lbl.setStyleSheet(
            f"color: {styles.TEXT_SEC}; font-size: 10px;"
        )
        info_row.addWidget(self._pl_status_lbl)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._export_csv)
        info_row.addWidget(self._export_btn)

        root.addLayout(info_row)

        # ── Correction table ─────────────────────────────────────────────────
        self._table = CalibrationTable(_COLUMNS)
        widths = [72, 40, 90, 72, 60, 55, 95, 95, 90, 130, 120, 200]
        for i, w in enumerate(widths):
            self._table.setColumnWidth(i, w)
        root.addWidget(self._table)

        # ── Text summary ─────────────────────────────────────────────────────
        lbl = QLabel("CORRECTION SUMMARY")
        lbl.setObjectName("section_header")
        root.addWidget(lbl)

        self._summary_box = QTextEdit()
        self._summary_box.setReadOnly(True)
        self._summary_box.setMaximumHeight(140)
        self._summary_box.setFont(QFont("Cascadia Code, Consolas", 11))
        self._summary_box.setStyleSheet(
            f"background-color: {styles.BG_BASE}; "
            f"color: {styles.C_WARN}; "
            f"border: 1px solid {styles.C_WARN};"
        )
        self._summary_box.setPlaceholderText(
            "No corrections needed — or run calibration first."
        )
        root.addWidget(self._summary_box)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def load_corrections(self, corrections: list[dict], tolerance: float) -> None:
        """
        Populate the page with the corrections produced by
        ``CalibrationEngine.get_corrections()``.

        Parameters
        ----------
        corrections : list[dict]
            Each dict has the keys returned by ``get_corrections()``.
        tolerance : float
            The TX tolerance (dBm) that was used during calibration.
        """
        self._corrections = corrections
        self._applied.clear()
        self._populate_table(corrections)
        self._update_metrics(corrections)
        self._build_summary(corrections, tolerance)
        self._export_btn.setEnabled(bool(corrections))

    def set_path_loss_file(self, filepath: str) -> None:
        """
        Pre-load a path-loss file programmatically (e.g. from settings).
        """
        self._do_load_path_loss(filepath)

    # -----------------------------------------------------------------------
    # Path-loss loading
    # -----------------------------------------------------------------------

    def _load_path_loss(self) -> None:
        """Open a file dialog and load the selected CSV."""
        start_dir = (
            str(Path(self._path_loss_path).parent)
            if self._path_loss_path else ""
        )
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select path_loss.csv",
            start_dir,
            "CSV files (*.csv);;All files (*.*)",
        )
        if path:
            self._do_load_path_loss(path)

    def _do_load_path_loss(self, path: str) -> None:
        if not _PATH_LOSS_AVAILABLE:
            QMessageBox.critical(
                self, "Module missing",
                "core.path_loss module is not available.\n"
                "Make sure core/path_loss.py exists.",
            )
            return

        try:
            table = PathLossTable.load(path)
        except Exception as exc:
            QMessageBox.critical(
                self, "Load error",
                f"Could not load path-loss file:\n{exc}",
            )
            return

        self._path_loss_table = table
        self._path_loss_path  = path
        fname = Path(path).name
        n = len(table)
        self._pl_status_lbl.setText(f"✔ {fname}  ({n} freq entries)")
        self._pl_status_lbl.setStyleSheet(
            "color: #00C853; font-size: 10px; font-weight: bold;"
        )
        self._pl_btn.setText(f"📂 {fname}")

        # Refresh buttons in the table so they become active
        self._refresh_note_buttons()

    # -----------------------------------------------------------------------
    # Table population
    # -----------------------------------------------------------------------

    def _populate_table(self, corrections: list[dict]) -> None:
        self._table.setSortingEnabled(False)
        self._table.clear_rows()
        self._table.setHorizontalHeaderLabels(_COLUMNS)

        for row_idx, c in enumerate(corrections):
            delta = c.get("delta_dbm")
            corr  = c.get("correction_dbm")

            delta_s = f"{delta:+.2f}" if delta is not None else "—"
            corr_s  = f"{corr:+.2f}" if corr is not None else "—"

            delta_item_ = mono_item(delta_s)
            if delta is not None:
                delta_item_.setForeground(
                    styles.cell_color_warn() if abs(delta) > 0.3
                    else QColor(styles.TEXT_PRI)
                )

            corr_item = mono_item(corr_s)
            corr_item.setForeground(styles.cell_color_warn())
            corr_item.setBackground(styles.cell_bg_warn())
            corr_item.setFont(
                QFont("Cascadia Code, Consolas", 11, QFont.Weight.Bold)
            )

            self._table.add_row([
                make_band_item(c.get("band", "")),
                mono_item(str(c.get("label", "").split(".")[0])),
                mono_item(str(c.get("freq_mhz", ""))),
                mono_item(c.get("modulation", "")),
                mono_item(c.get("bandwidth", "")),
                mono_item(c.get("antenna", "")),
                mono_item(f"{c.get('origin_measured_dbm', 0):.2f}"),
                mono_item(f"{c.get('dut_measured_dbm', 0):.2f}"),
                delta_item_,
                corr_item,
                status_item(c.get("status", "")),
                # NOTE column — placeholder item (button set below)
                mono_item(""),
            ])

            # Place the "Apply Correction" button in the NOTE column
            self._set_note_button(row_idx, c)

        self._table.setSortingEnabled(True)

    def _set_note_button(self, row: int, correction: dict) -> None:
        """
        Insert an 'Apply Correction' button into the NOTE cell for *row*.
        If the correction has already been applied, show the applied label.
        """
        if self._applied.get(row):
            self._table.setCellWidget(row, _COL_NOTE, _applied_label())
            return

        btn = QPushButton("⚡ Apply Correction")
        btn.setFixedHeight(26)
        btn.setToolTip(
            f"Apply correction of {correction.get('correction_dbm', 0):+.3f} dBm\n"
            f"for {correction.get('label', '')}"
        )
        btn.setStyleSheet(
            "QPushButton {"
            "  background: #1565C0;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 4px;"
            "  padding: 0 10px;"
            "  font-size: 10px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover  { background: #1976D2; }"
            "QPushButton:pressed { background: #0D47A1; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )

        # Capture loop variable with default argument
        btn.clicked.connect(
            lambda _checked, r=row, c=correction: self._on_apply_correction(r, c)
        )
        self._table.setCellWidget(row, _COL_NOTE, btn)

    def _refresh_note_buttons(self) -> None:
        """Re-create all NOTE buttons (called after a path-loss file is loaded)."""
        for row_idx, c in enumerate(self._corrections):
            if not self._applied.get(row_idx):
                self._set_note_button(row_idx, c)

    # -----------------------------------------------------------------------
    # Correction logic
    # -----------------------------------------------------------------------

    def _on_apply_correction(self, row: int, correction: dict) -> None:
        """
        Called when the user clicks "Apply Correction" for a specific row.

        Steps
        -----
        1. Resolve path-loss value (load file if not done yet).
        2. Compute corrected origin value = origin_measured + correction_dbm
           (optionally adjusted by path loss).
        3. Show confirmation dialog.
        4. Mark row as applied, replace button with ✔ label.
        """
        # ── 1. Ensure a path-loss file is loaded ─────────────────────────────
        if self._path_loss_table is None:
            reply = QMessageBox.question(
                self,
                "Path-loss file required",
                "No path-loss CSV file is loaded.\n\n"
                "Would you like to select one now?\n"
                "(Click 'No' to apply correction without path-loss compensation.)",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No  |
                QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self._load_path_loss()
                # If user cancelled the file dialog, path_loss_table is still None
                # → proceed without it

        # ── 2. Build correction info ──────────────────────────────────────────
        freq_mhz      = correction.get("freq_mhz", 0)
        antenna       = correction.get("antenna", "")
        origin_dbm    = correction.get("origin_measured_dbm", 0.0) or 0.0
        dut_dbm       = correction.get("dut_measured_dbm", 0.0) or 0.0
        delta_dbm     = correction.get("delta_dbm", 0.0) or 0.0
        correction_dbm = correction.get("correction_dbm", 0.0) or 0.0
        label          = correction.get("label", "")

        # Path-loss lookup
        path_loss: Optional[float] = None
        if self._path_loss_table is not None:
            path_loss = self._path_loss_table.get_loss(freq_mhz, antenna)

        # Corrected value to write to EEPROM
        # = correction_dbm  (+ path_loss if available, as an informational note)
        eeprom_correction = correction_dbm
        path_loss_note = ""
        if path_loss is not None:
            path_loss_note = (
                f"\n  Path-loss ({freq_mhz} MHz / {antenna}): "
                f"{path_loss:+.2f} dBm"
            )

        # ── 3. Confirmation dialog ────────────────────────────────────────────
        details = (
            f"Block  : {label}\n"
            f"Band   : {correction.get('band', '')}\n"
            f"Freq   : {freq_mhz} MHz\n"
            f"Antenna: {antenna}\n"
            f"\n"
            f"Origin measured : {origin_dbm:+.3f} dBm\n"
            f"DUT measured    : {dut_dbm:+.3f} dBm\n"
            f"Delta           : {delta_dbm:+.3f} dBm\n"
            f"\n"
            f"EEPROM correction to apply: {eeprom_correction:+.3f} dBm"
            f"{path_loss_note}\n"
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("Apply EEPROM Correction")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(
            f"<b>Apply correction for block:</b><br>"
            f"<code>{label}</code>"
        )
        msg.setInformativeText(
            f"EEPROM correction: <b>{eeprom_correction:+.3f} dBm</b>"
            + (f"<br>Path-loss: <b>{path_loss:+.2f} dBm</b>" if path_loss is not None else "")
        )
        msg.setDetailedText(details)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Apply)

        result = msg.exec()

        if result != QMessageBox.StandardButton.Apply:
            return

       # ── 4. Apply correction to path-loss file ─────────────────

        updated_loss = None
        backup_path = None

        try:
            if self._path_loss_table is not None:
                # Create automatic backup
                backup_path = self._path_loss_table.backup()

                # Apply correction in memory
                updated_loss = self._path_loss_table.apply_correction(
                    freq_mhz=freq_mhz,
                    antenna=antenna,
                    correction_db=correction_dbm,
                )

                # Save updated CSV
                self._path_loss_table.save()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Correction failed",
                f"Could not update path-loss file:\n\n{exc}",
            )
            return

        # Mark row as applied
        self._applied[label] = True

        # Replace button with green label
        applied_lbl = _applied_label(
            f"✔ Applied ({correction_dbm:+.3f} dBm)"
        )

        self._table.setCellWidget(row, _COL_NOTE, applied_lbl)

        # Update correction dict
        correction["path_loss_db"] = updated_loss
        correction["applied"] = True
        correction["eeprom_correction_dbm"] = correction_dbm

        # Emit signal
        self.correction_applied.emit(correction)

        # Update summary
        self._mark_applied_in_summary(label, correction_dbm)

        # Success dialog
        msg_text = (
            f"Path-loss file updated successfully.\n\n"
            f"Updated value: {updated_loss:.3f} dB"
        )

        if backup_path:
            msg_text += f"\nBackup saved to:\n{backup_path}"

        QMessageBox.information(
            self,
            "Correction Applied",
            msg_text,
        )

    def _mark_applied_in_summary(self, label: str, value: float) -> None:
        """Append an 'Applied' note to the summary text box."""
        current = self._summary_box.toPlainText()
        marker = f"\n  ✔ APPLIED: {label}  →  {value:+.3f} dBm"
        if marker not in current:
            self._summary_box.setPlainText(current + marker)

    # -----------------------------------------------------------------------
    # Metrics update
    # -----------------------------------------------------------------------

    def _update_metrics(self, corrections: list[dict]) -> None:
        self._c_count.set_value(str(len(corrections)))
        self._c_band5.set_value(
            str(sum(1 for c in corrections if c.get("band") == "5 GHz"))
        )
        self._c_band2.set_value(
            str(sum(1 for c in corrections if c.get("band") == "2.4 GHz"))
        )
        self._c_band6.set_value(
            str(sum(1 for c in corrections if c.get("band") == "6 GHz"))
        )

    # -----------------------------------------------------------------------
    # Summary text
    # -----------------------------------------------------------------------

    def _build_summary(self, corrections: list[dict], tolerance: float) -> None:
        if not corrections:
            self._summary_box.setPlainText(
                f"✓  No corrections needed at tolerance = {tolerance} dBm.\n"
                "   All TX blocks are within the acceptable range."
            )
            self._summary_box.setStyleSheet(
                f"background-color: {styles.C_PASS_BG}; "
                f"color: {styles.C_PASS}; "
                f"border: 1px solid {styles.C_PASS};"
            )
            return

        lines = [
            f"EEPROM CALIBRATION CORRECTIONS  (tolerance = {tolerance} dBm)",
            "─" * 60,
        ]
        for c in corrections:
            corr = c.get("correction_dbm", 0)
            lines.append(
                f"  {c['label']:<40}  "
                f"delta={c['delta_dbm']:+.3f} dBm  →  "
                f"correction = {corr:+.3f} dBm"
            )
        lines += [
            "─" * 60,
            f"Total: {len(corrections)} block(s) require correction.",
        ]
        self._summary_box.setPlainText("\n".join(lines))
        self._summary_box.setStyleSheet(
            f"background-color: {styles.BG_BASE}; "
            f"color: {styles.C_WARN}; "
            f"border: 1px solid {styles.C_WARN};"
        )

    # -----------------------------------------------------------------------
    # CSV export
    # -----------------------------------------------------------------------

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export corrections", "eeprom_corrections.csv",
            "CSV files (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "label", "band", "freq_mhz", "modulation", "bandwidth",
                "antenna", "origin_measured_dbm", "dut_measured_dbm",
                "delta_dbm", "correction_dbm", "status", "warning",
                "path_loss_db", "applied",
            ])
            for c in self._corrections:
                writer.writerow([
                    c.get("label"),
                    c.get("band"),
                    c.get("freq_mhz"),
                    c.get("modulation"),
                    c.get("bandwidth"),
                    c.get("antenna"),
                    c.get("origin_measured_dbm"),
                    c.get("dut_measured_dbm"),
                    c.get("delta_dbm"),
                    c.get("correction_dbm"),
                    c.get("status"),
                    c.get("warning"),
                    c.get("path_loss_db", ""),
                    c.get("applied", False),
                ])
