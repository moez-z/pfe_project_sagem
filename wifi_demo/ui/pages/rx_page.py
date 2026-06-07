"""
pages/rx_page.py
----------------
RX Comparison page — read-only RSSI / PER comparison table.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
)
from PyQt6.QtGui import QColor, QFont

from ui.widgets import (
    CalibrationTable, MetricCard,
    mono_item, make_band_item, status_item, delta_item,
)
from ui import styles


_COLUMNS = [
    "BAND", "BLK", "FREQ (MHz)", "MCS", "BW", "ANT",
    "ORIGIN RSSI", "DUT RSSI", "Δ RSSI",
    "ORIG PER %", "DUT PER %", "STATUS",
]


class RxPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
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
        self._status_combo.addItems(["All", "PASS", "FAIL", "INVALID"])
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

        # ── Metrics ───────────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self._c_shown   = MetricCard("SHOWN",   "—", "blocks")
        self._c_pass    = MetricCard("PASS",     "—", "PER ≤ limit",
                                     style_name="metric_card_pass",
                                     value_name="metric_value_pass")
        self._c_fail    = MetricCard("FAIL",     "—", "PER > limit",
                                     style_name="metric_card_fail",
                                     value_name="metric_value_fail")
        self._c_invalid = MetricCard("N/A",      "—", "RSSI −999")
        for c in [self._c_shown, self._c_pass, self._c_fail, self._c_invalid]:
            cards_row.addWidget(c)
        cards_row.addStretch()
        root.addLayout(cards_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = CalibrationTable(_COLUMNS)
        widths = [72, 40, 90, 60, 60, 80, 100, 100, 80, 90, 90, 100]
        for i, w in enumerate(widths):
            self._table.setColumnWidth(i, w)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSortingEnabled(True)
        root.addWidget(self._table)

        # ── Legend ────────────────────────────────────────────────────────────
        legend = QHBoxLayout()
        for text, color in [
            ("PASS — PER within limit", styles.C_PASS),
            ("FAIL — PER exceeded", styles.C_FAIL),
            ("N/A — RSSI = −999 (multi-ant aggregate, expected)", styles.C_INVALID),
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

    def load_results(self, results: list):
        self._results = results
        self._apply_filter()
        self._export_btn.setEnabled(bool(results))

    # ── Private ───────────────────────────────────────────────────────────────

    def _apply_filter(self):
        band_f   = self._band_combo.currentText()
        status_f = self._status_combo.currentText()

        filtered = self._results
        if band_f != "All bands":
            filtered = [r for r in filtered
                        if r.band and r.band.value == band_f]
        if status_f != "All":
            filtered = [r for r in filtered
                        if r.status.value == status_f]

        self._populate_table(filtered)
        self._c_shown.set_value(str(len(filtered)))
        self._c_pass.set_value(str(sum(1 for r in filtered
                                       if r.status.value == "PASS")))
        self._c_fail.set_value(str(sum(1 for r in filtered
                                       if r.status.value == "FAIL")))
        self._c_invalid.set_value(str(sum(1 for r in filtered
                                          if r.status.value == "INVALID")))

    def _populate_table(self, results: list):
        self._table.setSortingEnabled(False)
        self._table.clear_rows()
        self._table.setHorizontalHeaderLabels(_COLUMNS)

        for r in results:
            band_val  = r.band.value if r.band else "?"
            orig_rssi = f"{r.origin_rssi:.1f}" if r.origin_rssi is not None else "—"
            dut_rssi  = f"{r.dut_rssi:.1f}"    if r.dut_rssi  is not None else "—"
            orig_per  = f"{r.origin_per:.2f}"  if r.origin_per  is not None else "—"
            dut_per   = f"{r.dut_per:.2f}"     if r.dut_per  is not None else "—"

            delta_cell = delta_item(r.rssi_delta, threshold=2.0) \
                         if r.rssi_delta is not None else mono_item("—")

            self._table.add_row([
                make_band_item(band_val),
                mono_item(str(r.block_number)),
                mono_item(str(r.freq_mhz)),
                mono_item(r.mcs),
                mono_item(r.bandwidth),
                mono_item(r.antenna_label),
                mono_item(orig_rssi),
                mono_item(dut_rssi),
                delta_cell,
                mono_item(orig_per),
                mono_item(dut_per),
                status_item(r.status.value),
            ])

        self._table.setSortingEnabled(True)

    def _export_csv(self):
        from PyQt6.QtWidgets import QFileDialog
        import csv

        path, _ = QFileDialog.getSaveFileName(
            self, "Export RX results", "rx_comparison.csv",
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
                    r.mcs,
                    r.bandwidth,
                    r.antenna_label,
                    r.origin_rssi,
                    r.dut_rssi,
                    r.rssi_delta,
                    r.origin_per,
                    r.dut_per,
                    r.status.value,
                ])