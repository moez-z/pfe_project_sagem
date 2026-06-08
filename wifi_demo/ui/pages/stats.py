"""
ui/pages/stats.py
-----------------
Statistics dashboard page — Saint Petersburg Blue theme.
Colors: #71C5EE (light blue), #025091 (dark blue)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtCharts import (
    QChart, QChartView, QLineSeries, QBarSeries, QBarSet,
    QValueAxis, QBarCategoryAxis, QScatterSeries,
)
from ui.widgets import MetricCard
from ui import styles
class StatsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._api_url = None
        self._build_ui()
    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)
        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = QHBoxLayout()
        self._refresh_btn = QPushButton("Refresh stats")
        self._refresh_btn.clicked.connect(self.refresh)
        bar.addStretch()
        bar.addWidget(self._refresh_btn)
        root.addLayout(bar)
        # ── KPI cards row ─────────────────────────────────────────────────────
        cards = QHBoxLayout()
        cards.setSpacing(10)
        self._c_total   = MetricCard("TOTAL SESSIONS", "—", "in database")
        self._c_passrt  = MetricCard("PASS RATE",      "—", "%",
                                     style_name="metric_card_accent",
                                     value_name="metric_value_accent")
        self._c_avgd    = MetricCard("AVG DELTA",       "—", "dBm all sessions",
                                     style_name="metric_card_accent",
                                     value_name="metric_value_accent")
        self._c_maxd    = MetricCard("WORST DELTA",     "—", "dBm")
        for c in [self._c_total, self._c_passrt, self._c_avgd, self._c_maxd]:
            cards.addWidget(c)
        cards.addStretch()
        root.addLayout(cards)
        # ── Band pass-rate cards ───────────────────────────────────────────────
        band_row = QHBoxLayout()
        band_row.setSpacing(10)
        self._c_5g = MetricCard("5 GHz PASS RATE",   "—", "TX blocks",
                                style_name="metric_card_accent",
                                value_name="metric_value_accent")
        self._c_2g = MetricCard("2.4 GHz PASS RATE", "—", "TX blocks")
        self._c_6g = MetricCard("6 GHz PASS RATE",   "—", "TX blocks",
                                style_name="metric_card_accent",
                                value_name="metric_value_accent")
        for c in [self._c_5g, self._c_2g, self._c_6g]:
            band_row.addWidget(c)
        band_row.addStretch()
        root.addLayout(band_row)
        # ── Delta trend chart ─────────────────────────────────────────────────
        trend_lbl = QLabel("DELTA TREND — last 30 sessions")
        trend_lbl.setObjectName("section_header")
        root.addWidget(trend_lbl)
        self._trend_chart_view = self._make_empty_chart("Delta trend")
        self._trend_chart_view.setMinimumHeight(220)
        root.addWidget(self._trend_chart_view)
        # ── Pass/Fail bar chart ───────────────────────────────────────────────
        bar_lbl = QLabel("PASS / FAIL — last 20 sessions")
        bar_lbl.setObjectName("section_header")
        root.addWidget(bar_lbl)
        self._bar_chart_view = self._make_empty_chart("Pass/Fail")
        self._bar_chart_view.setMinimumHeight(180)
        root.addWidget(self._bar_chart_view)
    # ── Public API ─────────────────────────────────────────────────────────────
    # ── Public API ─────────────────────────────────────────────────────────────

    def set_api_url(self, api_url: str):
        self._api_url = api_url

    # keep backward compat
    def set_db(self, db):
        pass

    def refresh(self):
        if not hasattr(self, "_api_url") or not self._api_url:
            return
        try:
            import requests
            stats  = requests.get(f"{self._api_url}/stats/summary", timeout=10).json()
            deltas = requests.get(f"{self._api_url}/stats/deltas?limit=30", timeout=10).json()
            self._update_kpis(stats)
            self._update_trend_chart(deltas)
            self._update_bar_chart(deltas)
        except Exception as e:
            self._c_total.set_value("ERR")
            self._c_total.set_sub(str(e)[:40])
    # ── Private ───────────────────────────────────────────────────────────────
    def _update_kpis(self, stats: dict):
        self._c_total.set_value(str(stats["total_sessions"]))
        self._c_passrt.set_value(f"{stats['pass_rate']:.1f}%")
        avg = stats["avg_delta_dbm"]
        mx  = stats["max_delta_dbm"]
        self._c_avgd.set_value(f"{avg:+.3f}" if avg is not None else "—")
        self._c_maxd.set_value(f"{mx:.3f}"  if mx  is not None else "—")
        bs = stats["band_stats"]
        for c, key in [(self._c_5g, "5 GHz"), (self._c_2g, "2.4 GHz"), (self._c_6g, "6 GHz")]:
            b = bs.get(key, {})
            rate = b.get("rate", 0)
            total = b.get("total", 0)
            c.set_value(f"{rate:.0f}%")
            c.set_sub(f"{b.get('pass',0)} / {total} blocks")
    def _update_trend_chart(self, deltas: list):
        try:
            chart = QChart()
            # ── Blue theme backgrounds ────────────────────────────────────────
            chart.setBackgroundBrush(QBrush(QColor(styles.BG_SURFACE)))   # #0A1628
            chart.setPlotAreaBackgroundBrush(QBrush(QColor(styles.BG_RAISED)))  # #0F1F3D
            chart.setPlotAreaBackgroundVisible(True)
            chart.legend().setVisible(True)
            chart.legend().setLabelColor(QColor(styles.ACCENT))            # #71C5EE
            chart.legend().setBackgroundVisible(False)
            from PyQt6.QtCore import QMargins
            chart.setMargins(QMargins(8, 8, 8, 8))
            # ── Avg delta — light blue line ───────────────────────────────────
            avg_series = QLineSeries()
            avg_series.setName("Avg Δ dBm")
            avg_series.setColor(QColor(styles.ACCENT))                     # #71C5EE
            pen_avg = avg_series.pen()
            pen_avg.setWidth(2)
            avg_series.setPen(pen_avg)
            # ── Max delta — dark blue line ────────────────────────────────────
            max_series = QLineSeries()
            max_series.setName("Max |Δ| dBm")
            max_series.setColor(QColor(styles.ACCENT_DARK))                # #025091
            pen_max = max_series.pen()
            pen_max.setWidth(2)
            max_series.setPen(pen_max)
            for i, d in enumerate(deltas):
                if d["avg_delta"] is not None:
                    avg_series.append(i, d["avg_delta"])
                if d["max_delta"] is not None:
                    max_series.append(i, d["max_delta"])
            chart.addSeries(avg_series)
            chart.addSeries(max_series)
            axis_x = QValueAxis()
            axis_x.setRange(0, max(len(deltas)-1, 1))
            axis_x.setLabelFormat("%d")
            axis_x.setLabelsColor(QColor(styles.ACCENT))                   # #71C5EE
            axis_x.setGridLineColor(QColor(styles.BORDER))                 # #1A3A6A
            axis_x.setTitleText("Session index")
            axis_x.setTitleBrush(QBrush(QColor(styles.ACCENT)))
            axis_y = QValueAxis()
            axis_y.setLabelsColor(QColor(styles.ACCENT))                   # #71C5EE
            axis_y.setGridLineColor(QColor(styles.BORDER))                 # #1A3A6A
            axis_y.setTitleText("dBm")
            axis_y.setTitleBrush(QBrush(QColor(styles.ACCENT)))
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            avg_series.attachAxis(axis_x)
            avg_series.attachAxis(axis_y)
            max_series.attachAxis(axis_x)
            max_series.attachAxis(axis_y)
            self._trend_chart_view.setChart(chart)
        except Exception:
            pass
    def _update_bar_chart(self, deltas: list):
        try:
            # ── PASS = light blue, FAIL = red ─────────────────────────────────
            pass_set = QBarSet("PASS")
            fail_set = QBarSet("FAIL")
            pass_set.setColor(QColor(styles.ACCENT))          # #71C5EE  light blue
            pass_set.setBorderColor(QColor(styles.ACCENT_DARK))
            fail_set.setColor(QColor(styles.C_FAIL))          # #E74C3C  red
            fail_set.setBorderColor(QColor("#8B1A1A"))
            categories = []
            for d in deltas[-20:]:
                categories.append(f"#{d['id']}")
                pass_set.append(1 if d["overall_pass"] else 0)
                fail_set.append(0 if d["overall_pass"] else 1)
            series = QBarSeries()
            series.append(pass_set)
            series.append(fail_set)
            chart = QChart()
            chart.setBackgroundBrush(QBrush(QColor(styles.BG_SURFACE)))   # #0A1628
            chart.setPlotAreaBackgroundBrush(QBrush(QColor(styles.BG_RAISED)))
            chart.setPlotAreaBackgroundVisible(True)
            chart.addSeries(series)
            chart.legend().setVisible(True)
            chart.legend().setLabelColor(QColor(styles.ACCENT))
            chart.legend().setBackgroundVisible(False)
            from PyQt6.QtCore import QMargins
            chart.setMargins(QMargins(8, 4, 8, 4))
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setLabelsColor(QColor(styles.ACCENT))                   # #71C5EE
            axis_x.setGridLineColor(QColor(styles.BORDER))
            axis_y = QValueAxis()
            axis_y.setRange(0, 1.2)
            axis_y.setLabelsColor(QColor(styles.ACCENT))                   # #71C5EE
            axis_y.setGridLineColor(QColor(styles.BORDER))
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
            self._bar_chart_view.setChart(chart)
        except Exception:
            pass
    def _make_empty_chart(self, title: str) -> QChartView:
        try:
            chart = QChart()
            chart.setBackgroundBrush(QBrush(QColor(styles.BG_SURFACE)))   # #0A1628
            chart.setTitle(title)
            chart.setTitleBrush(QBrush(QColor(styles.ACCENT)))             # #71C5EE
            view = QChartView(chart)
            view.setRenderHint(QPainter.RenderHint.Antialiasing)
            view.setStyleSheet(
                f"background: {styles.BG_SURFACE}; border: 1px solid {styles.BORDER};"
            )
            return view
        except Exception:
            lbl = QLabel(f"[{title}]")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return lbl
