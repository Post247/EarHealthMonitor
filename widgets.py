import math
import random
from PyQt5.QtCore import (
    Qt, QRectF, QEasingCurve, QVariantAnimation,
    QPropertyAnimation, pyqtProperty, QTimer,
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QRadialGradient,
)
from PyQt5.QtWidgets import (
    QWidget, QLabel, QFrame,
)


SAFE_COLOR     = QColor(52, 211, 153)
WARN_COLOR     = QColor(251, 191, 36)
CRITICAL_COLOR = QColor(248, 113, 113)
BG             = QColor(26, 26, 26)
CARD_BG        = QColor(34, 34, 34)
BORDER         = QColor(255, 255, 255, 28)
BORDER_HOVER   = QColor(255, 255, 255, 55)
ACCENT         = QColor(234, 234, 234)
TEXT_PRIMARY    = QColor(234, 234, 234)
TEXT_SECONDARY  = QColor(255, 255, 255, 90)


def draw_neumorphic_shadow(painter: QPainter, rect: QRectF, radius: int = 18, intensity: float = 1.0):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    rect = QRectF(rect)
    pen = QPen(QColor(255, 255, 255, int(22 * intensity)), 1)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(rect, radius, radius)
    painter.restore()


class NeoCard(QFrame):
    def __init__(self, parent=None, shadow_radius=18, shadow_intensity=1.0, flat=False):
        super().__init__(parent)
        self._shadow_radius = shadow_radius
        self._shadow_intensity = shadow_intensity
        self._flat = flat
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)

        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect, 14, 14)
        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()


class GaugeRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._target = 0.0
        self._color = SAFE_COLOR
        self._target_color = SAFE_COLOR
        self._glow_alpha = 0.0
        self._max_val = 180
        self._current_val = 0
        self.setMinimumSize(200, 200)

        self._anim = QVariantAnimation()
        self._anim.setDuration(800)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(lambda v: (setattr(self, '_progress', v), self.update()))

        self._color_anim = QVariantAnimation()
        self._color_anim.setDuration(500)
        self._color_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._color_anim.setStartValue(SAFE_COLOR)
        self._color_anim.setEndValue(SAFE_COLOR)
        self._color_anim.valueChanged.connect(lambda v: (setattr(self, '_color', v), self.update()))

        self._pulse_anim = QPropertyAnimation(self, b"glowAlpha")
        self._pulse_anim.setDuration(1200)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setKeyValueAt(0.5, 100.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)

    def set_target(self, current, maximum, animate=True):
        self._max_val = max(int(round(maximum)), 1)
        self._current_val = int(round(current))
        t = min(current / self._max_val, 1.0)
        self._target = t
        if animate:
            self._anim.setStartValue(self._progress)
            self._anim.setEndValue(t)
            self._anim.start()
        else:
            self._progress = t
            self.update()

    def set_status(self, status):
        color_map = {"safe": SAFE_COLOR, "warn": WARN_COLOR, "critical": CRITICAL_COLOR}
        new_c = color_map.get(status, SAFE_COLOR)
        self._color_anim.setStartValue(self._color)
        self._color_anim.setEndValue(new_c)
        self._color_anim.start()
        if status == "critical":
            if self._pulse_anim.state() != QPropertyAnimation.Running:
                self._pulse_anim.setLoopCount(3)
                self._pulse_anim.start()
        else:
            self._pulse_anim.stop()
            self._glow_alpha = 0.0
            self.update()

    def get_glowAlpha(self):
        return self._glow_alpha

    def set_glowAlpha(self, val):
        self._glow_alpha = val
        self.update()

    glowAlpha = pyqtProperty(float, get_glowAlpha, set_glowAlpha)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        size = min(self.width(), self.height())
        pad = 12
        rect = QRectF(pad, pad, size - 2 * pad, size - 2 * pad)
        cx, cy = rect.center().x(), rect.center().y()
        radius = rect.width() / 2
        pw = 2

        bg_pen = QPen(QColor(255, 255, 255, 18), pw, Qt.SolidLine, Qt.RoundCap)
        p.setPen(bg_pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(rect, 135 * 16, -270 * 16)

        if self._progress > 0.001:
            span = -270 * self._progress
            fg_pen = QPen(QColor(self._color), pw, Qt.SolidLine, Qt.RoundCap)
            p.setPen(fg_pen)
            p.drawArc(rect, 135 * 16, int(span * 16))

        if self._glow_alpha > 5:
            glow = QRadialGradient(cx, cy, radius + 20)
            gc = QColor(self._color)
            gc.setAlpha(int(self._glow_alpha * 0.4))
            glow.setColorAt(0.6, gc)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(QRectF(cx - radius - 20, cy - radius - 20,
                                 (radius + 20) * 2, (radius + 20) * 2))

        p.setPen(TEXT_PRIMARY)
        big = QFont("Cascadia Code", 28, QFont.Bold)
        p.setFont(big)
        p.drawText(QRectF(rect.left(), cy - 38, rect.width(), 44), Qt.AlignCenter,
                   str(self._current_val))

        p.setPen(TEXT_SECONDARY)
        unit = QFont("Cascadia Code", 9)
        p.setFont(unit)
        p.drawText(QRectF(rect.left(), cy + 8, rect.width(), 20), Qt.AlignCenter,
                   f"/ {self._max_val} min")


class AnimatedNumber(QLabel):
    def __init__(self, text="0", parent=None):
        super().__init__(text, parent)
        self._value = 0.0
        self._fmt = ".0f"
        self._anim = QVariantAnimation()
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(lambda v: self.setText(f"{v:{self._fmt}}"))

    def set_value(self, val, fmt=None):
        if fmt is not None:
            self._fmt = fmt
        self._anim.setStartValue(self._value)
        self._anim.setEndValue(val)
        self._anim.start()
        self._value = val

    def set_text_direct(self, text):
        self.setText(text)


class StatusDot(QWidget):
    def __init__(self, parent=None, size=14):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = TEXT_SECONDARY
        self._target_color = TEXT_SECONDARY

    def set_status(self, status):
        color_map = {"safe": SAFE_COLOR, "warn": WARN_COLOR, "critical": CRITICAL_COLOR,
                     "idle": TEXT_SECONDARY}
        self._target_color = color_map.get(status, TEXT_SECONDARY)
        self._anim = QVariantAnimation()
        self._anim.setDuration(400)
        self._anim.setStartValue(self._color)
        self._anim.setEndValue(self._target_color)
        self._anim.valueChanged.connect(lambda v: (setattr(self, '_color', v), self.update()))
        self._anim.start()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(self._color)
        p.drawEllipse(0, 0, self.width(), self.height())
        m = 4
        p.setBrush(QColor(26, 26, 26))
        p.drawEllipse(m, m, self.width() - 2 * m, self.height() - 2 * m)
        p.end()


class AudioWave(QWidget):
    def __init__(self, parent=None, bars=28):
        super().__init__(parent)
        self._bars = bars
        self._target = 0.0
        self._levels = [0.05] * bars
        self._speeds = [(0.6 + (i * 7919 % 31) / 31.0) * 10 for i in range(bars)]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(45)
        self.setMinimumHeight(110)

    def set_target(self, value):
        self._target = max(0.0, min(1.0, value / 100.0))

    def _tick(self):
        changed = False
        ev = 0.35 + 0.65 * self._target
        for i in range(self._bars):
            mid = 0.4 + 0.4 * math.sin(i / self._bars * math.pi)
            target_h = mid * (0.4 + 0.75 * self._target)
            jitter = random.uniform(-0.35, 0.35) * ev
            goal = max(0.03, target_h + jitter)
            cur = self._levels[i]
            nv = cur + (goal - cur) * 0.35
            if abs(nv - cur) > 0.001:
                changed = True
            self._levels[i] = nv
        if changed:
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        n = self._bars
        gap = 5
        bw = max((w - gap * (n + 1)) / n, 3)
        base = h * 0.85
        for i in range(n):
            lvl = self._levels[i]
            bh = max(base * lvl, 2)
            x = gap + i * (bw + gap)
            bar_rect = QRectF(x, h - bh, bw, bh)

            c = int(60 + 174 * lvl)
            col = QColor(c, c, c, 200)
            p.setPen(Qt.NoPen)
            p.setBrush(col)
            p.drawRoundedRect(bar_rect, bw / 2, bw / 2)
        p.end()
