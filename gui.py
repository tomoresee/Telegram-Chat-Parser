"""gui.py — Desktop GUI для Telegram Parser (PyQt6)."""

import asyncio
import sys
import threading
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPushButton, QScrollArea,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)
from telethon.errors import SessionPasswordNeededError

from core.auth import get_client
from core.fetcher import get_private_dialogs, fetch_messages
from core.formatter import format_dialog
from core.exporter import save_to_file


STYLE = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-size: 13px;
    font-family: "Segoe UI", sans-serif;
}
QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    color: #cdd6f4;
}
QLineEdit:focus { border-color: #89b4fa; }
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
}
QPushButton:hover { background-color: #b4befe; }
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QTextEdit {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
}
QScrollArea, QScrollArea > QWidget > QWidget { background-color: #1e1e2e; border: none; }
QScrollBar:vertical { background: #313244; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #585b70; border-radius: 4px; }
QCheckBox { spacing: 8px; color: #cdd6f4; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px; border: 2px solid #45475a; background: transparent;
}
QCheckBox::indicator:checked { background-color: #89b4fa; border-color: #89b4fa; }
QFrame#left_panel { background-color: #181825; border-right: 1px solid #313244; }
"""


def _run_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


class _Sig(QObject):
    auth_status  = pyqtSignal(str, str)   # text, css-color
    show_code    = pyqtSignal()
    show_2fa     = pyqtSignal()
    go_to_chats  = pyqtSignal()
    chats_ready  = pyqtSignal(list)
    log_append   = pyqtSignal(str)
    export_done  = pyqtSignal()
    btn_restore  = pyqtSignal(str)        # "send" | "signin" | "pw"


class App(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Telegram Parser")
        self.setFixedSize(820, 560)
        self.setStyleSheet(STYLE)

        self._loop = asyncio.new_event_loop()
        threading.Thread(target=_run_loop, args=(self._loop,), daemon=True).start()

        self._client = get_client()
        self._phone: Optional[str] = None
        self._dialogs: list[dict] = []

        self._sig = _Sig()
        self._sig.go_to_chats.connect(self._show_loading)
        self._sig.chats_ready.connect(self._show_chats)

        self._show_auth()
        self._run(self._check_auth())

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    # ── Auth ─────────────────────────────────────────────────────────────────

    def _show_auth(self):
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setFixedWidth(380)
        lay = QVBoxLayout(card)
        lay.setSpacing(10)
        lay.setContentsMargins(36, 36, 36, 36)

        title = QLabel("Telegram Parser")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        sub = QLabel("Войдите в аккаунт Telegram")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #6c7086;")

        self._phone_input = QLineEdit()
        self._phone_input.setPlaceholderText("+79001234567")

        self._send_btn = QPushButton("Отправить код")
        self._send_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._send_btn.clicked.connect(self._on_send_code)

        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("Код из Telegram")
        self._code_input.hide()

        self._signin_btn = QPushButton("Войти")
        self._signin_btn.hide()
        self._signin_btn.clicked.connect(self._on_sign_in)

        self._pw_input = QLineEdit()
        self._pw_input.setPlaceholderText("Пароль двухфакторной аутентификации")
        self._pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_input.hide()

        self._pw_btn = QPushButton("Подтвердить")
        self._pw_btn.hide()
        self._pw_btn.clicked.connect(self._on_2fa)

        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setWordWrap(True)

        for w in [title, sub, self._phone_input, self._send_btn,
                  self._code_input, self._signin_btn,
                  self._pw_input, self._pw_btn, self._status_lbl]:
            lay.addWidget(w)

        outer.addWidget(card)
        self.setCentralWidget(root)

        self._sig.auth_status.connect(
            lambda t, c: (self._status_lbl.setText(t),
                          self._status_lbl.setStyleSheet(f"color: {c};")))
        self._sig.show_code.connect(lambda: (
            self._code_input.show(), self._signin_btn.show(),
            self._send_btn.setText("Отправить код снова"),
            self._send_btn.setEnabled(True)))
        self._sig.show_2fa.connect(lambda: (
            self._pw_input.show(), self._pw_btn.show(),
            self._signin_btn.setEnabled(True)))
        self._sig.btn_restore.connect(self._restore_btn)

    def _restore_btn(self, which: str):
        if which == "send":
            self._send_btn.setEnabled(True)
            self._send_btn.setText("Отправить код")
        elif which == "signin":
            self._signin_btn.setEnabled(True)
            self._signin_btn.setText("Войти")
        elif which == "pw":
            self._pw_btn.setEnabled(True)
            self._pw_btn.setText("Подтвердить")

    def _on_send_code(self):
        phone = self._phone_input.text().strip()
        if not phone:
            self._sig.auth_status.emit("Введите номер телефона", "#f38ba8")
            return
        self._phone = phone
        self._send_btn.setEnabled(False)
        self._send_btn.setText("Отправка...")
        self._run(self._async_send_code(phone))

    def _on_sign_in(self):
        code = self._code_input.text().strip()
        if not code:
            self._sig.auth_status.emit("Введите код", "#f38ba8")
            return
        self._signin_btn.setEnabled(False)
        self._signin_btn.setText("Вхожу...")
        self._run(self._async_sign_in(code))

    def _on_2fa(self):
        pw = self._pw_input.text().strip()
        if not pw:
            self._sig.auth_status.emit("Введите пароль", "#f38ba8")
            return
        self._pw_btn.setEnabled(False)
        self._pw_btn.setText("Проверяю...")
        self._run(self._async_2fa(pw))

    async def _check_auth(self):
        await self._client.connect()
        if await self._client.is_user_authorized():
            self._sig.go_to_chats.emit()

    async def _async_send_code(self, phone: str):
        try:
            await self._client.connect()
            await self._client.send_code_request(phone)
            self._sig.auth_status.emit("Код отправлен — проверьте Telegram", "#a6e3a1")
            self._sig.show_code.emit()
        except Exception as e:
            self._sig.auth_status.emit(str(e), "#f38ba8")
            self._sig.btn_restore.emit("send")

    async def _async_sign_in(self, code: str):
        try:
            await self._client.sign_in(self._phone or "", code)
            self._sig.go_to_chats.emit()
        except SessionPasswordNeededError:
            self._sig.auth_status.emit("Требуется пароль 2FA", "#fab387")
            self._sig.show_2fa.emit()
        except Exception as e:
            self._sig.auth_status.emit(str(e), "#f38ba8")
            self._sig.btn_restore.emit("signin")

    async def _async_2fa(self, password: str):
        try:
            await self._client.sign_in(password=password)
            self._sig.go_to_chats.emit()
        except Exception as e:
            self._sig.auth_status.emit(str(e), "#f38ba8")
            self._sig.btn_restore.emit("pw")

    # ── Chat screen ───────────────────────────────────────────────────────────

    def _show_loading(self):
        w = QWidget()
        lbl = QLabel("Загружаю список чатов...")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 15px;")
        QVBoxLayout(w).addWidget(lbl)
        self.setCentralWidget(w)
        self._run(self._async_fetch_dialogs())

    async def _async_fetch_dialogs(self):
        self._dialogs = await get_private_dialogs(self._client)
        self._sig.chats_ready.emit(self._dialogs)

    def _show_chats(self, dialogs: list):
        root = QWidget()
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── левая панель ──────────────────────────────────────────────────
        left = QFrame()
        left.setObjectName("left_panel")
        left.setFixedWidth(280)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(12, 16, 12, 12)

        title_lbl = QLabel(f"Чаты ({len(dialogs)})")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")

        self._select_all_cb = QCheckBox("Выбрать все")
        self._select_all_cb.stateChanged.connect(self._on_select_all)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_w = QWidget()
        scroll_lay = QVBoxLayout(scroll_w)
        scroll_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_lay.setSpacing(4)

        self._chat_cbs: list[QCheckBox] = []
        for d in dialogs:
            cb = QCheckBox(d["name"])
            self._chat_cbs.append(cb)
            scroll_lay.addWidget(cb)

        scroll.setWidget(scroll_w)
        left_lay.addWidget(title_lbl)
        left_lay.addWidget(self._select_all_cb)
        left_lay.addWidget(scroll)

        # ── правая панель ─────────────────────────────────────────────────
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(20, 16, 20, 16)

        dates_lbl = QLabel("Временной диапазон")
        dates_lbl.setStyleSheet("font-weight: bold;")

        dates_row = QHBoxLayout()
        dates_row.addWidget(QLabel("С:"))
        self._from_input = QLineEdit()
        self._from_input.setPlaceholderText("ДД.ММ.ГГГГ")
        self._from_input.setFixedWidth(130)
        dates_row.addWidget(self._from_input)
        dates_row.addSpacing(16)
        dates_row.addWidget(QLabel("По:"))
        self._to_input = QLineEdit()
        self._to_input.setPlaceholderText("ДД.ММ.ГГГГ")
        self._to_input.setFixedWidth(130)
        dates_row.addWidget(self._to_input)
        dates_row.addStretch()

        self._export_btn = QPushButton("Начать экспорт")
        self._export_btn.setFixedWidth(200)
        self._export_btn.clicked.connect(self._on_export)

        self._log_box = QTextEdit()
        self._log_box.setReadOnly(True)

        right_lay.addWidget(dates_lbl)
        right_lay.addLayout(dates_row)
        right_lay.addSpacing(8)
        right_lay.addWidget(self._export_btn)
        right_lay.addWidget(self._log_box)

        root_lay.addWidget(left)
        root_lay.addWidget(right)
        self.setCentralWidget(root)

        self._sig.log_append.connect(self._log_box.append)
        self._sig.export_done.connect(lambda: (
            self._export_btn.setEnabled(True),
            self._export_btn.setText("Начать экспорт")))

    def _on_select_all(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        for cb in self._chat_cbs:
            cb.setChecked(checked)

    def _parse_date(self, raw: str) -> Optional[datetime]:
        raw = raw.strip()
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%d.%m.%Y")
        except ValueError:
            return None

    def _on_export(self):
        selected = [self._dialogs[i] for i, cb in enumerate(self._chat_cbs) if cb.isChecked()]
        if not selected:
            self._log_box.append("⚠ Выберите хотя бы один чат.")
            return

        date_from = self._parse_date(self._from_input.text())
        date_to_raw = self._parse_date(self._to_input.text())
        date_to = date_to_raw.replace(hour=23, minute=59, second=59) if date_to_raw else None

        self._export_btn.setEnabled(False)
        self._export_btn.setText("Экспорт...")
        self._log_box.clear()

        self._run(self._async_export(selected, date_from, date_to))

    async def _async_export(self, selected: list[dict], date_from, date_to):
        all_blocks = []

        for d in selected:
            name = d["name"]
            self._sig.log_append.emit(f"→ {name}...")
            messages = await fetch_messages(self._client, d["entity"], date_from, date_to)

            if messages:
                block = format_dialog(name, messages)
                all_blocks.append(block)
                self._sig.log_append.emit(f"  ✓ {len(messages)} сообщений")
            else:
                self._sig.log_append.emit("  — нет сообщений за период")

        if all_blocks:
            content = "\n".join(all_blocks)
            filepath = save_to_file(content)
            self._sig.log_append.emit(f"\nГотово! Файл сохранён:\n{filepath}")
        else:
            self._sig.log_append.emit("\nНет данных для экспорта.")

        self._sig.export_done.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = App()
    window.show()
    sys.exit(app.exec())
