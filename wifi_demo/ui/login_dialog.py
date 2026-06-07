"""
------------------
Login dialog shown at application startup.
Verifies matricule + password against the users table in PostgreSQL.
Also shows DB connection status.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QKeyEvent

from ui.styles import (
    APP_STYLE, BG_BASE, BG_SURFACE, BG_RAISED, BORDER,
    ACCENT, ACCENT_DIM, TEXT_PRI, TEXT_SEC, TEXT_DIM,
    C_PASS, C_PASS_BG, C_FAIL, C_FAIL_BG, FONT_MONO,
)


# ── Background auth worker ────────────────────────────────────────────────────

class _AuthWorker(QObject):
    success = pyqtSignal(object)   # User object
    failure = pyqtSignal(str)      # error message

    def __init__(self, matricule: str, password: str):
        super().__init__()
        self.matricule = matricule
        self.password = password

    def run(self):
        try:
            from db.config import SessionLocal, init_db
            from db.repository import UserRepo
            from sqlalchemy.orm import make_transient

            db = SessionLocal()
            try:
                init_db()                                     # create tables if needed
                UserRepo.ensure_default_admin(db)             # create admin if empty
                user = UserRepo.verify(db, self.matricule, self.password)

                if user:
                    db.refresh(user)        # eagerly load all columns
                    db.expunge(user)        # detach safely from session
                    make_transient(user)
                    self.success.emit(user)
                else:
                    self.failure.emit("Invalid matricule or password.")
            finally:
                db.close()
        except Exception as e:
            self.failure.emit(f"Database error:\n{e}")


# ── Login dialog ──────────────────────────────────────────────────────────────

class LoginDialog(QDialog):
    """
    Modal login dialog. On successful authentication, `self.user` is set
    and the dialog accepts. On cancel / close, the app should exit.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = None
        self._thread = None
        self._worker = None

        self.setWindowTitle("WiFi Calibration Tool — Login")
        self.setFixedSize(400, 420)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._check_db_connection()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(0)

        # Branding
        brand = QLabel("SAGEMCOM")
        brand.setStyleSheet(
            f"QLabel {{ color: {ACCENT}; font-family: {FONT_MONO}; "
            f"font-size: 11px; letter-spacing: 4px; }}"
        )
        root.addWidget(brand)

        title = QLabel("WiFi Calibration")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"QLabel {{ color: {TEXT_PRI}; margin-bottom: 2px; }}")
        root.addWidget(title)

        sub = QLabel("Test Bench Calibration System")
        sub.setStyleSheet(
            f"QLabel {{ color: {TEXT_SEC}; font-size: 12px; margin-bottom: 24px; }}"
        )
        root.addWidget(sub)
        root.addSpacing(20)

        # DB status indicator
        self._db_status = QLabel("◌  Checking database connection…")
        self._db_status.setStyleSheet(
            f"QLabel {{ color: {TEXT_SEC}; font-family: {FONT_MONO}; "
            f"font-size: 11px; margin-bottom: 16px; }}"
        )
        root.addWidget(self._db_status)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; margin-bottom: 16px;")
        root.addWidget(sep)
        root.addSpacing(8)

        # Matricule label
        user_lbl = QLabel("matricule")
        user_lbl.setStyleSheet(
            f"QLabel {{ color: {TEXT_SEC}; font-family: {FONT_MONO}; "
            f"font-size: 10px; letter-spacing: 1.5px; margin-bottom: 4px; }}"
        )
        root.addWidget(user_lbl)

        self._matricule_edit = QLineEdit()
        self._matricule_edit.setPlaceholderText("Enter matricule")
        self._matricule_edit.setFixedHeight(38)
        self._matricule_edit.returnPressed.connect(self._on_login)
        root.addWidget(self._matricule_edit)
        root.addSpacing(14)

        # Password label
        pass_lbl = QLabel("PASSWORD")
        pass_lbl.setStyleSheet(
            f"QLabel {{ color: {TEXT_SEC}; font-family: {FONT_MONO}; "
            f"font-size: 10px; letter-spacing: 1.5px; margin-bottom: 4px; }}"
        )
        root.addWidget(pass_lbl)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setPlaceholderText("Enter password")
        self._password_edit.setFixedHeight(38)
        self._password_edit.returnPressed.connect(self._on_login)
        root.addWidget(self._password_edit)
        root.addSpacing(8)

        # Error message
        self._error_lbl = QLabel("")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet(
            f"QLabel {{ color: {C_FAIL}; font-size: 11px; "
            f"font-family: {FONT_MONO}; min-height: 32px; }}"
        )
        root.addWidget(self._error_lbl)
        root.addSpacing(8)

        # Login button
        self._login_btn = QPushButton("LOGIN")
        self._login_btn.setObjectName("btn_primary")
        self._login_btn.setFixedHeight(42)
        self._login_btn.setFont(QFont("Cascadia Code, Consolas", 12, QFont.Weight.Bold))
        self._login_btn.clicked.connect(self._on_login)
        root.addWidget(self._login_btn)

        root.addStretch()

        # Hint
        hint = QLabel("Default: admin / admin123")
        hint.setStyleSheet(
            f"QLabel {{ color: {TEXT_DIM}; font-size: 10px; font-family: {FONT_MONO}; }}"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hint)

    # ── DB connection check ────────────────────────────────────────────────────

    def _check_db_connection(self):
        try:
            from db.config import test_connection
            ok, msg = test_connection()
            if ok:
                self._db_status.setText(f"◆  {msg}")
                self._db_status.setStyleSheet(
                    f"QLabel {{ color: {C_PASS}; font-family: {FONT_MONO}; font-size: 11px; }}"
                )
            else:
                self._db_status.setText(f"✗  {msg}")
                self._db_status.setStyleSheet(
                    f"QLabel {{ color: {C_FAIL}; font-family: {FONT_MONO}; font-size: 11px; }}"
                )
                self._login_btn.setEnabled(False)
        except Exception as e:
            self._db_status.setText(f"✗  Cannot reach database: {e}")
            self._db_status.setStyleSheet(
                f"QLabel {{ color: {C_FAIL}; font-family: {FONT_MONO}; font-size: 11px; }}"
            )
            self._login_btn.setEnabled(False)

    # ── Login ──────────────────────────────────────────────────────────────────

    def _on_login(self):
        matricule = self._matricule_edit.text().strip()
        password = self._password_edit.text()

        if not matricule:
            self._show_error("Please enter your matricule.")
            return
        if not password:
            self._show_error("Please enter your password.")
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("VERIFYING…")
        self._error_lbl.setText("")

        import threading
        print(f"🔍 Main thread ID: {threading.current_thread().ident}")
        print(f"🔍 Creating AuthWorker for user: {matricule}")

        self._worker = _AuthWorker(matricule, password)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)

        self._worker.success.connect(lambda user: print(f"✓ Worker returned user: {user}"))
        self._worker.failure.connect(lambda msg: print(f"✗ Worker failed: {msg}"))

        self._worker.success.connect(self._on_success)
        self._worker.failure.connect(self._on_failure)
        self._worker.success.connect(self._thread.quit)
        self._worker.failure.connect(self._thread.quit)
        self._thread.start()

    def _on_success(self, user):
        print(f"🔍 _on_success called with user: {user}")
        print(f"🔍 User ID: {getattr(user, 'id', 'NO ID!')}")
        print(f"🔍 User matricule: {getattr(user, 'matricule', 'NO matricule!')}")
        self.user = user
        self.accept()

    def _on_failure(self, msg):
        print(f"🔍 _on_failure: {msg}")
        self._show_error(msg)
        self._login_btn.setEnabled(True)
        self._login_btn.setText("LOGIN")
        self._password_edit.clear()
        self._password_edit.setFocus()

    def _show_error(self, msg: str):
        self._error_lbl.setText(f"✗  {msg}")