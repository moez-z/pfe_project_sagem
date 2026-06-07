"""
pages/tx_page.py
----------------
TX Calibration page.

Shows a full table of all TX_VERIFY blocks with:
  Band | Block | Freq | Mod | BW | ANT | Origin (dBm) | DUT (dBm) |
  Delta | Correction | Target | Limits | Status
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from ui.widgets import (
    CalibrationTable, MetricCard,
    SectionHeader, mono_item, make_band_item,
    delta_item, status_item,
)
from ui import styles
from core.calibration import TxStatus


_COLUMNS = [
    "BAND", "BLK", "FREQ (MHz)", "MOD", "BW",
    "ANT", "ORIGIN dBm", "DUT dBm",
    "DELTA", "CORRECTION", "TARGET", "LIMITS", "STATUS",
]


class TxPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._tolerance = 0.5
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # ── Filter bar ────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        band_lbl = QLabel("Band:")
        band_lbl.setObjectName("metric_label")
        self._band_combo = QComboBox()
        self._band_combo.addItems(["All bands", "5 GHz", "2.4 GHz", "6 GHz"])
        self._band_combo.currentTextChanged.connect(self._apply_filter)

        status_lbl = QLabel("Status:")
        status_lbl.setObjectName("metric_label")
        self._status_combo = QComboBox()
        self._status_combo.addItems([
            "All", "PASS", "FAIL", "NEEDS_CORRECTION", "OK", "NO_LIMIT"
        ])
        self._status_combo.currentTextChanged.connect(self._apply_filter)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._export_csv)

        filter_row.addWidget(band_lbl)
        filter_row.addWidget(self._band_combo)
        filter_row.addWidget(status_lbl)
        filter_row.addWidget(self._status_combo)
        filter_row.addStretch()
        filter_row.addWidget(self._export_btn)
        root.addLayout(filter_row)

        # ── Mini metric row ───────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self._c_shown  = MetricCard("SHOWN",   "—", "blocks")
        self._c_corr   = MetricCard("CORRECTIONS", "—", "blocks")
        self._c_avg_d  = MetricCard("AVG DELTA",   "—", "dBm")
        self._c_max_d  = MetricCard("MAX |Δ|",     "—", "dBm")
        for c in [self._c_shown, self._c_corr, self._c_avg_d, self._c_max_d]:
            cards_row.addWidget(c)
        cards_row.addStretch()
        root.addLayout(cards_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = CalibrationTable(_COLUMNS)
        # Column widths
        hdr = self._table.horizontalHeader()
        widths = [72, 40, 90, 72, 60, 55, 95, 95, 90, 95, 70, 110, 110]
        for i, w in enumerate(widths):
            self._table.setColumnWidth(i, w)
        hdr.setStretchLastSection(True)
        self._table.setSortingEnabled(True)
        root.addWidget(self._table)

        # ── Legend ────────────────────────────────────────────────────────────
        legend = QHBoxLayout()
        for text, color in [
            ("PASS — within hard limits", styles.C_PASS),
            ("FAIL — outside hard limits", styles.C_FAIL),
            ("NEEDS CORRECTION — delta > tolerance", styles.C_WARN),
            ("OK — delta within tolerance", styles.TEXT_SEC),
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            lbl = QLabel(text)
            lbl.setObjectName("metric_sub")
            legend.addWidget(dot)
            legend.addWidget(lbl)
            legend.addSpacing(16)
        legend.addStretch()
        root.addLayout(legend)

    # ── Public ────────────────────────────────────────────────────────────────

    def load_results(self, results: list, tolerance: float):
        self._results  = results
        self._tolerance = tolerance
        self._apply_filter()
        self._export_btn.setEnabled(bool(results))

    # ── Private ───────────────────────────────────────────────────────────────

    def _apply_filter(self):
        band_filter   = self._band_combo.currentText()
        status_filter = self._status_combo.currentText()

        filtered = self._results
        if band_filter != "All bands":
            filtered = [r for r in filtered
                        if r.band and r.band.value == band_filter]
        if status_filter != "All":
            filtered = [r for r in filtered
                        if r.status.value == status_filter]

        self._populate_table(filtered)
        self._update_mini_metrics(filtered)

    def _populate_table(self, results: list):
        self._table.setSortingEnabled(False)
        self._table.clear_rows()
        self._table.setHorizontalHeaderLabels(_COLUMNS)

        for r in results:
            band_val  = r.band.value if r.band else "?"
            limits_s  = r.limits_str
            orig_s    = f"{r.origin_measured_dbm:.2f}" if r.origin_measured_dbm is not None else "—"
            dut_s     = f"{r.dut_measured_dbm:.2f}"    if r.dut_measured_dbm is not None else "—"
            target_s  = f"{r.tx_target_dbm:.1f}"       if r.tx_target_dbm is not None else "—"
            corr_s    = r.correction_str

            delta_cell = delta_item(r.delta_dbm, self._tolerance) \
                         if r.delta_dbm is not None \
                         else mono_item("—")

            # Colour correction cell
            corr_cell = mono_item(corr_s)
            if r.needs_correction and r.correction_dbm is not None:
                corr_cell.setForeground(styles.cell_color_warn())
                corr_cell.setBackground(styles.cell_bg_warn())

            self._table.add_row([
                make_band_item(band_val),
                mono_item(str(r.block_number)),
                mono_item(str(r.freq_mhz)),
                mono_item(r.modulation),
                mono_item(r.bandwidth),
                mono_item(r.antenna),
                mono_item(orig_s),
                mono_item(dut_s),
                delta_cell,
                corr_cell,
                mono_item(target_s),
                mono_item(limits_s, color=QColor(styles.TEXT_DIM)),
                status_item(r.status.value),
            ])

        self._table.setSortingEnabled(True)

    def _update_mini_metrics(self, results: list):
        self._c_shown.set_value(str(len(results)))
        corr = sum(1 for r in results if r.needs_correction)
        self._c_corr.set_value(str(corr))

        deltas = [r.delta_dbm for r in results if r.delta_dbm is not None]
        if deltas:
            avg = sum(deltas) / len(deltas)
            mx  = max(abs(d) for d in deltas)
            self._c_avg_d.set_value(f"{avg:+.3f}")
            self._c_max_d.set_value(f"{mx:.3f}")
        else:
            self._c_avg_d.set_value("—")
            self._c_max_d.set_value("—")

    def _export_csv(self):
        from PyQt6.QtWidgets import QFileDialog
        import csv, os

        path, _ = QFileDialog.getSaveFileName(
            self, "Export TX results", "tx_calibration.csv",
            "CSV files (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(_COLUMNS)
            for r in self._results:
                writer.writerow([
                    r.band.value if r.band else "",
                    r.block_number,
                    r.freq_mhz,
                    r.modulation,
                    r.bandwidth,
                    r.antenna,
                    r.origin_measured_dbm,
                    r.dut_measured_dbm,
                    r.delta_dbm,
                    r.correction_dbm,
                    r.tx_target_dbm,
                    r.limits_str,
                    r.status.value,
                ])