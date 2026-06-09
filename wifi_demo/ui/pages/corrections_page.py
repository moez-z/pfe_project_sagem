from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QFileDialog, QMessageBox, QTableWidgetItem,
    QSizePolicy, QCheckBox,
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
# Column layout  (checkbox added as first column)
# ---------------------------------------------------------------------------

_COLUMNS = [
    "✓", "BAND", "BLK", "FREQ (MHz)", "MOD", "BW", "ANT",
    "ORIGIN dBm", "DUT dBm", "DELTA", "CORRECTION TO APPLY", "STATUS", "NOTE",
]

# Convenience indices (shifted by 1 due to checkbox column)
_COL_CHECK  = 0
_COL_BAND   = 1
_COL_BLK    = 2
_COL_FREQ   = 3
_COL_MOD    = 4
_COL_BW     = 5
_COL_ANT    = 6
_COL_ORIGIN = 7
_COL_DUT    = 8
_COL_DELTA  = 9
_COL_CORR   = 10
_COL_STATUS = 11
_COL_NOTE   = 12


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _applied_label(text: str = "✔ Applied", color: str = "#00C853") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    lbl.setStyleSheet(
        f"color: {color}; background: transparent; padding: 2px 6px;"
    )
    return lbl


def _centered_checkbox() -> QWidget:
    """Return a QCheckBox centered inside a QWidget for table cell use."""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    cb = QCheckBox()
    layout.addWidget(cb)
    return container


# ---------------------------------------------------------------------------
# CorrectionsPage
# ---------------------------------------------------------------------------

class CorrectionsPage(QWidget):
    """Corrections page widget."""

    correction_applied = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._corrections: list[dict] = []
        self._path_loss_table: Optional["PathLossTable"] = None
        self._path_loss_path: str = ""
        self._applied: dict[str, bool] = {}
        self._select_all_state: bool = False
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

        # ── Selection action row ─────────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self._select_all_btn = QPushButton("☐  Select All")
        self._select_all_btn.setFixedHeight(30)
        self._select_all_btn.setStyleSheet(
            "QPushButton {"
            "  background: #263238;"
            f"  color: {styles.TEXT_PRI};"
            "  border: 1px solid #455A64;"
            "  border-radius: 4px;"
            "  padding: 0 12px;"
            "  font-size: 11px;"
            "}"
            "QPushButton:hover { border-color: #00BCD4; color: #00BCD4; }"
        )
        self._select_all_btn.clicked.connect(self._toggle_select_all)
        action_row.addWidget(self._select_all_btn)

        self._apply_selected_btn = QPushButton("⚡ Apply Selected")
        self._apply_selected_btn.setFixedHeight(30)
        self._apply_selected_btn.setEnabled(False)
        self._apply_selected_btn.setStyleSheet(
            "QPushButton {"
            "  background: #1B5E20;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 4px;"
            "  padding: 0 16px;"
            "  font-size: 11px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover  { background: #2E7D32; }"
            "QPushButton:pressed { background: #1B5E20; }"
            "QPushButton:disabled { background: #333; color: #666; }"
        )
        self._apply_selected_btn.clicked.connect(self._on_apply_selected)
        action_row.addWidget(self._apply_selected_btn)

        self._selection_lbl = QLabel("0 rows selected")
        self._selection_lbl.setStyleSheet(
            f"color: {styles.TEXT_SEC}; font-size: 10px;"
        )
        action_row.addWidget(self._selection_lbl)
        action_row.addStretch()

        root.addLayout(action_row)

        # ── Correction table ─────────────────────────────────────────────────
        self._table = CalibrationTable(_COLUMNS)
        widths = [32, 72, 40, 90, 72, 60, 55, 95, 95, 90, 130, 120, 200]
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
        self._corrections = corrections
        self._applied.clear()
        self._select_all_state = False
        self._select_all_btn.setText("☐  Select All")
        self._populate_table(corrections)
        self._update_metrics(corrections)
        self._build_summary(corrections, tolerance)
        self._export_btn.setEnabled(bool(corrections))
        self._update_selection_label()

    def set_path_loss_file(self, filepath: str) -> None:
        self._do_load_path_loss(filepath)

    # -----------------------------------------------------------------------
    # Selection helpers
    # -----------------------------------------------------------------------

    def _get_checkbox(self, row: int) -> Optional[QCheckBox]:
        """Return the QCheckBox widget for a given row, or None."""
        container = self._table.cellWidget(row, _COL_CHECK)
        if container is None:
            return None
        cb = container.findChild(QCheckBox)
        return cb

    def _toggle_select_all(self) -> None:
        self._select_all_state = not self._select_all_state
        label = "☑  Deselect All" if self._select_all_state else "☐  Select All"
        self._select_all_btn.setText(label)

        for row in range(self._table.rowCount()):
            # Skip already-applied rows
            if self._applied.get(self._corrections[row].get("label", row)):
                continue
            cb = self._get_checkbox(row)
            if cb:
                cb.setChecked(self._select_all_state)

        self._update_selection_label()

    def _update_selection_label(self) -> None:
        count = self._count_selected()
        self._selection_lbl.setText(f"{count} row{'s' if count != 1 else ''} selected")
        self._apply_selected_btn.setEnabled(count > 0)

    def _count_selected(self) -> int:
        count = 0
        for row in range(self._table.rowCount()):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                count += 1
        return count

    def _get_selected_rows(self) -> list[tuple[int, dict]]:
        """Return list of (row_index, correction_dict) for checked rows."""
        selected = []
        for row in range(self._table.rowCount()):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                selected.append((row, self._corrections[row]))
        return selected

    # -----------------------------------------------------------------------
    # Path-loss loading
    # -----------------------------------------------------------------------

    def _load_path_loss(self) -> None:
        start_dir = (
            str(Path(self._path_loss_path).parent)
            if self._path_loss_path else ""
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Select path_loss.csv", start_dir,
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
            QMessageBox.critical(self, "Load error",
                                 f"Could not load path-loss file:\n{exc}")
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
                QTableWidgetItem(""),       # placeholder for checkbox column
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
                mono_item(""),
            ])

            # Place checkbox widget in column 0
            cb_widget = _centered_checkbox()
            cb = cb_widget.findChild(QCheckBox)
            if cb:
                cb.stateChanged.connect(lambda _s: self._update_selection_label())
            self._table.setCellWidget(row_idx, _COL_CHECK, cb_widget)

            # Place apply button in NOTE column
            self._set_note_button(row_idx, c)

        self._table.setSortingEnabled(True)

    def _set_note_button(self, row: int, correction: dict) -> None:
        if self._applied.get(correction.get("label", row)):
            self._table.setCellWidget(row, _COL_NOTE, _applied_label())
            # Disable & uncheck checkbox for applied rows
            cb = self._get_checkbox(row)
            if cb:
                cb.setChecked(False)
                cb.setEnabled(False)
            return

        btn = QPushButton("⚡ Apply Correction")
        btn.setFixedHeight(26)
        btn.setToolTip(
            f"Apply correction of {correction.get('correction_dbm', 0):+.2f} dBm\n"
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
        btn.clicked.connect(
            lambda _checked, r=row, c=correction: self._on_apply_correction(r, c)
        )
        self._table.setCellWidget(row, _COL_NOTE, btn)

    def _refresh_note_buttons(self) -> None:
        for row_idx, c in enumerate(self._corrections):
            if not self._applied.get(c.get("label", row_idx)):
                self._set_note_button(row_idx, c)

    # -----------------------------------------------------------------------
    # Single correction
    # -----------------------------------------------------------------------

    def _on_apply_correction(self, row: int, correction: dict) -> None:
        if self._path_loss_table is None:
            reply = QMessageBox.question(
                self, "Path-loss file required",
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

        freq_mhz       = correction.get("freq_mhz", 0)
        antenna        = correction.get("antenna", "")
        origin_dbm     = correction.get("origin_measured_dbm", 0.0) or 0.0
        dut_dbm        = correction.get("dut_measured_dbm", 0.0) or 0.0
        delta_dbm      = correction.get("delta_dbm", 0.0) or 0.0
        correction_dbm = correction.get("correction_dbm", 0.0) or 0.0
        label          = correction.get("label", "")

        path_loss: Optional[float] = None
        if self._path_loss_table is not None:
            path_loss = self._path_loss_table.get_loss(freq_mhz, antenna)

        path_loss_note = ""
        if path_loss is not None:
            path_loss_note = (
                f"\n  Path-loss ({freq_mhz} MHz / {antenna}): "
                f"{path_loss:+.2f} dBm"
            )

        details = (
            f"Block  : {label}\n"
            f"Band   : {correction.get('band', '')}\n"
            f"Freq   : {freq_mhz} MHz\n"
            f"Antenna: {antenna}\n\n"
            f"Origin measured : {origin_dbm:+.2f} dBm\n"
            f"DUT measured    : {dut_dbm:+.2f} dBm\n"
            f"Delta           : {delta_dbm:+.2f} dBm\n\n"
            f"EEPROM correction to apply: {correction_dbm:+.2f} dBm"
            f"{path_loss_note}\n"
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("Apply EEPROM Correction")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(f"<b>Apply correction for block:</b><br><code>{label}</code>")
        msg.setInformativeText(
            f"EEPROM correction: <b>{correction_dbm:+.2f} dBm</b>"
            + (f"<br>Path-loss: <b>{path_loss:+.2f} dBm</b>" if path_loss is not None else "")
        )
        msg.setDetailedText(details)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Apply)

        if msg.exec() != QMessageBox.StandardButton.Apply:
            return

        self._do_apply(row, correction)

    # -----------------------------------------------------------------------
    # Multi-correction (Apply Selected)
    # -----------------------------------------------------------------------

    def _on_apply_selected(self) -> None:
        selected = self._get_selected_rows()
        if not selected:
            return

        # Ensure path-loss file if needed
        if self._path_loss_table is None:
            reply = QMessageBox.question(
                self, "Path-loss file required",
                "No path-loss CSV file is loaded.\n\n"
                "Would you like to select one now?\n"
                "(Click 'No' to apply corrections without path-loss compensation.)",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No  |
                QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self._load_path_loss()

        # Build summary for confirmation dialog
        summary_lines = []
        for _row, c in selected:
            corr = c.get("correction_dbm", 0.0) or 0.0
            summary_lines.append(
                f"  • {c.get('label', ''):<40}  {corr:+.2f} dBm"
            )

        msg = QMessageBox(self)
        msg.setWindowTitle("Apply Selected Corrections")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(
            f"<b>Apply corrections to {len(selected)} selected block(s)?</b>"
        )
        msg.setInformativeText(
            "This will update the path-loss file for all selected blocks.\n"
            "A backup will be created automatically."
        )
        msg.setDetailedText("\n".join(summary_lines))
        msg.setStandardButtons(
            QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Apply)

        if msg.exec() != QMessageBox.StandardButton.Apply:
            return

        # Apply all selected
        failed = []
        for row, correction in selected:
            try:
                self._do_apply(row, correction)
            except Exception as exc:
                failed.append(f"{correction.get('label', row)}: {exc}")

        if failed:
            QMessageBox.warning(
                self, "Some corrections failed",
                "The following corrections could not be applied:\n\n"
                + "\n".join(failed)
            )
        else:
            QMessageBox.information(
                self, "Done",
                f"✔ {len(selected)} correction(s) applied successfully."
            )

        self._update_selection_label()

    # -----------------------------------------------------------------------
    # Core apply logic (shared by single and multi)
    # -----------------------------------------------------------------------

    def _do_apply(self, row: int, correction: dict) -> None:
        freq_mhz       = correction.get("freq_mhz", 0)
        antenna        = correction.get("antenna", "")
        correction_dbm = correction.get("correction_dbm", 0.0) or 0.0
        label          = correction.get("label", "")

        updated_loss = None
        backup_path  = None

        try:
            if self._path_loss_table is not None:
                backup_path  = self._path_loss_table.backup()
                updated_loss = self._path_loss_table.apply_correction(
                    freq_mhz=freq_mhz,
                    antenna=antenna,
                    correction_db=correction_dbm,
                )
                self._path_loss_table.save()
        except Exception as exc:
            raise RuntimeError(f"Could not update path-loss file: {exc}") from exc

        # Mark applied
        self._applied[label] = True

        # Update UI
        applied_lbl = _applied_label(f"✔ Applied ({correction_dbm:+.2f} dBm)")
        self._table.setCellWidget(row, _COL_NOTE, applied_lbl)

        # Disable checkbox
        cb = self._get_checkbox(row)
        if cb:
            cb.setChecked(False)
            cb.setEnabled(False)

        # Update correction dict
        correction["path_loss_db"] = updated_loss
        correction["applied"] = True
        correction["eeprom_correction_dbm"] = correction_dbm

        self.correction_applied.emit(correction)
        self._mark_applied_in_summary(label, correction_dbm)

    def _mark_applied_in_summary(self, label: str, value: float) -> None:
        current = self._summary_box.toPlainText()
        marker = f"\n  ✔ APPLIED: {label}  →  {value:+.2f} dBm"
        if marker not in current:
            self._summary_box.setPlainText(current + marker)

    # -----------------------------------------------------------------------
    # Metrics
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
    # Summary
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
                f"delta={c['delta_dbm']:+.2f} dBm  →  "
                f"correction = {corr:+.2f} dBm"
            )
        lines += ["─" * 60, f"Total: {len(corrections)} block(s) require correction."]
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
                    c.get("label"), c.get("band"), c.get("freq_mhz"),
                    c.get("modulation"), c.get("bandwidth"), c.get("antenna"),
                    c.get("origin_measured_dbm"), c.get("dut_measured_dbm"),
                    c.get("delta_dbm"), c.get("correction_dbm"),
                    c.get("status"), c.get("warning"),
                    c.get("path_loss_db", ""), c.get("applied", False),
                ])