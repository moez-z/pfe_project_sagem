from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont
import core.app_config as app_config


class PostSetupDialog(QDialog):

    def __init__(self, api_url: str, parent=None, allow_cancel: bool = False):
        super().__init__(parent)
        self.api_url       = api_url
        self._allow_cancel = allow_cancel
        self._posts        = []

        self.setWindowTitle("Post Configuration")
        self.setFixedSize(420, 280)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint
        )
        self._build_ui()
        self._load_posts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Welcome — Post Setup")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(
            "This is the first time the app runs on this machine.\n"
            "Please select which Caisson (post) this machine is.\n"
            "This setting can be changed later in Settings."
        )
        subtitle.setStyleSheet("color: #64748b; font-size: 12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(line)

        selector_layout = QHBoxLayout()
        lbl = QLabel("Select Post:")
        lbl.setFixedWidth(100)
        lbl.setFont(QFont("Segoe UI", 11))

        self.combo = QComboBox()
        self.combo.setFixedHeight(36)
        self.combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QComboBox:focus { border-color: #3b82f6; }
        """)
        selector_layout.addWidget(lbl)
        selector_layout.addWidget(self.combo)
        layout.addLayout(selector_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if self._allow_cancel:
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setFixedSize(90, 36)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #cbd5e1; border-radius: 6px;
                    font-size: 12px; color: #64748b;
                }
                QPushButton:hover { background: #f1f5f9; }
            """)
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setFixedSize(110, 36)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background: #2563eb; color: white;
                border-radius: 6px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover    { background: #1d4ed8; }
            QPushButton:disabled { background: #93c5fd; }
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)

    def _load_posts(self):
        try:
            import requests
            r = requests.get(f"{self.api_url}/posts", timeout=10)
            r.raise_for_status()
            self._posts = r.json()
        except Exception as e:
            QMessageBox.critical(self, "API Error",
                                 f"Cannot load posts from server:\n{e}")
            return

        self.combo.addItem("— Select a post —", userData=None)
        for post in self._posts:
            self.combo.addItem(post["name"], userData=post)

        self.combo.currentIndexChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, index: int):
        self.confirm_btn.setEnabled(index > 0)

    def _on_confirm(self):
        post = self.combo.currentData()
        if post is None:
            return
        app_config.set_post(
            post_id     = post["id"],
            post_number = post["number"],
            post_name   = post["name"],
        )
        QMessageBox.information(
            self, "Post Configured",
            f"This machine is now configured as:\n\n"
            f"  {post['name']}\n\n"
            f"Every calibration session will automatically\n"
            f"be linked to this post."
        )
        self.accept()