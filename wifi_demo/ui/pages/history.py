from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.widgets import status_item, mono_item
from ui import styles


_COLUMNS = [
    "ID", "DATE", "DUT SERIAL", "PRODUCT",
    "TX PASS", "TX FAIL", "CORRECTIONS",
    "RX PASS", "RX FAIL",
    "AVG Δ dBm", "MAX |Δ|", "TOLERANCE", "RESULT",
]


class HistoryPage(QWidget):

    session_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions = []
        self._api_url  = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        bar = QHBoxLayout()
        search_lbl = QLabel("Search:")
        search_lbl.setObjectName("metric_label")
        self._search = QLineEdit()
        self._search.setPlaceholderText("Serial number, product…")
        self._search.setFixedWidth(240)
        self._search.textChanged.connect(self._apply_filter)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self.refresh)

        self._delete_btn = QPushButton("Delete selected")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._delete_selected)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._export_csv)

        self._count_lbl = QLabel("0 sessions")
        self._count_lbl.setObjectName("metric_sub")

        bar.addWidget(search_lbl)
        bar.addWidget(self._search)
        bar.addSpacing(12)
        bar.addWidget(self._count_lbl)
        bar.addStretch()
        bar.addWidget(self._refresh_btn)
        bar.addWidget(self._delete_btn)
        bar.addWidget(self._export_btn)
        root.addLayout(bar)

        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSortingEnabled(True)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.itemSelectionChanged.connect(self._on_selection)

        widths = [36, 120, 140, 80, 60, 60, 80, 60, 60, 80, 80, 70, 80]
        for i, w in enumerate(widths):
            self._table.setColumnWidth(i, w)
        root.addWidget(self._table)

        self._empty_lbl = QLabel(
            "No sessions in database.\n"
            "Run a calibration to save the first entry."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {styles.TEXT_DIM}; font-size: 13px;"
        )
        self._empty_lbl.setVisible(False)
        root.addWidget(self._empty_lbl)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_api_url(self, api_url: str):
        self._api_url = api_url

    # keep backward compat if anything still calls set_db
    def set_db(self, db):
        pass

    def refresh(self):
        if not self._api_url:
            return
        try:
            import requests
            r = requests.get(f"{self._api_url}/sessions?limit=500", timeout=10)
            r.raise_for_status()
            self._sessions = r.json()
            self._apply_filter()
            self._export_btn.setEnabled(bool(self._sessions))
        except Exception as e:
            self._count_lbl.setText(f"API error: {e}")

    # ── Private ───────────────────────────────────────────────────────────────

    def _apply_filter(self):
        q = self._search.text().lower().strip()
        filtered = self._sessions
        if q:
            filtered = [
                s for s in filtered
                if q in (s.get("dut_serial") or "").lower()
                or q in (s.get("product_name") or "").lower()
                or q in (s.get("origin_serial") or "").lower()
            ]
        self._populate(filtered)

    def _populate(self, sessions: list):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for s in sessions:
            row = self._table.rowCount()
            self._table.insertRow(row)

            avg = f"{s['avg_delta_dbm']:+.3f}" if s.get("avg_delta_dbm") is not None else "—"
            mx  = f"{s['max_delta_dbm']:.3f}"  if s.get("max_delta_dbm") is not None else "—"
            date_str = s.get("created_at", "—")[:16].replace("T", " ")

            cells = [
                mono_item(str(s["id"])),
                mono_item(date_str),
                mono_item(s.get("dut_serial") or "—"),
                mono_item(s.get("product_name") or "—"),
                mono_item(str(s.get("tx_pass", 0)),
                          color=QColor(styles.C_PASS)),
                mono_item(str(s.get("tx_fail", 0)),
                          color=QColor(styles.C_FAIL) if s.get("tx_fail") else None),
                mono_item(str(s.get("tx_corrections", 0)),
                          color=QColor(styles.C_WARN) if s.get("tx_corrections") else None),
                mono_item(str(s.get("rx_pass", 0)),
                          color=QColor(styles.C_PASS)),
                mono_item(str(s.get("rx_fail", 0)),
                          color=QColor(styles.C_FAIL) if s.get("rx_fail") else None),
                mono_item(avg),
                mono_item(mx),
                mono_item(f"{s.get('tolerance_dbm', 0):.1f}"),
                status_item("PASS" if s.get("overall_pass") else "FAIL"),
            ]

            for col, item in enumerate(cells):
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setData(Qt.ItemDataRole.UserRole, s["id"])
                    self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 28)

        self._table.setSortingEnabled(True)
        self._count_lbl.setText(f"{len(sessions)} session(s)")
        self._empty_lbl.setVisible(len(sessions) == 0)
        self._table.setVisible(len(sessions) > 0)

    def _on_selection(self):
        rows = self._table.selectedItems()
        self._delete_btn.setEnabled(bool(rows))
        if rows:
            sid = rows[0].data(Qt.ItemDataRole.UserRole)
            if sid:
                self.session_selected.emit(sid)

    def _delete_selected(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        sid = rows[0].data(Qt.ItemDataRole.UserRole)
        if sid is None:
            return
        reply = QMessageBox.question(
            self, "Delete session",
            f"Delete calibration session #{sid}?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes and self._api_url:
            try:
                import requests
                requests.delete(f"{self._api_url}/sessions/{sid}", timeout=10)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed:\n{e}")

    def _export_csv(self):
        from PyQt6.QtWidgets import QFileDialog
        import csv
        path, _ = QFileDialog.getSaveFileName(
            self, "Export session history", "calibration_history.csv",
            "CSV files (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(_COLUMNS)
            for s in self._sessions:
                writer.writerow([
                    s["id"],
                    s.get("created_at", "")[:16].replace("T", " "),
                    s.get("dut_serial", ""),
                    s.get("product_name", ""),
                    s.get("tx_pass", 0), s.get("tx_fail", 0),
                    s.get("tx_corrections", 0),
                    s.get("rx_pass", 0), s.get("rx_fail", 0),
                    s.get("avg_delta_dbm"), s.get("max_delta_dbm"),
                    s.get("tolerance_dbm"),
                    "PASS" if s.get("overall_pass") else "FAIL",
                ])