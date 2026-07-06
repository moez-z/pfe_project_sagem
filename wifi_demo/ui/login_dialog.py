from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from ui.styles import (
    APP_STYLE, BG_BASE, BG_SURFACE, BG_RAISED, BORDER,
    ACCENT, ACCENT_DIM, TEXT_PRI, TEXT_SEC, TEXT_DIM,
    C_PASS, C_PASS_BG, C_FAIL, C_FAIL_BG, FONT_MONO,
)


# ── Simple user object (replaces SQLAlchemy User model) ──────────────────────

class UserData:
    def __init__(self, data: dict):
        self.id        = data.get("id")
        self.matricule = data.get("matricule", "")
        self.full_name = data.get("full_name", "")
        self.role      = data.get("role", "operator")
        self.last_login  = None
        self.created_at  = None


# ── Background auth worker ────────────────────────────────────────────────────

class _AuthWorker(QObject):
    success = pyqtSignal(object)
    failure = pyqtSignal(str)

    def __init__(self, api_url: str, matricule: str, password: str):
        super().__init__()
        self.api_url   = api_url
        self.matricule = matricule
        self.password  = password

    def run(self):
        try:
            import requests
            r = requests.post(
                f"{self.api_url}/auth/login",
                json={"matricule": self.matricule, "password": self.password},
                timeout=10,
            )
            if r.status_code == 200:
                self.success.emit(UserData(r.json()))
            elif r.status_code == 401:
                self.failure.emit("Invalid matricule or password.")
            else:
                self.failure.emit(f"Server error: {r.status_code}")
        except Exception as e:
            self.failure.emit(f"Cannot reach server:\n{e}")


# ── Login dialog ──────────────────────────────────────────────────────────────

class LoginDialog(QDialog):

    def __init__(self, api_url: str, parent=None):
        super().__init__(parent)
        self.api_url = api_url
        self.user    = None
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
        self._check_api_connection()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(0)

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

        self._api_status = QLabel("◌  Checking server connection…")
        self._api_status.setStyleSheet(
            f"QLabel {{ color: {TEXT_SEC}; font-family: {FONT_MONO}; "
            f"font-size: 11px; margin-bottom: 16px; }}"
        )
        root.addWidget(self._api_status)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; margin-bottom: 16px;")
        root.addWidget(sep)
        root.addSpacing(8)

        user_lbl = QLabel("MATRICULE")
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

        self._error_lbl = QLabel("")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet(
            f"QLabel {{ color: {C_FAIL}; font-size: 11px; "
            f"font-family: {FONT_MONO}; min-height: 32px; }}"
        )
        root.addWidget(self._error_lbl)
        root.addSpacing(8)

        self._login_btn = QPushButton("LOGIN")
        self._login_btn.setObjectName("btn_primary")
        self._login_btn.setFixedHeight(42)
        self._login_btn.setFont(QFont("Cascadia Code, Consolas", 12, QFont.Weight.Bold))
        self._login_btn.clicked.connect(self._on_login)
        root.addWidget(self._login_btn)

        root.addStretch()

        hint = QLabel("Default: admin / admin123")
        hint.setStyleSheet(
            f"QLabel {{ color: {TEXT_DIM}; font-size: 10px; font-family: {FONT_MONO}; }}"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hint)

    def _check_api_connection(self):
        try:
            import requests
            r = requests.get(f"{self.api_url}/health", timeout=5)
            if r.status_code == 200:
                self._api_status.setText(f"◆  Connected to server")
                self._api_status.setStyleSheet(
                    f"QLabel {{ color: {C_PASS}; font-family: {FONT_MONO}; font-size: 11px; }}"
                )
            else:
                self._set_offline(f"Server returned {r.status_code}")
        except Exception as e:
            self._set_offline(str(e))

    def _set_offline(self, msg: str):
        self._api_status.setText(f"✗  {msg}")
        self._api_status.setStyleSheet(
            f"QLabel {{ color: {C_FAIL}; font-family: {FONT_MONO}; font-size: 11px; }}"
        )
        self._login_btn.setEnabled(False)

    def _on_login(self):
        matricule = self._matricule_edit.text().strip()
        password  = self._password_edit.text()
        if not matricule:
            self._show_error("Please enter your matricule.")
            return
        if not password:
            self._show_error("Please enter your password.")
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("VERIFYING…")
        self._error_lbl.setText("")

        self._worker = _AuthWorker(self.api_url, matricule, password)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._on_success)
        self._worker.failure.connect(self._on_failure)
        self._worker.success.connect(self._thread.quit)
        self._worker.failure.connect(self._thread.quit)
        self._thread.start()

    def _on_success(self, user):
        self.user = user
        self.accept()

    def _on_failure(self, msg):
        self._show_error(msg)
        self._login_btn.setEnabled(True)
        self._login_btn.setText("LOGIN")
        self._password_edit.clear()
        self._password_edit.setFocus()

    def _show_error(self, msg: str):
        self._error_lbl.setText(f"✗  {msg}")