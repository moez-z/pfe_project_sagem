
"""
pages/dashboard.py
------------------
Dashboard page — Saint Petersburg Blue theme.
Colors: #71C5EE (light blue / ACCENT), #025091 (dark blue / ACCENT_DARK)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QGroupBox,
    QTextEdit, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..widgets import (
    MetricCard, FilePathPicker,
    SectionHeader, HLine,
)
from .. import styles
class DashboardPage(QWidget):
    run_requested = pyqtSignal(str, str, float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)
        # ── File inputs ──────────────────────────────────────────────────────
        files_group = QGroupBox("LOG FILES")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(10)
        self._origin_picker = FilePathPicker(
            "Origin log", "Select reference / golden log…"
        )
        self._dut_picker = FilePathPicker(
            "DUT log", "Select device-under-test log…"
        )
        files_layout.addWidget(self._origin_picker)
        files_layout.addWidget(self._dut_picker)
        tol_row = QHBoxLayout()
        tol_lbl = QLabel("TX TOLERANCE")
        tol_lbl.setObjectName("metric_label")
        tol_lbl.setFixedWidth(90)
        tol_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._tolerance_spin = QDoubleSpinBox()
        self._tolerance_spin.setRange(0.1, 5.0)
        self._tolerance_spin.setSingleStep(0.1)
        self._tolerance_spin.setValue(0.5)
        self._tolerance_spin.setSuffix("  dBm")
        self._tolerance_spin.setDecimals(1)
        self._tolerance_spin.setFixedWidth(110)
        tol_hint = QLabel("delta threshold for correction flag")
        tol_hint.setObjectName("metric_sub")
        tol_row.addWidget(tol_lbl)
        tol_row.addWidget(self._tolerance_spin)
        tol_row.addWidget(tol_hint)
        tol_row.addStretch()
        files_layout.addLayout(tol_row)
        # ── RUN button — blue gradient ────────────────────────────────────────
        self._run_btn = QPushButton("▶  RUN CALIBRATION")
        self._run_btn.setObjectName("btn_primary")
        self._run_btn.setFixedHeight(40)
        self._run_btn.setFont(QFont("Cascadia Code, Consolas", 12, QFont.Weight.Bold))
        # Override inline for gradient effect:
        self._run_btn.setStyleSheet(f"""
            QPushButton#btn_primary {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {styles.ACCENT_DARK}, stop:1 {styles.ACCENT});
                color: #E0EFFF;
                border: 1px solid {styles.ACCENT};
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QPushButton#btn_primary:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {styles.ACCENT}, stop:1 {styles.ACCENT_DARK});
                color: #FFFFFF;
            }}
            QPushButton#btn_primary:disabled {{
                background-color: {styles.BG_RAISED};
                color: {styles.TEXT_DIM};
                border-color: {styles.BORDER_LO};
            }}
        """)
        self._run_btn.clicked.connect(self._on_run)
        files_layout.addWidget(self._run_btn)
        root.addWidget(files_group)
        # ── Overall banner ────────────────────────────────────────────────────
        self._banner = _ResultBanner()
        root.addWidget(self._banner)
        # ── Metric cards ──────────────────────────────────────────────────────
        root.addWidget(SectionHeader("Calibration Summary"))
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self._c_tx_total = MetricCard("TX BLOCKS",    "—", "total parsed",
                                      style_name="metric_card_accent",
                                      value_name="metric_value_accent")
        self._c_tx_pass  = MetricCard("TX PASS",      "—", "within limits",
                                      style_name="metric_card_pass",
                                      value_name="metric_value_pass")
        self._c_tx_fail  = MetricCard("TX FAIL",      "—", "outside limits",
                                      style_name="metric_card_fail",
                                      value_name="metric_value_fail")
        self._c_tx_corr  = MetricCard("TX CORRECTION","—", "need EEPROM fix",
                                      style_name="metric_card_accent",
                                      value_name="metric_value_accent")
        self._c_rx_pass  = MetricCard("RX PASS",      "—", "PER ≤ limit",
                                      style_name="metric_card_pass",
                                      value_name="metric_value_pass")
        self._c_rx_fail  = MetricCard("RX FAIL",      "—", "PER > limit",
                                      style_name="metric_card_fail",
                                      value_name="metric_value_fail")
        for card in [self._c_tx_total, self._c_tx_pass, self._c_tx_fail,
                     self._c_tx_corr, self._c_rx_pass, self._c_rx_fail]:
            cards_row.addWidget(card)
        root.addLayout(cards_row)
        # ── Delta stats row ───────────────────────────────────────────────────
        root.addWidget(SectionHeader("TX Delta Statistics"))
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self._c_avg_delta = MetricCard("AVG DELTA",    "—", "dBm",
                                       style_name="metric_card_accent",
                                       value_name="metric_value_accent")
        self._c_max_delta = MetricCard("MAX |DELTA|",  "—", "dBm",
                                       style_name="metric_card_accent",
                                       value_name="metric_value_accent")
        self._c_dut_sn    = MetricCard("DUT SERIAL",   "—", "")
        self._c_origin_sn = MetricCard("ORIGIN SERIAL","—", "")
        for card in [self._c_avg_delta, self._c_max_delta,
                     self._c_dut_sn, self._c_origin_sn]:
            stats_row.addWidget(card)
        stats_row.addStretch()
        root.addLayout(stats_row)
        # ── Console / warnings ────────────────────────────────────────────────
        root.addWidget(SectionHeader("Parse Log"))
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setMaximumHeight(120)
        self._console.setFont(QFont("Cascadia Code, Consolas", 11))
        self._console.setStyleSheet(
            f"background-color: {styles.BG_BASE}; "
            f"color: {styles.ACCENT}; "
            f"border: 1px solid {styles.ACCENT_DARK};"
        )
        self._console.setPlaceholderText(
            "Load two log files and press RUN CALIBRATION…"
        )
        root.addWidget(self._console)
        root.addStretch()
    def _on_run(self):
        origin = self._origin_picker.path()
        dut    = self._dut_picker.path()
        tol    = self._tolerance_spin.value()
        if not origin or not dut:
            self._console.setPlainText(
                "⚠  Please select both an Origin log and a DUT log."
            )
            return
        self.run_requested.emit(origin, dut, tol)
    def update_report(self, report):
        self._c_tx_total.set_value(str(len(report.tx_results)))
        self._c_tx_pass.set_value(str(report.tx_pass_count))
        self._c_tx_fail.set_value(str(report.tx_fail_count))
        self._c_tx_corr.set_value(str(report.tx_needs_correction_count))
        self._c_rx_pass.set_value(str(report.rx_pass_count))
        self._c_rx_fail.set_value(str(report.rx_fail_count))
        avg = report.tx_avg_delta
        mx  = report.tx_max_delta
        self._c_avg_delta.set_value(f"{avg:+.3f}" if avg is not None else "—")
        self._c_max_delta.set_value(f"{mx:.3f}" if mx is not None else "—")
        self._c_dut_sn.set_value(report.dut_serial[:12] or "—")
        self._c_dut_sn.set_sub(report.dut_serial[12:] or "")
        self._c_origin_sn.set_value(report.origin_serial[:12] or "—")
        self._banner.set_result(report.overall_pass)
        warnings_text = "\\n".join(report.warnings) if report.warnings else "No warnings."
        self._console.setPlainText(
            f"✓  Parsed {len(report.tx_results)} TX blocks, "
            f"{len(report.rx_results)} RX blocks.\\n"
            f"   Tolerance = {report.tolerance_dbm} dBm\\n\\n"
            + warnings_text
        )
# ── Result banner ─────────────────────────────────────────────────────────────
class _ResultBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)
        self._icon  = QLabel("◆")
        self._icon.setFont(QFont("Arial", 18))
        self._text  = QLabel("NO DATA — Load logs and run calibration")
        self._text.setFont(QFont("Cascadia Code, Consolas", 13, QFont.Weight.Bold))
        lay.addWidget(self._icon)
        lay.addWidget(self._text)
        lay.addStretch()
        self._set_style(None)
    def set_result(self, passed: bool):
        self._set_style(passed)
        if passed:
            self._text.setText("OVERALL RESULT:  PASS  — No corrections required")
        else:
            self._text.setText("OVERALL RESULT:  ❌  FAIL / CORRECTION NEEDED")
    def _set_style(self, passed):
        if passed is None:
            # Blue default state (was grey)
            bg     = styles.ACCENT_DIM    # #042A50
            border = styles.ACCENT_DARK   # #025091
            fg     = styles.ACCENT        # #71C5EE
        elif passed:
            bg, border, fg = styles.C_PASS_BG, styles.C_PASS, styles.C_PASS
        else:
            bg, border, fg = styles.C_FAIL_BG, styles.C_FAIL, styles.C_FAIL
        self.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border};"
        )
        self._icon.setStyleSheet(f"color: {fg};")
        self._text.setStyleSheet(f"color: {fg};")
