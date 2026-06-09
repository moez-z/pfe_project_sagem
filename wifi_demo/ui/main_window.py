import sys
import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget,
    QApplication, QStatusBar, QFrame, QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from ui.post_setup_dialog import PostSetupDialog
import core.app_config as app_config


from ui.styles import APP_STYLE, BORDER, ACCENT, TEXT_SEC, FONT_MONO, C_FAIL, C_FAIL_BG
from ui.pages.dashboard         import DashboardPage
from ui.pages.tx_page           import TxPage
from ui.pages.rx_page           import RxPage
from ui.pages.corrections_page  import CorrectionsPage
from ui.pages.history           import HistoryPage
from ui.pages.stats             import StatsPage
from ui.pages.path_loss_page    import PathLossPage


class _CalibrationWorker(QObject):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, origin_path, dut_path, tolerance):
        super().__init__()
        self.origin_path = origin_path
        self.dut_path    = dut_path
        self.tolerance   = tolerance

    def run(self):
        try:
            from core import LogParser, CalibrationEngine
            origin = LogParser.parse(self.origin_path)
            dut    = LogParser.parse(self.dut_path)
            self.finished.emit(CalibrationEngine.compare(origin, dut, self.tolerance))
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n\n{traceback.format_exc()}")


class MainWindow(QMainWindow):

    _NAV_ITEMS = [
        ("Dashboard",       "◈"),
        ("TX Calibration",  "◉"),
        ("RX Comparison",   "◎"),
        ("Corrections",     "◆"),
        ("Path Loss",       "⬡"),
        ("History",         "≡"),
        ("Statistics",      "▣"),
    ]

    def __init__(self, user=None, api_url=None):
        super().__init__()
        self._user   = user
        self._api_url = api_url
        self._report = None
        self._thread = None
        self._worker = None

        name = (user.full_name or user.matricule) if user else "offline"
        self.setWindowTitle(f"WiFi Calibration Tool — Sagemcom  |  {name}")
        self.resize(1300, 840)
        self.setMinimumSize(1050, 700)
        self._build_ui()
        self._nav_select(0)

        if api_url:
            self._history_page.set_api_url(api_url)
            self._stats_page.set_api_url(api_url)
            self._history_page.refresh()
            self._stats_page.refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        h.addWidget(self._make_sidebar())

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(self._make_topbar())

        self._stack = QStackedWidget()
        rl.addWidget(self._stack, 1)
        h.addWidget(right, 1)

        # ── Pages ────────────────────────────────────────────────────────────
        self._dash_page      = DashboardPage()
        self._tx_page        = TxPage()
        self._rx_page        = RxPage()
        self._corr_page      = CorrectionsPage()
        self._path_loss_page = PathLossPage()
        self._history_page   = HistoryPage()
        self._stats_page     = StatsPage()

        for pg in [
            self._dash_page,
            self._tx_page,
            self._rx_page,
            self._corr_page,
            self._path_loss_page,
            self._history_page,
            self._stats_page,
        ]:
            self._stack.addWidget(pg)

        self._path_loss_page.file_loaded.connect(
            self._corr_page.set_path_loss_file
        )

        # ── Status bar ───────────────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        post_name = app_config.get_post_name() or "No post"
        self._status_bar.showMessage(
            f"Ready.  |  Post: {post_name}"
            + ("  |  DB connected" if self._api_url else "  |  Offline")
        )
        self._dash_page.run_requested.connect(self._on_run_requested)

    def _make_sidebar(self):
        sb = QWidget()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(220)
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        logo = QLabel("SAGEMCOM")
        logo.setObjectName("logo_label")
        lay.addWidget(logo)

        self._product_lbl = QLabel("EDERSON")
        self._product_lbl.setObjectName("product_label")
        lay.addWidget(self._product_lbl)

        self._serial_lbl = QLabel("SN: —")
        self._serial_lbl.setObjectName("serial_label")
        lay.addWidget(self._serial_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        lay.addWidget(sep)
        lay.addSpacing(8)

        self._nav_btns = []
        for idx, (label, icon) in enumerate(self._NAV_ITEMS):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda checked, i=idx: self._nav_select(i))
            btn.setFixedHeight(42)
            lay.addWidget(btn)
            self._nav_btns.append(btn)

        lay.addStretch()

        # ── Post label + change button ────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {BORDER};")
        lay.addWidget(sep2)

        post_name = app_config.get_post_name() or "Not configured"
        self._post_lbl = QLabel(f"⬡  {post_name}")
        self._post_lbl.setStyleSheet(
            f"color: {ACCENT}; font-family: {FONT_MONO}; "
            f"font-size: 11px; padding: 6px 16px 2px 16px; font-weight: bold;"
        )
        lay.addWidget(self._post_lbl)

        change_post_btn = QPushButton("  ✎  Change Post")
        change_post_btn.setObjectName("nav_btn")
        change_post_btn.setFixedHeight(32)
        change_post_btn.setStyleSheet("font-size: 10px;")
        change_post_btn.clicked.connect(self._change_post)
        lay.addWidget(change_post_btn)

        # ── DB / operator info ────────────────────────────────────────────────
        db_color = ACCENT if self._api_url else TEXT_SEC
        db_text  = "● DB connected" if self._api_url else "○ Offline"
        db_lbl = QLabel(db_text)
        db_lbl.setStyleSheet(
            f"color: {db_color}; font-family: {FONT_MONO}; "
            f"font-size: 10px; padding: 4px 16px;"
        )
        lay.addWidget(db_lbl)

        op_name = (self._user.full_name or self._user.matricule) if self._user else "—"
        op_lbl = QLabel(f"Operator: {op_name}")
        op_lbl.setObjectName("serial_label")
        lay.addWidget(op_lbl)

        self._pdf_btn = QPushButton("  ⬇  Export PDF")
        self._pdf_btn.setObjectName("nav_btn")
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.clicked.connect(self._export_pdf)
        self._pdf_btn.setFixedHeight(38)
        lay.addWidget(self._pdf_btn)
        lay.addSpacing(10)

        # ── Logout button ─────────────────────────────────────────────────────────
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"color: {BORDER};")
        lay.addWidget(sep3)

        self._logout_btn = QPushButton("  ⏻  Logout")
        self._logout_btn.setObjectName("nav_btn")
        self._logout_btn.setFixedHeight(38)
        self._logout_btn.setStyleSheet(
            f"QPushButton {{ color: {C_FAIL}; text-align: left; "
            f"border: none; border-left: 3px solid transparent; "
            f"padding: 10px 16px 10px 13px; }}"
            f"QPushButton:hover {{ background-color: {C_FAIL_BG}; "
            f"border-left: 3px solid {C_FAIL}; color: {C_FAIL}; }}"
        )
        self._logout_btn.clicked.connect(self._on_logout)
        lay.addWidget(self._logout_btn)
        lay.addSpacing(6)

        return sb

    def _make_topbar(self):
        tb = QWidget()
        tb.setObjectName("topbar")
        row = QHBoxLayout(tb)
        row.setContentsMargins(24, 0, 24, 0)

        self._page_title = QLabel("Dashboard")
        self._page_title.setObjectName("page_title")

        self._status_badge = QLabel("NO DATA")
        self._status_badge.setObjectName("status_badge")
        self._status_badge.setProperty("status", "none")
        self._status_badge.setFont(
            QFont("Cascadia Code, Consolas", 10, QFont.Weight.Bold)
        )

        # Dark mode toggle
        from ui.styles import is_dark
        self._theme_btn = QPushButton("☀️  Light" if is_dark() else "🌙  Dark")
        self._theme_btn.setFixedHeight(32)
        self._theme_btn.setFixedWidth(100)
        self._theme_btn.clicked.connect(self._toggle_theme)

        row.addWidget(self._page_title)
        row.addStretch()
        row.addWidget(self._theme_btn)
        row.addSpacing(12)
        row.addWidget(self._status_badge)

        #User config button
        self._user_btn = QPushButton("👤  Profile")
        self._user_btn.setFixedHeight(32)
        self._user_btn.setFixedWidth(100)
        self._user_btn.clicked.connect(self._open_user_config)
        self._user_btn.setEnabled(self._user is not None)

        row.addWidget(self._page_title)
        row.addStretch()
        row.addWidget(self._user_btn)      # ← add this
        row.addSpacing(8)
        row.addWidget(self._theme_btn)
        row.addSpacing(12)
        row.addWidget(self._status_badge)
        return tb
    
    def _open_user_config(self):
        from ui.user_config_dialog import UserConfigDialog
        dlg = UserConfigDialog(self._user, self._api_url, parent=self)
        dlg.exec()

    def _toggle_theme(self):
        from ui import styles
        from PyQt6.QtWidgets import QApplication
        new_dark = not styles.is_dark()
        styles._DARK_MODE = new_dark
        styles.save_theme_pref(new_dark)
        QApplication.instance().setStyleSheet(styles.build_style())
        self._theme_btn.setText("☀️  Light" if new_dark else "🌙  Dark")

    def _nav_select(self, index):
        for i, btn in enumerate(self._nav_btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._stack.setCurrentIndex(index)
        self._page_title.setText(self._NAV_ITEMS[index][0])

    def _change_post(self):
        """Let the user re-configure the post from the sidebar."""
        dialog = PostSetupDialog(parent=self, allow_cancel=True)
        if dialog.exec() == PostSetupDialog.DialogCode.Accepted:
            post_name = app_config.get_post_name() or "Not configured"
            self._post_lbl.setText(f"⬡  {post_name}")
            self._status_bar.showMessage(
                f"Post changed to: {post_name}"
                + ("  |  DB connected" if self._api_url else "  |  Offline")
            )

    def _on_run_requested(self, origin_path, dut_path, tolerance):
        if self._thread and self._thread.isRunning():
            return
        self._status_bar.showMessage("⟳  Running calibration…")
        self._update_badge("none", "RUNNING…")

        self._worker = _CalibrationWorker(origin_path, dut_path, tolerance)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_done(self, report):
        self._report = report

        if report.dut_serial:
            self._serial_lbl.setText(f"SN: {report.dut_serial[:14]}")
        if report.product_name:
            self._product_lbl.setText(report.product_name)

        self._update_badge("pass" if report.overall_pass else "fail",
                           "PASS" if report.overall_pass else "FAIL")

        self._dash_page.update_report(report)
        self._tx_page.load_results(report.tx_results, report.tolerance_dbm)
        self._rx_page.load_results(report.rx_results)

        from core import CalibrationEngine
        corrections = CalibrationEngine.get_corrections(report)
        self._corr_page.load_corrections(corrections, report.tolerance_dbm)

        pl_path = self._path_loss_page.current_filepath()
        if pl_path:
            self._corr_page.set_path_loss_file(pl_path)

       # ── Persist via API ───────────────────────────────────────────────
        session_id = None
        if self._api_url:
            try:
                import requests
                payload = {
                    "user_id":       self._user.id if self._user else None,
                    "post_id":       app_config.get_post_id(),
                    "dut_serial":    report.dut_serial,
                    "origin_serial": report.origin_serial,
                    "product_name":  report.product_name,
                    "tolerance_dbm": report.tolerance_dbm,
                    "overall_pass":  report.overall_pass,
                    "tx_total":      len(report.tx_results),
                    "tx_pass":       report.tx_pass_count,
                    "tx_fail":       report.tx_fail_count,
                    "tx_corrections":report.tx_needs_correction_count,
                    "rx_total":      len(report.rx_results),
                    "rx_pass":       report.rx_pass_count,
                    "rx_fail":       report.rx_fail_count,
                    "avg_delta_dbm": report.tx_avg_delta,
                    "max_delta_dbm": report.tx_max_delta,
                    "tx_results": [
                        {
                            "band":           r.band.value if r.band else "",
                            "block_number":   r.block_number,
                            "freq_mhz":       r.freq_mhz,
                            "modulation":     r.modulation,
                            "bandwidth":      r.bandwidth,
                            "antenna":        r.antenna,
                            "origin_dbm":     r.origin_measured_dbm,
                            "dut_dbm":        r.dut_measured_dbm,
                            "delta_dbm":      r.delta_dbm,
                            "correction_dbm": r.correction_dbm,
                            "tx_target_dbm":  r.tx_target_dbm,
                            "limit_lo":       r.tx_limit_lo,
                            "limit_hi":       r.tx_limit_hi,
                            "status":         r.status.value,
                        }
                        for r in report.tx_results
                    ],
                    "rx_results": [
                        {
                            "band":          r.band.value if r.band else "",
                            "block_number":  r.block_number,
                            "freq_mhz":      r.freq_mhz,
                            "mcs":           r.mcs,
                            "bandwidth":     r.bandwidth,
                            "antenna_label": r.antenna_label,
                            "origin_rssi":   r.origin_rssi,
                            "dut_rssi":      r.dut_rssi,
                            "rssi_delta":    r.rssi_delta,
                            "origin_per":    r.origin_per,
                            "dut_per":       r.dut_per,
                            "status":        r.status.value,
                        }
                        for r in report.rx_results
                    ],
                }
                r = requests.post(f"{self._api_url}/sessions",
                                json=payload, timeout=15)
                session_id = r.json().get("id")
                self._history_page.refresh()
                self._stats_page.refresh()
            except Exception as e:
                print(f"[API ERROR] {e}")

    def _on_error(self, msg):
        self._update_badge("fail", "ERROR")
        self._status_bar.showMessage(f"✗  {msg.splitlines()[0]}")
        self._dash_page._console.setPlainText(f"ERROR:\n{msg}")

    def _export_pdf(self):
        if not self._report:
            return
        dut = self._report.dut_serial or "report"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", f"calibration_{dut}.pdf", "PDF files (*.pdf)"
        )
        if not path:
            return
        try:
            from core.pdf_report import PdfReport
            op = (self._user.full_name or self._user.matricule) if self._user else ""
            PdfReport.generate(self._report, path, operator=op)
            QMessageBox.information(self, "Export complete", f"Saved to:\n{path}")
        except ImportError as e:
            QMessageBox.warning(self, "Missing dependency", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))

    def _on_logout(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Close DB session
        if self._api_url:
            self._api_url.close()
            self._api_url = None

        self.close()

        # Show login again
        from PyQt6.QtWidgets import QApplication
        from ui.login_dialog import LoginDialog
        from db.config import SessionLocal, init_db
        from db.repository import UserRepo

        dlg = LoginDialog()
        if dlg.exec() != LoginDialog.DialogCode.Accepted:
            QApplication.instance().quit()
            return

        # Open new main window
        new_db   = SessionLocal()
        new_win  = MainWindow(user=dlg.user, db=new_db)
        new_win.show()

        # Keep reference so it doesn't get garbage collected
        QApplication.instance()._main_window = new_win           

    def _update_badge(self, status, text):
        self._status_badge.setText(text)
        self._status_badge.setProperty("status", status)
        self._status_badge.style().unpolish(self._status_badge)
        self._status_badge.style().polish(self._status_badge)


def run_app():
    import os
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    API_URL = os.environ.get("API_URL", "https://wifi-calibration-api.onrender.com")

    user    = None
    api_url = None

    try:
       
        QMessageBox.information(None, "Connecting...", 
            "Connecting to server, please wait...\n(First connection may take ~30 seconds)")
        r = requests.get(f"{API_URL}/health", timeout=30)
        if r.status_code == 200:
            api_url = API_URL
            from ui.login_dialog import LoginDialog
            dlg = LoginDialog(api_url=api_url)
            if dlg.exec() != LoginDialog.DialogCode.Accepted:
                sys.exit(0)
            user = dlg.user

            if not app_config.is_configured():
                setup = PostSetupDialog(api_url=api_url, allow_cancel=False)
                if setup.exec() != PostSetupDialog.DialogCode.Accepted:
                    sys.exit(0)
        else:
            QMessageBox.warning(None, "Server unavailable",
                                f"Cannot connect to API.\nRunning offline.")
    except Exception as e:
        QMessageBox.warning(None, "Offline", f"Running offline.\n{e}")

    window = MainWindow(user=user, api_url=api_url)
    window.show()
    sys.exit(app.exec())