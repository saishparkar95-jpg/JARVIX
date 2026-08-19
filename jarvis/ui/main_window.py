"""
jarvis/ui/main_window.py
Main futuristic desktop window for JARVIS AI Assistant built with PySide6.
"""

import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QProgressBar, QMessageBox,
    QApplication, QDialog, QTextEdit
)
from PySide6.QtGui import QIcon, QFont, QKeySequence, QShortcut
from PySide6.QtCore import Qt, Slot

import config
from jarvis.ui.core_animation import AICoreWidget
from jarvis.ui.worker import VoiceWorker, SystemMonitorWorker
from jarvis.ui.system_tray import JarvisSystemTray, create_tray_icon_pixmap


DARK_STYLESHEET = """
QMainWindow {
    background-color: #070a12;
    color: #e2e8f0;
}

QFrame#glassPanel {
    background-color: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 14px;
}

QFrame#telemetryCard {
    background-color: rgba(13, 19, 33, 0.9);
    border: 1px solid rgba(0, 240, 255, 0.15);
    border-radius: 10px;
    padding: 6px;
}

QLabel {
    color: #cbd5e1;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

QLabel#titleLabel {
    color: #00f0ff;
    font-size: 26px;
    font-weight: bold;
    letter-spacing: 4px;
}

QLabel#stateBadge {
    background-color: rgba(0, 240, 255, 0.15);
    color: #00f0ff;
    border: 1px solid #00f0ff;
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #0d1321;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #00f0ff;
    border-radius: 3px;
    min-height: 20px;
}

QPushButton {
    background-color: rgba(15, 23, 42, 0.9);
    color: #00f0ff;
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(0, 240, 255, 0.2);
    border: 1px solid #00f0ff;
}

QPushButton:pressed {
    background-color: rgba(0, 240, 255, 0.4);
}

QPushButton#stopButton {
    color: #ff3344;
    border: 1px solid rgba(255, 51, 68, 0.5);
    background-color: rgba(30, 10, 15, 0.8);
}

QPushButton#stopButton:hover {
    background-color: rgba(255, 51, 68, 0.3);
    border: 1px solid #ff3344;
}

QPushButton#micButton {
    background-color: rgba(0, 255, 136, 0.15);
    color: #00ff88;
    border: 1px solid #00ff88;
}

QPushButton#micButton:hover {
    background-color: rgba(0, 255, 136, 0.3);
}

QProgressBar {
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 4px;
    text-align: center;
    background-color: #0d1321;
    color: #e2e8f0;
    font-size: 10px;
    height: 10px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077ff, stop:1 #00f0ff);
    border-radius: 3px;
}
"""


class MainWindow(QMainWindow):
    """Futuristic desktop GUI for JARVIS AI."""

    def __init__(self, start_minimized: bool = False):
        super().__init__()
        self.setWindowTitle(f"{config.ASSISTANT_NAME} AI Desktop Assistant")
        self.resize(1020, 680)
        self.setMinimumSize(850, 580)
        self.setWindowIcon(QIcon(create_tray_icon_pixmap()))
        self.setStyleSheet(DARK_STYLESHEET)

        # 1. Initialize UI Layout
        self._init_ui()

        # 2. Setup System Tray
        self.tray = JarvisSystemTray(self)
        self.tray.show()

        # 3. Setup Shortcuts (ESC for Emergency Stop)
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.esc_shortcut.activated.connect(self.trigger_emergency_stop)

        # 4. Start Background Workers
        self._start_workers()

        if start_minimized:
            self.hide()

    def _init_ui(self):
        """Constructs the futuristic dashboard layout."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # ----------------------------------------------------
        # TOP HEADER
        # ----------------------------------------------------
        header_layout = QHBoxLayout()
        self.title_label = QLabel(f"J A R V I S", self)
        self.title_label.setObjectName("titleLabel")

        self.state_badge = QLabel("STANDBY", self)
        self.state_badge.setObjectName("stateBadge")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.state_badge)
        main_layout.addLayout(header_layout)

        # ----------------------------------------------------
        # MIDDLE WORKSPACE (Left: AI Core, Right: Conversation)
        # ----------------------------------------------------
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(14)

        # LEFT: Holographic AI Core & Primary Status
        core_panel = QFrame(self)
        core_panel.setObjectName("glassPanel")
        core_layout = QVBoxLayout(core_panel)
        core_layout.setContentsMargins(16, 16, 16, 16)
        core_layout.setAlignment(Qt.AlignCenter)

        self.core_widget = AICoreWidget(self)
        core_layout.addWidget(self.core_widget)

        self.status_prompt = QLabel('"How can I help you, Sir?"', self)
        self.status_prompt.setAlignment(Qt.AlignCenter)
        self.status_prompt.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc; margin-top: 10px;")
        core_layout.addWidget(self.status_prompt)

        self.sub_status = QLabel(f"Say \"{config.WAKE_WORDS[0].title()}\" or click 🎤", self)
        self.sub_status.setAlignment(Qt.AlignCenter)
        self.sub_status.setStyleSheet("font-size: 12px; color: #94a3b8;")
        core_layout.addWidget(self.sub_status)

        middle_layout.addWidget(core_panel, stretch=5)

        # RIGHT: Conversation Feed
        chat_panel = QFrame(self)
        chat_panel.setObjectName("glassPanel")
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(14, 14, 14, 14)

        chat_header = QHBoxLayout()
        chat_title = QLabel("CONVERSATION FEED", self)
        chat_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #00f0ff; letter-spacing: 1px;")
        
        clear_btn = QPushButton("Clear", self)
        clear_btn.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        clear_btn.clicked.connect(self._clear_chat)
        
        chat_header.addWidget(chat_title)
        chat_header.addStretch()
        chat_header.addWidget(clear_btn)
        chat_layout.addLayout(chat_header)

        # Chat scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_feed_layout = QVBoxLayout(self.chat_container)
        self.chat_feed_layout.setAlignment(Qt.AlignTop)
        self.chat_feed_layout.setSpacing(10)
        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)

        middle_layout.addWidget(chat_panel, stretch=6)
        main_layout.addLayout(middle_layout, stretch=1)

        # ----------------------------------------------------
        # SYSTEM TELEMETRY CARDS
        # ----------------------------------------------------
        telemetry_layout = QHBoxLayout()
        telemetry_layout.setSpacing(10)

        # CPU Card
        self.cpu_card, self.cpu_bar, self.cpu_lbl = self._create_metric_card("CPU USAGE", "0%")
        telemetry_layout.addWidget(self.cpu_card)

        # RAM Card
        self.ram_card, self.ram_bar, self.ram_lbl = self._create_metric_card("RAM USAGE", "0%")
        telemetry_layout.addWidget(self.ram_card)

        # Battery Card
        self.bat_card, self.bat_bar, self.bat_lbl = self._create_metric_card("BATTERY", "100%")
        telemetry_layout.addWidget(self.bat_card)

        # Network Card
        self.net_card, self.net_lbl = self._create_network_card("NETWORK", "ONLINE")
        telemetry_layout.addWidget(self.net_card)

        main_layout.addLayout(telemetry_layout)

        # ----------------------------------------------------
        # BOTTOM CONTROLS
        # ----------------------------------------------------
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.mic_button = QPushButton("🎤 Listen (Direct)", self)
        self.mic_button.setObjectName("micButton")
        self.mic_button.clicked.connect(self._on_mic_clicked)

        self.stop_button = QPushButton("⏹ STOP (ESC)", self)
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.trigger_emergency_stop)

        self.mem_button = QPushButton("🧠 Memory", self)
        self.mem_button.clicked.connect(self._show_memory_dialog)

        self.settings_button = QPushButton("⚙ Settings", self)
        self.settings_button.clicked.connect(self._show_settings_dialog)

        controls_layout.addWidget(self.mic_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.mem_button)
        controls_layout.addWidget(self.settings_button)

        main_layout.addLayout(controls_layout)

    def _create_metric_card(self, title: str, initial_val: str):
        card = QFrame(self)
        card.setObjectName("telemetryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title_lbl = QLabel(title, card)
        title_lbl.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: bold; letter-spacing: 1px;")
        val_lbl = QLabel(initial_val, card)
        val_lbl.setStyleSheet("font-size: 12px; color: #00f0ff; font-weight: bold;")
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(val_lbl)
        layout.addLayout(header)

        prog_bar = QProgressBar(card)
        prog_bar.setRange(0, 100)
        prog_bar.setValue(0)
        prog_bar.setTextVisible(False)
        layout.addWidget(prog_bar)

        return card, prog_bar, val_lbl

    def _create_network_card(self, title: str, initial_val: str):
        card = QFrame(self)
        card.setObjectName("telemetryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        title_lbl = QLabel(title, card)
        title_lbl.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        val_lbl = QLabel(f"● {initial_val}", card)
        val_lbl.setStyleSheet("font-size: 13px; color: #00ff88; font-weight: bold;")
        layout.addWidget(val_lbl)

        return card, val_lbl

    def _start_workers(self):
        """Initializes and runs the non-blocking background workers."""
        # 1. Voice Worker
        self.voice_worker = VoiceWorker(self)
        self.voice_worker.state_changed.connect(self.on_state_changed)
        self.voice_worker.user_spoke.connect(self.add_user_message)
        self.voice_worker.jarvis_replied.connect(self.add_jarvis_message)
        self.voice_worker.start()

        # 2. System Monitor Worker
        self.monitor_worker = SystemMonitorWorker(self)
        self.monitor_worker.metrics_updated.connect(self.update_telemetry)
        self.monitor_worker.start()

    @Slot(str, str)
    def on_state_changed(self, state: str, details: str):
        """Refreshes UI state badges and animated core."""
        self.core_widget.set_state(state)
        self.state_badge.setText(state.upper())
        self.sub_status.setText(details if details else f"Say \"{config.WAKE_WORDS[0].title()}\"")

        if state == config.STATE_LISTENING:
            self.status_prompt.setText('"Listening to your voice..."')
        elif state == config.STATE_THINKING:
            self.status_prompt.setText('"Processing command..."')
        elif state == config.STATE_SPEAKING:
            self.status_prompt.setText('"Responding..."')
        elif state == config.STATE_IDLE:
            self.status_prompt.setText('"How can I help you, Sir?"')

    @Slot(str)
    def add_user_message(self, text: str):
        """Appends a user bubble to the conversation feed."""
        time_str = datetime.now().strftime("%I:%M %p")
        msg_frame = QFrame()
        msg_frame.setStyleSheet("""
            background-color: rgba(0, 119, 255, 0.15);
            border-left: 3px solid #0077ff;
            border-radius: 6px;
            padding: 8px;
        """)
        layout = QVBoxLayout(msg_frame)
        layout.setContentsMargins(6, 4, 6, 4)
        
        lbl_head = QLabel(f"<b>You</b> <font color='#64748b' size='2'>({time_str})</font>")
        lbl_text = QLabel(text)
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet("color: #f1f5f9; font-size: 13px;")
        
        layout.addWidget(lbl_head)
        layout.addWidget(lbl_text)
        self.chat_feed_layout.addWidget(msg_frame)
        self._scroll_chat_to_bottom()

    @Slot(str)
    def add_jarvis_message(self, text: str):
        """Appends a JARVIS bubble to the conversation feed."""
        time_str = datetime.now().strftime("%I:%M %p")
        msg_frame = QFrame()
        msg_frame.setStyleSheet("""
            background-color: rgba(0, 240, 255, 0.12);
            border-left: 3px solid #00f0ff;
            border-radius: 6px;
            padding: 8px;
        """)
        layout = QVBoxLayout(msg_frame)
        layout.setContentsMargins(6, 4, 6, 4)
        
        lbl_head = QLabel(f"<b>{config.ASSISTANT_NAME}</b> <font color='#64748b' size='2'>({time_str})</font>")
        lbl_head.setStyleSheet("color: #00f0ff;")
        lbl_text = QLabel(text)
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        
        layout.addWidget(lbl_head)
        layout.addWidget(lbl_text)
        self.chat_feed_layout.addWidget(msg_frame)
        self._scroll_chat_to_bottom()

    def _scroll_chat_to_bottom(self):
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def _clear_chat(self):
        while self.chat_feed_layout.count():
            item = self.chat_feed_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    @Slot(dict)
    def update_telemetry(self, metrics: dict):
        """Updates live CPU, RAM, Battery, and Network widgets."""
        cpu = int(metrics.get("cpu", 0))
        self.cpu_bar.setValue(cpu)
        self.cpu_lbl.setText(f"{cpu}%")

        ram = int(metrics.get("ram", 0))
        self.ram_bar.setValue(ram)
        self.ram_lbl.setText(f"{ram}%")

        bat = int(metrics.get("battery", 100))
        charging = " ⚡" if metrics.get("charging") else ""
        self.bat_bar.setValue(bat)
        self.bat_lbl.setText(f"{bat}%{charging}")

        net = metrics.get("network", "ONLINE")
        color = "#00ff88" if net == "ONLINE" else "#ff3344"
        self.net_lbl.setText(f"● {net}")
        self.net_lbl.setStyleSheet(f"font-size: 13px; color: {color}; font-weight: bold;")

    def _on_mic_clicked(self):
        """Triggers manual microphone listening."""
        if hasattr(self, "voice_worker"):
            self.voice_worker.trigger_manual_listen()

    def trigger_emergency_stop(self):
        """Cancels ongoing actions immediately."""
        if hasattr(self, "voice_worker"):
            self.voice_worker.tts.speak(f"Emergency stop activated, {config.USER_NAME}.")
            self.voice_worker.pause_listening()
            self.voice_worker.resume_listening()
            self.on_state_changed(config.STATE_IDLE, "Emergency Stop Triggered")

    def _show_memory_dialog(self):
        """Displays SQLite memory viewer."""
        dialog = QDialog(self)
        dialog.setWindowTitle("JARVIS Memory Database")
        dialog.resize(500, 400)
        dialog.setStyleSheet(DARK_STYLESHEET)
        
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit(dialog)
        text_edit.setReadOnly(True)
        
        recent = self.voice_worker.memory.get_recent_conversations(limit=15)
        content = "=== RECENT CONVERSATIONS IN MEMORY ===\n\n"
        for item in recent:
            role = item['role'].upper()
            content += f"[{role}]: {item['content']}\n"
            
        text_edit.setPlainText(content)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def _show_settings_dialog(self):
        """Displays Settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{config.ASSISTANT_NAME} Settings")
        dialog.resize(450, 320)
        dialog.setStyleSheet(DARK_STYLESHEET)
        
        layout = QVBoxLayout(dialog)
        info_label = QLabel(
            f"<b>{config.ASSISTANT_NAME} Desktop v1.2</b><br><br>"
            f"<b>Wake Word:</b> {config.WAKE_WORDS[0].title()}<br>"
            f"<b>User Name:</b> {config.USER_NAME}<br>"
            f"<b>AI Provider:</b> {config.AI_PROVIDER.upper()}<br>"
            f"<b>Voice Speed:</b> {config.VOICE_RATE} WPM<br>"
            f"<b>Security Mode:</b> {'STRICT (Safe Mode ON)' if config.SAFE_MODE else 'STANDARD'}<br>"
            f"<b>Protected Paths:</b> C:\\Windows, C:\\System32, C:\\Program Files"
        )
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def show_and_activate(self):
        """Restores window from tray and brings to foreground."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        """Minimizes to tray on close button rather than terminating immediately."""
        if self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                config.ASSISTANT_NAME,
                "JARVIS is running in the background. Say \"Hey Jarvis\" or click the tray icon.",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            self.close_application()

    def close_application(self):
        """Fully terminates application and workers."""
        if hasattr(self, "voice_worker"):
            self.voice_worker.stop()
        if hasattr(self, "monitor_worker"):
            self.monitor_worker.stop()
        QApplication.quit()
