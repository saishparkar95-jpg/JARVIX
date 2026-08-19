"""
jarvis/ui/system_tray.py
Windows System Tray integration for JARVIS.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
import config


def create_tray_icon_pixmap() -> QPixmap:
    """Generates a sleek cyan glowing circular icon for the system tray."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Outer cyan ring
    painter.setPen(QColor(0, 240, 255, 255))
    painter.setBrush(QColor(10, 20, 35, 220))
    painter.drawEllipse(2, 2, 28, 28)

    # Inner glowing core
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 240, 255, 200))
    painter.drawEllipse(10, 10, 12, 12)

    painter.end()
    return pixmap


class JarvisSystemTray(QSystemTrayIcon):
    """Manages Windows System Tray icon and quick actions context menu."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        # Set tray icon
        self.setIcon(QIcon(create_tray_icon_pixmap()))
        self.setToolTip(f"{config.ASSISTANT_NAME} AI Assistant - Online")

        self._create_menu()
        self.activated.connect(self._on_tray_activated)

    def _create_menu(self):
        """Builds system tray context menu."""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 6px;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
            }
        """)

        # Status item
        self.status_action = menu.addAction(f"🤖 {config.ASSISTANT_NAME}: Online")
        self.status_action.setEnabled(False)
        menu.addSeparator()

        # Navigation
        show_action = menu.addAction("🖥️ Show Dashboard")
        show_action.triggered.connect(self.main_window.show_and_activate)

        self.pause_action = menu.addAction("⏸️ Pause Assistant")
        self.pause_action.triggered.connect(self._toggle_pause)

        menu.addSeparator()
        stop_action = menu.addAction("⏹️ Emergency Stop")
        stop_action.triggered.connect(self.main_window.trigger_emergency_stop)

        menu.addSeparator()
        exit_action = menu.addAction("❌ Exit Application")
        exit_action.triggered.connect(self.main_window.close_application)

        self.setContextMenu(menu)

    def _toggle_pause(self):
        """Toggles pause/resume state."""
        if hasattr(self.main_window, "voice_worker"):
            if self.main_window.voice_worker.is_paused:
                self.main_window.voice_worker.resume_listening()
                self.pause_action.setText("⏸️ Pause Assistant")
                self.status_action.setText(f"🤖 {config.ASSISTANT_NAME}: Online")
            else:
                self.main_window.voice_worker.pause_listening()
                self.pause_action.setText("▶️ Resume Assistant")
                self.status_action.setText(f"🤖 {config.ASSISTANT_NAME}: Paused")

    def _on_tray_activated(self, reason):
        """Restores dashboard on double-click."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show_and_activate()
