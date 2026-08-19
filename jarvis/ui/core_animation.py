"""
jarvis/ui/core_animation.py
Custom PySide6 Widget rendering an animated futuristic glowing AI core.
Reacts to assistant states (IDLE, LISTENING, THINKING, EXECUTING, SPEAKING, ERROR).
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
from PySide6.QtCore import Qt, QTimer
import config


STATE_PALETTES = {
    config.STATE_IDLE: {
        "primary": QColor(0, 240, 255, 220),       # Cyan
        "secondary": QColor(0, 150, 255, 120),
        "glow": QColor(0, 240, 255, 40),
        "speed": 0.8,
        "label": "STANDBY"
    },
    config.STATE_LISTENING: {
        "primary": QColor(0, 255, 136, 240),       # Neon Green
        "secondary": QColor(0, 200, 100, 140),
        "glow": QColor(0, 255, 136, 60),
        "speed": 2.2,
        "label": "LISTENING"
    },
    config.STATE_THINKING: {
        "primary": QColor(255, 180, 0, 240),       # Amber / Gold
        "secondary": QColor(255, 120, 0, 140),
        "glow": QColor(255, 180, 0, 60),
        "speed": 3.5,
        "label": "THINKING"
    },
    config.STATE_EXECUTING: {
        "primary": QColor(0, 170, 255, 240),       # Electric Blue
        "secondary": QColor(70, 100, 255, 140),
        "glow": QColor(0, 170, 255, 60),
        "speed": 2.8,
        "label": "EXECUTING"
    },
    config.STATE_SPEAKING: {
        "primary": QColor(217, 70, 239, 240),      # Neon Magenta
        "secondary": QColor(168, 85, 247, 140),
        "glow": QColor(217, 70, 239, 60),
        "speed": 2.0,
        "label": "SPEAKING"
    },
    config.STATE_ERROR: {
        "primary": QColor(255, 50, 70, 240),       # Crimson Red
        "secondary": QColor(200, 30, 50, 140),
        "glow": QColor(255, 50, 70, 60),
        "speed": 1.2,
        "label": "ALERT"
    }
}


class AICoreWidget(QWidget):
    """Futuristic holographic glowing AI core widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)

        self.current_state = config.STATE_IDLE
        self.angle = 0.0
        self.pulse = 0.0
        self.pulse_dir = 1

        # Smooth 40 FPS render timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_step)
        self.timer.start(25)

    def set_state(self, state: str):
        """Updates animation palette and rhythm."""
        if state in STATE_PALETTES:
            self.current_state = state
        self.update()

    def _animate_step(self):
        """Advances rotation angle and pulse waveform."""
        palette = STATE_PALETTES.get(self.current_state, STATE_PALETTES[config.STATE_IDLE])
        speed = palette["speed"]

        self.angle = (self.angle + speed * 1.2) % 360

        # Sine wave breathing pulse (0.0 to 1.0)
        self.pulse += 0.035 * speed * self.pulse_dir
        if self.pulse >= 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse <= 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1

        self.update()

    def paintEvent(self, event):
        """Paints the glowing concentric rings, rotating orbital arcs, and center core."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2.0
        center_y = height / 2.0
        base_radius = min(center_x, center_y) * 0.78

        palette = STATE_PALETTES.get(self.current_state, STATE_PALETTES[config.STATE_IDLE])
        prim = palette["primary"]
        sec = palette["secondary"]
        glow = palette["glow"]

        # 1. Background radial glow
        radial_grad = QRadialGradient(center_x, center_y, base_radius * 1.1)
        radial_grad.setColorAt(0.0, glow)
        radial_grad.setColorAt(0.7, QColor(glow.red(), glow.green(), glow.blue(), int(glow.alpha() * 0.4)))
        radial_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(radial_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - base_radius * 1.1, center_y - base_radius * 1.1,
                            base_radius * 2.2, base_radius * 2.2)

        # 2. Outer segmented ring
        outer_pen = QPen(sec, 1.5, Qt.DashLine)
        painter.setPen(outer_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_x - base_radius, center_y - base_radius, base_radius * 2, base_radius * 2)

        # 3. Rotating orbital arcs (Clockwise & Counter-Clockwise)
        arc_rect = (center_x - base_radius * 0.85, center_y - base_radius * 0.85,
                    base_radius * 1.7, base_radius * 1.7)
        arc_pen = QPen(prim, 3.0)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)

        # Draw 3 symmetric rotating arcs
        for i in range(3):
            start_deg = int((self.angle + i * 120) * 16)
            span_deg = int(70 * 16)
            painter.drawArc(*arc_rect, start_deg, span_deg)

        # Inner counter-rotating thin arc
        inner_arc_rect = (center_x - base_radius * 0.65, center_y - base_radius * 0.65,
                          base_radius * 1.3, base_radius * 1.3)
        inner_arc_pen = QPen(sec, 2.0)
        painter.setPen(inner_arc_pen)
        for i in range(4):
            start_deg = int((-self.angle * 1.4 + i * 90) * 16)
            span_deg = int(45 * 16)
            painter.drawArc(*inner_arc_rect, start_deg, span_deg)

        # 4. Central Glowing Orb (Pulsing)
        core_r = base_radius * (0.32 + 0.08 * self.pulse)
        core_grad = QRadialGradient(center_x, center_y, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        core_grad.setColorAt(0.4, prim)
        core_grad.setColorAt(1.0, QColor(prim.red(), prim.green(), prim.blue(), 20))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - core_r, center_y - core_r, core_r * 2, core_r * 2)

        # 5. Orbiting Data Nodes / Particles
        node_pen = QPen(QColor(255, 255, 255, 220), 1)
        painter.setPen(node_pen)
        painter.setBrush(QBrush(prim))
        for i in range(3):
            theta = math.radians(self.angle * 1.5 + i * 120)
            orb_x = center_x + base_radius * 0.85 * math.cos(theta)
            orb_y = center_y + base_radius * 0.85 * math.sin(theta)
            painter.drawEllipse(orb_x - 3.5, orb_y - 3.5, 7, 7)

        painter.end()
