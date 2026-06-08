from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QWidget, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.styles import build_style, _tokens, FONT_MONO


def _t():
    return _tokens()


class UserConfigDialog(QDialog):

    def __init__(self, user, api_url, parent=None):
        super().__init__(parent)
        self._user = user
        self._api_url = api_url
        self._tab  = 0  # 0=info, 1=name, 2=password

        self.setWindowTitle("User Configuration")
        self.setFixedSize(460, 500)
        self.setStyleSheet(build_style())
        self._build_ui()

    # ── Root layout ───────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_tab_bar())

        self._content = QWidget()
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._content, 1)

        self._pages = [
            self._make_info_page(),
            self._make_name_page(),
            self._make_password_page(),
        ]
        for p in self._pages:
            self._content_lay.addWidget(p)

        self._switch_tab(0)

    # ── Header ────────────────────────────────────────────────────────────────

    def _make_header(self):
        t = _t()
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {t['ACCENT_DARK']}, stop:1 {t['ACCENT']});"
        )
        lay = QHBoxLayout(header)
        lay.setContentsMargins(24, 0, 24, 0)

        # Avatar circle
        avatar = QLabel(self._get_initials())
        avatar.setFixedSize(46, 46)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        avatar.setStyleSheet(
            f"background-color: rgba(255,255,255,0.2); "
            f"color: white; border-radius: 23px;"
        )
        lay.addWidget(avatar)
        lay.addSpacing(14)

        # Name + role
        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(self._user.full_name or self._user.matricule)
        name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: white;")

        role_lbl = QLabel(f"@{self._user.matricule}  ·  {self._user.role.upper()}")
        role_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.75); font-size: 11px;"
        )
        info.addWidget(name_lbl)
        info.addWidget(role_lbl)
        lay.addLayout(info)
        lay.addStretch()
        return header

    def _get_initials(self):
        name = self._user.full_name or self._user.matricule or "?"
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return name[:2].upper()

    # ── Tab bar ───────────────────────────────────────────────────────────────

    def _make_tab_bar(self):
        t = _t()
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(
            f"background-color: {t['BG_SURFACE']}; "
            f"border-bottom: 1px solid {t['BORDER']};"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._tab_btns = []
        tabs = [("ℹ  My Info", 0), ("✎  Full Name", 1), ("🔑  Password", 2)]
        for label, idx in tabs:
            btn = QPushButton(label)
            btn.setFixedHeight(44)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(self._tab_btn_style(idx == self._tab))
            btn.clicked.connect(lambda _, i=idx: self._switch_tab(i))
            lay.addWidget(btn)
            self._tab_btns.append(btn)

        return bar

    def _tab_btn_style(self, active: bool) -> str:
        t = _t()
        if active:
            return (
                f"QPushButton {{ background-color: {t['BG_BASE']}; "
                f"color: {t['ACCENT']}; border: none; "
                f"border-bottom: 2px solid {t['ACCENT']}; "
                f"font-size: 12px; font-family: {FONT_MONO}; }}"
            )
        return (
            f"QPushButton {{ background-color: {t['BG_SURFACE']}; "
            f"color: {t['TEXT_SEC']}; border: none; "
            f"border-bottom: 2px solid transparent; "
            f"font-size: 12px; font-family: {FONT_MONO}; }}"
            f"QPushButton:hover {{ color: {t['TEXT_PRI']}; "
            f"background-color: {t['BG_RAISED']}; }}"
        )

    def _switch_tab(self, idx: int):
        self._tab = idx
        for i, btn in enumerate(self._tab_btns):
            btn.setStyleSheet(self._tab_btn_style(i == idx))
        for i, page in enumerate(self._pages):
            page.setVisible(i == idx)

    # ── Page 1: Info ─────────────────────────────────────────────────────────

    def _make_info_page(self):
        t = _t()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(0)

        fields = [
            ("MATRICULE",    self._user.matricule),
            ("FULL NAME",    self._user.full_name or "—"),
            ("ROLE",         self._user.role.capitalize()),
            ("LAST LOGIN",   self._user.last_login.strftime("%d %b %Y  %H:%M")
                             if self._user.last_login else "Never"),
            ("MEMBER SINCE", self._user.created_at.strftime("%d %b %Y")
                             if self._user.created_at else "—"),
        ]

        for label, value in fields:
            row = QWidget()
            row.setStyleSheet(
                f"background-color: {t['BG_SURFACE']}; "
                f"border-radius: 6px; margin-bottom: 2px;"
            )
            rl = QVBoxLayout(row)
            rl.setContentsMargins(14, 10, 14, 10)
            rl.setSpacing(2)

            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color: {t['TEXT_SEC']}; font-size: 9px; "
                f"font-family: {FONT_MONO}; letter-spacing: 1.5px; "
                f"background: transparent;"
            )
            val = QLabel(str(value))
            val.setStyleSheet(
                f"color: {t['TEXT_PRI']}; font-size: 13px; "
                f"font-family: {FONT_MONO}; background: transparent;"
            )
            rl.addWidget(lbl)
            rl.addWidget(val)
            lay.addWidget(row)
            lay.addSpacing(6)

        lay.addStretch()
        return w

    # ── Page 2: Full Name ─────────────────────────────────────────────────────

    def _make_name_page(self):
        t = _t()
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(8)

        lay.addWidget(self._label("CURRENT NAME"))
        current = QLineEdit(self._user.full_name or "")
        current.setReadOnly(True)
        current.setFixedHeight(40)
        current.setStyleSheet(
            f"QLineEdit {{ background: {t['BG_RAISED']}; color: {t['TEXT_SEC']}; "
            f"border: 1px solid {t['BORDER']}; border-radius: 4px; "
            f"padding: 0 12px; font-size: 13px; }}"
        )
        lay.addWidget(current)
        lay.addSpacing(16)

        lay.addWidget(self._label("NEW FULL NAME"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter new full name…")
        self._name_edit.setFixedHeight(40)
        self._name_edit.returnPressed.connect(self._save_name)
        self._style_input(self._name_edit)
        lay.addWidget(self._name_edit)

        self._name_msg = QLabel("")
        self._name_msg.setFixedHeight(24)
        lay.addWidget(self._name_msg)

        lay.addStretch()

        btn = self._primary_btn("  ✓  Save Name")
        btn.clicked.connect(self._save_name)
        lay.addWidget(btn)
        return w

    def _save_name(self):
        new_name = self._name_edit.text().strip()
        if not new_name:
            self._msg(self._name_msg, "Please enter a name.", False)
            return
        try:
            import requests
            r = requests.patch(
                f"{self._api_url}/users/{self._user.id}/name",
                json={"full_name": new_name},
                timeout=10,
            )
            r.raise_for_status()
            self._user.full_name = new_name
            self._name_edit.clear()
            self._msg(self._name_msg, f"Name updated to '{new_name}'.", True)
        except Exception as e:
            self._msg(self._name_msg, f"Error: {e}", False)

    # ── Page 3: Password ──────────────────────────────────────────────────────

    def _make_password_page(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 20, 28, 28)
        lay.setSpacing(6)

        fields = [
            ("CURRENT PASSWORD",      "_old_pass",     "Current password"),
            ("NEW PASSWORD",          "_new_pass",      "At least 6 characters"),
            ("CONFIRM NEW PASSWORD",  "_confirm_pass",  "Repeat new password"),
        ]
        for label, attr, placeholder in fields:
            lay.addWidget(self._label(label))
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            edit.setPlaceholderText(placeholder)
            edit.setFixedHeight(40)
            self._style_input(edit)
            lay.addWidget(edit)
            lay.addSpacing(8)
            setattr(self, attr, edit)

        self._confirm_pass.returnPressed.connect(self._save_password)

        self._pass_msg = QLabel("")
        self._pass_msg.setFixedHeight(24)
        lay.addWidget(self._pass_msg)

        lay.addStretch()

        btn = self._primary_btn("  🔑  Change Password")
        btn.clicked.connect(self._save_password)
        lay.addWidget(btn)
        return w

    def _save_password(self):
        old  = self._old_pass.text()
        new  = self._new_pass.text()
        conf = self._confirm_pass.text()

        if not old or not new or not conf:
            self._msg(self._pass_msg, "All fields are required.", False)
            return
        if new != conf:
            self._msg(self._pass_msg, "New passwords don't match.", False)
            return
        if len(new) < 6:
            self._msg(self._pass_msg, "Password must be at least 6 characters.", False)
            return
        try:
            import requests
            r = requests.patch(
                f"{self._api_url}/users/{self._user.id}/password",
                json={"old_password": old, "new_password": new},
                timeout=10,
            )
            if r.status_code == 401:
                self._msg(self._pass_msg, "Current password is incorrect.", False)
                return
            r.raise_for_status()
            self._old_pass.clear()
            self._new_pass.clear()
            self._confirm_pass.clear()
            self._msg(self._pass_msg, "Password changed successfully!", True)
        except Exception as e:
            self._msg(self._pass_msg, f"Error: {e}", False)
        old  = self._old_pass.text()
        new  = self._new_pass.text()
        conf = self._confirm_pass.text()

        if not old or not new or not conf:
            self._msg(self._pass_msg, "All fields are required.", False)
            return
        if new != conf:
            self._msg(self._pass_msg, "New passwords don't match.", False)
            return
        if len(new) < 6:
            self._msg(self._pass_msg, "Password must be at least 6 characters.", False)
            return
        try:
            import bcrypt
            from db.models import User
            user = self._db.query(User).filter_by(id=self._user.id).first()
            if not bcrypt.checkpw(old.encode(), user.password_hash.encode()):
                self._msg(self._pass_msg, "Current password is incorrect.", False)
                return
            user.password_hash = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
            self._db.commit()
            self._old_pass.clear()
            self._new_pass.clear()
            self._confirm_pass.clear()
            self._msg(self._pass_msg, "Password changed successfully!", True)
        except Exception as e:
            self._msg(self._pass_msg, f"Error: {e}", False)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _label(self, text: str) -> QLabel:
        t = _t()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {t['TEXT_SEC']}; font-family: {FONT_MONO}; "
            f"font-size: 9px; letter-spacing: 1.5px;"
        )
        return lbl

    def _style_input(self, edit: QLineEdit):
        t = _t()
        edit.setStyleSheet(
            f"QLineEdit {{ background: {t['BG_RAISED']}; color: {t['TEXT_PRI']}; "
            f"border: 1px solid {t['BORDER']}; border-radius: 4px; "
            f"padding: 0 12px; font-size: 13px; font-family: {FONT_MONO}; }}"
            f"QLineEdit:focus {{ border: 1px solid {t['ACCENT']}; }}"
        )

    def _primary_btn(self, text: str) -> QPushButton:
        t = _t()
        btn = QPushButton(text)
        btn.setFixedHeight(42)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['ACCENT_DARK']}; "
            f"color: {t['ACCENT']}; border: 1px solid {t['ACCENT']}; "
            f"border-radius: 4px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {t['ACCENT']}; "
            f"color: {t['BG_BASE']}; }}"
        )
        return btn

    def _msg(self, lbl: QLabel, text: str, success: bool):
        t = _t()
        color = t["C_PASS"] if success else t["C_FAIL"]
        icon  = "✓" if success else "✗"
        lbl.setText(f"{icon}  {text}")
        lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-family: {FONT_MONO};"
        )