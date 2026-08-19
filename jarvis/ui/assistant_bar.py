"""
jarvis/ui/assistant_bar.py
Google-Assistant-style Floating Bottom Pill/Overlay for Windows.
Features animated bouncing glowing dots, real-time live transcription, and seamless voice response.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QScreen
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QPropertyAnimation, QEasingCurve
import config


class GoogleDotsWidget(QWidget):
    """4-dot glowing animated voice visualizer (Google Assistant Style)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 40)
        self.phase = 0.0
        self.state = config.STATE_IDLE

        # Colors: Blue, Red, Yellow, Green (or JARVIS Neon Sci-fi Palette: Cyan, Blue, Magenta, Green)
        self.dot_colors = [
            QColor(0, 240, 255, 255),   # Cyan
            QColor(66, 133, 244, 255),  # Google Blue
            QColor(217, 70, 239, 255),  # Magenta
            QColor(0, 255, 136, 255),   # Green
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(25)  # 40 FPS

    def set_state(self, state: str):
        self.state = state
        self.update()

    def _animate(self):
        speed = 0.15 if self.state in [config.STATE_LISTENING, config.STATE_SPEAKING] else 0.05
        self.phase += speed
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        spacing = 26
        start_x = 24
        center_y = 20

        for i in range(4):
            # Calculate vertical bounce offset and size based on state
            if self.state == config.STATE_LISTENING:
                # Wave bounce animation
                y_offset = math.sin(self.phase * 2.0 + i * 0.8) * 8
                radius = 6.0 + math.sin(self.phase * 2.0 + i * 0.8) * 1.5
            elif self.state == config.STATE_THINKING:
                # Orbiting / pulsing
                y_offset = math.sin(self.phase * 3.0 + i * 1.2) * 5
                radius = 5.0
            elif self.state == config.STATE_SPEAKING:
                # Voice amplitude simulation
                y_offset = math.cos(self.phase * 2.5 + i * 0.9) * 9
                radius = 6.5
            else:
                # Idle subtle breathing
                y_offset = math.sin(self.phase + i * 0.5) * 2
                radius = 4.5

            color = self.dot_colors[i]
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                QPoint(int(start_x + i * spacing), int(center_y + y_offset)),
                int(radius), int(radius)
            )

        painter.end()


class GoogleAssistantBar(QWidget):
    """Floating Google-Assistant-style overlay bar that appears at bottom of screen."""

    def __init__(self, voice_worker, parent=None):
        super().__init__(parent)
        self.voice_worker = voice_worker

        # Frameless, Always on Top, Translucent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(580, 110)

        self._init_ui()
        self._position_bottom_center()
        self._connect_worker()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Glass Pill Card
        self.card = QFrame(self)
        self.card.setStyleSheet("""
            QFrame {
                background-color: rgba(13, 17, 23, 0.94);
                border: 1.5px solid rgba(0, 240, 255, 0.4);
                border-radius: 28px;
            }
        """)
        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(18, 10, 18, 10)
        card_layout.setSpacing(14)

        # 1. Google Animated Dots
        self.dots = GoogleDotsWidget(self.card)
        card_layout.addWidget(self.dots)

        # 2. Live Text Query & Response Area
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)

        self.status_label = QLabel("Hi, how can I help?", self.card)
        self.status_label.setStyleSheet("color: #f1f5f9; font-size: 15px; font-weight: 600; font-family: 'Segoe UI', sans-serif;")
        
        self.subtext_label = QLabel("Say \"Hey Jarvis\" or speak anytime", self.card)
        self.subtext_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-family: 'Segoe UI', sans-serif;")

        text_layout.addWidget(self.status_label)
        text_layout.addWidget(self.subtext_label)
        card_layout.addLayout(text_layout, stretch=1)

        # 3. Quick Close / Dismiss Button
        self.close_btn = QPushButton("✕", self.card)
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #94a3b8;
                border: none;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 70, 0.3);
                color: #ff3344;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        card_layout.addWidget(self.close_btn)

        main_layout.addWidget(self.card)

    def _position_bottom_center(self):
        """Positions the floating bar at the bottom center of the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 65  # Floating just above the Windows taskbar
        self.move(x, y)

    def _connect_worker(self):
        """Connects voice worker events to live UI updates."""
        self.voice_worker.state_changed.connect(self.on_state_changed)
        self.voice_worker.user_spoke.connect(self.on_user_spoke)
        self.voice_worker.jarvis_replied.connect(self.on_jarvis_replied)

    @Slot(str, str)
    def on_state_changed(self, state: str, details: str):
        self.dots.set_state(state)
        if state == config.STATE_LISTENING:
            self.show()
            self.status_label.setText("Listening...")
            self.subtext_label.setText("Speak your command in Hindi or English")
        elif state == config.STATE_THINKING:
            self.status_label.setText("Thinking...")
        elif state == config.STATE_IDLE:
            self.subtext_label.setText(f"Say \"{config.WAKE_WORDS[0].title()}\" anytime")

    @Slot(str)
    def on_user_spoke(self, text: str):
        self.show()
        self.status_label.setText(f'"{text}"')

    @Slot(str)
    def on_jarvis_replied(self, text: str):
        self.show()
        self.subtext_label.setText(f"JARVIS: {text}")
