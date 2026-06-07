"""
ui/pages/history.py
-------------------
History page — shows all past calibration sessions from the database.
Clicking a row loads its TX/RX detail.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.widgets import status_item, mono_item
from ui import styles


_COLUMNS = [
    "ID", "DATE", "DUT SERIAL", "PRODUCT",
    "TX PASS", "TX FAIL", "CORRECTIONS",
    "RX PASS", "RX FAIL",
    "AVG Δ dBm", "MAX |Δ|", "TOLERANCE", "OPERATOR", "RESULT",
]


class HistoryPage(QWidget):
    """Loads all sessions from DB and displays them in a sortable table."""

    session_selected = pyqtSignal(int)   # session_id → other pages can react

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions = []
        self._db = None
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # ── Toolbar ───────────────────────────────────────────────────────────
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

        # Summary counts
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

        # ── Table ─────────────────────────────────────────────────────────────
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

        widths = [36, 120, 140, 80, 60, 60, 80, 60, 60, 80, 80, 70, 90, 80]
        for i, w in enumerate(widths):
            self._table.setColumnWidth(i, w)

        root.addWidget(self._table)

        # ── No-data placeholder ───────────────────────────────────────────────
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

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_db(self, db):
        """Pass a live SQLAlchemy session."""
        self._db = db

    def refresh(self):
        if self._db is None:
            return
        try:
            self._db.expire_all()                  
            from db.repository import SessionRepo
            self._sessions = SessionRepo.list_recent(self._db, limit=500)
            self._apply_filter()
            self._export_btn.setEnabled(bool(self._sessions))
        except Exception as e:
            self._count_lbl.setText(f"DB error: {e}")

    # ── Private ───────────────────────────────────────────────────────────────

    def _apply_filter(self):
        q = self._search.text().lower().strip()
        filtered = self._sessions
        if q:
            filtered = [
                s for s in filtered
                if q in (s.dut_serial or "").lower()
                or q in (s.product_name or "").lower()
                or q in (s.origin_serial or "").lower()
            ]
        self._populate(filtered)

    def _populate(self, sessions: list):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for s in sessions:
            row = self._table.rowCount()
            self._table.insertRow(row)

            avg = f"{s.avg_delta_dbm:+.3f}" if s.avg_delta_dbm is not None else "—"
            mx  = f"{s.max_delta_dbm:.3f}"  if s.max_delta_dbm is not None else "—"
            date_str = s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "—"
            operator = s.user.username if s.user else "—"

            cells = [
                mono_item(str(s.id)),
                mono_item(date_str),
                mono_item(s.dut_serial or "—"),
                mono_item(s.product_name or "—"),
                mono_item(str(s.tx_pass),    color=QColor(styles.C_PASS)),
                mono_item(str(s.tx_fail),    color=QColor(styles.C_FAIL) if s.tx_fail else None),
                mono_item(str(s.tx_corrections), color=QColor(styles.C_WARN) if s.tx_corrections else None),
                mono_item(str(s.rx_pass),    color=QColor(styles.C_PASS)),
                mono_item(str(s.rx_fail),    color=QColor(styles.C_FAIL) if s.rx_fail else None),
                mono_item(avg),
                mono_item(mx),
                mono_item(f"{s.tolerance_dbm:.1f}"),
                mono_item(operator),
                status_item("PASS" if s.overall_pass else "FAIL"),
            ]

            for col, item in enumerate(cells):
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setData(Qt.ItemDataRole.UserRole, s.id)
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
        if reply == QMessageBox.StandardButton.Yes and self._db:
            from db.repository import SessionRepo
            SessionRepo.delete(self._db, sid)
            self.refresh()

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
                    s.id,
                    s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "",
                    s.dut_serial, s.product_name,
                    s.tx_pass, s.tx_fail, s.tx_corrections,
                    s.rx_pass, s.rx_fail,
                    s.avg_delta_dbm, s.max_delta_dbm,
                    s.tolerance_dbm,
                    s.user.username if s.user else "",
                    "PASS" if s.overall_pass else "FAIL",
                ])
