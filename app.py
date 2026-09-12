import sys
import time
import winsound
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSystemTrayIcon, QMenu, QAction,
    QProgressBar, QFrame, QSpinBox, QComboBox, QCheckBox,
    QTabWidget, QTextEdit, QGridLayout, QSlider,
    QMessageBox, QSizePolicy, QLineEdit, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QVariantAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPainterPath, QPen

from ui_theme import APP_QSS
from widgets import (
    GaugeRing, AnimatedNumber, NeoCard, StatusDot,
)
from monitor import (
    ListeningMonitor, load_config, save_config,
    get_today_stats, get_week_stats, load_history, TIPS,
)


class AlertSignal(QObject):
    alert_triggered = pyqtSignal(str, str)


class ToastWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self._text = ""
        self._severity = "info"
        self._opacity = 0.0
        self._visible = False

        self._in = QVariantAnimation()
        self._in.setDuration(400)
        self._in.setEasingCurve(QEasingCurve.OutCubic)
        self._in.setStartValue(0.0)
        self._in.setEndValue(1.0)
        self._in.valueChanged.connect(lambda v: (setattr(self, '_opacity', v), self.update()))

        self._out = QVariantAnimation()
        self._out.setDuration(500)
        self._out.setEasingCurve(QEasingCurve.InCubic)
        self._out.setStartValue(1.0)
        self._out.setEndValue(0.0)
        self._out.valueChanged.connect(lambda v: (setattr(self, '_opacity', v), self.update()))
        self._out.finished.connect(lambda: setattr(self, '_visible', False))

    def show_toast(self, severity, text, ms=4000):
        self._text = text
        self._severity = severity
        self._visible = True
        self._out.stop()
        self._in.setStartValue(self._opacity)
        self._in.start()
        self.show()
        self.update()
        QTimer.singleShot(ms, self._dismiss)

    def _dismiss(self):
        self._in.stop()
        self._out.setStartValue(self._opacity)
        self._out.start()

    def paintEvent(self, e):
        if self._opacity < 0.01 or not self._visible:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self._opacity)
        w, h = self.width(), self.height()

        bg_map = {
            "critical": QColor(34, 34, 34),
            "warning":  QColor(34, 34, 34),
            "info":     QColor(34, 34, 34),
        }
        border_map = {
            "critical": QColor(248, 113, 113),
            "warning":  QColor(251, 191, 36),
            "info":     QColor(234, 234, 234),
        }
        text_map = border_map
        bg = bg_map.get(self._severity, bg_map["info"])
        acc = border_map.get(self._severity, border_map["info"])
        tc = text_map.get(self._severity, text_map["info"])

        path = QPainterPath()
        path.addRoundedRect(8, 4, w - 16, h - 8, 14, 14)

        p.setPen(QPen(acc, 1))
        p.setBrush(bg)
        p.drawPath(path)

        p.setPen(tc)
        p.setFont(QFont("Cascadia Code", 11, QFont.Bold))
        icon_map = {"critical": "!", "warning": "~", "info": "i"}
        p.drawText(QRect(24, 4, 24, h - 8), Qt.AlignCenter, icon_map.get(self._severity, "i"))
        p.setFont(QFont("Cascadia Code", 11))
        p.drawText(QRect(52, 4, w - 72, h - 8), Qt.AlignVCenter | Qt.AlignLeft, self._text[:70])
        p.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.monitor = ListeningMonitor(self.config)
        self.alert_signal = AlertSignal()
        self.alert_signal.alert_triggered.connect(self._on_alert)
        self._syncing = False
        self._paused = False

        self.setWindowTitle("Ear Health Monitor")
        self.setMinimumSize(760, 620)
        self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        self.setObjectName("main")

        self._setup_ui()
        self._setup_tray()
        self._tick = QTimer()
        self._tick.timeout.connect(self._update_display)
        self._tick.start(1000)

    def _setup_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(20, 16, 20, 8)
        lay.setSpacing(0)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(4, 0, 4, 8)
        t = QLabel("Ear Health Monitor")
        t.setObjectName("title")
        hl.addWidget(t)
        s = QLabel("60/60 Safe Listening Guardian")
        s.setObjectName("subtitle")
        hl.addWidget(s, 0, Qt.AlignBottom)
        hl.addStretch()
        self.dot = StatusDot(header, 12)
        hl.addWidget(self.dot, 0, Qt.AlignCenter)
        self.dot_lbl = QLabel("Idle")
        self.dot_lbl.setObjectName("subtitle")
        hl.addWidget(self.dot_lbl)
        lay.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._mon_tab(), "  Monitor  ")
        self.tabs.addTab(self._hist_tab(), "  History  ")
        self.tabs.addTab(self._cfg_tab(), "  Settings  ")
        self.tabs.addTab(self._tips_tab(), "  Tips  ")
        lay.addWidget(self.tabs)

        self.toast = ToastWidget(root)
        self.toast.hide()

        self.statusBar().showMessage("  Ready")

    # ---- Monitor Tab ----
    def _mon_tab(self):
        tab = QWidget()
        main = QVBoxLayout(tab)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(14)

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        bottom.addWidget(self._gauge_section(), 0)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)
        rl.addWidget(self._session_card())
        rl.addWidget(self._vol_card())
        rl.addWidget(self._controls_bar())
        rl.addStretch()
        bottom.addWidget(right, 1)

        main.addLayout(bottom)
        return tab

    def _gauge_section(self):
        c = NeoCard(shadow_radius=20, shadow_intensity=1.0)
        c.setMinimumWidth(280)
        c.setMaximumWidth(320)
        c.setFixedHeight(440)
        cl = QVBoxLayout(c)
        cl.setContentsMargins(24, 24, 24, 18)
        cl.setSpacing(4)
        cl.setAlignment(Qt.AlignHCenter)

        lbl = QLabel("TODAY'S LISTENING")
        lbl.setObjectName("sectionTitle")
        lbl.setAlignment(Qt.AlignCenter)
        cl.addWidget(lbl)
        cl.addSpacing(4)

        self.gauge = GaugeRing()
        self.gauge.setFixedSize(200, 200)
        cl.addWidget(self.gauge, 0, Qt.AlignHCenter)
        cl.addSpacing(8)

        r = QHBoxLayout()
        self.sc_val = AnimatedNumber("0")
        self.sc_val.setObjectName("statValue")
        self.sc_val.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.sc_val.setAlignment(Qt.AlignCenter)
        sc_l = QLabel("Sessions")
        sc_l.setObjectName("statLabel")
        sc_l.setAlignment(Qt.AlignCenter)
        sc_b = QVBoxLayout()
        sc_b.addWidget(self.sc_val, 0, Qt.AlignHCenter)
        sc_b.addWidget(sc_l, 0, Qt.AlignHCenter)
        r.addLayout(sc_b)

        r.addSpacing(16)

        self.av_val = AnimatedNumber("0")
        self.av_val.setObjectName("statValue")
        self.av_val.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.av_val.setAlignment(Qt.AlignCenter)
        av_l = QLabel("Avg Vol")
        av_l.setObjectName("statLabel")
        av_l.setAlignment(Qt.AlignCenter)
        av_b = QVBoxLayout()
        av_b.addWidget(self.av_val, 0, Qt.AlignHCenter)
        av_b.addWidget(av_l, 0, Qt.AlignHCenter)
        r.addLayout(av_b)

        cl.addLayout(r)
        cl.addSpacing(8)

        self.dbar = QProgressBar()
        self.dbar.setMaximumHeight(8)
        cl.addWidget(self.dbar)
        self.dlbl = QLabel("0 / 0 min")
        self.dlbl.setObjectName("dailyLabel")
        self.dlbl.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.dlbl)

        cl.addStretch()
        self._update_gauge_today()
        return c

    def _session_card(self):
        c = NeoCard(shadow_radius=16)
        cl = QVBoxLayout(c)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(6)

        top = QHBoxLayout()
        lbl = QLabel("CURRENT SESSION")
        lbl.setObjectName("sectionTitle")
        top.addWidget(lbl)
        top.addStretch()
        self.ss_lbl = QLabel("Inactive")
        self.ss_lbl.setObjectName("sessionEnded")
        top.addWidget(self.ss_lbl)
        cl.addLayout(top)

        cl.addSpacing(4)

        r1 = QHBoxLayout()
        r1.setSpacing(20)
        self.elapsed_lbl = QLabel("0:00")
        self.elapsed_lbl.setObjectName("elapsed")
        self.elapsed_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.elapsed_lbl.setMinimumWidth(100)
        r1.addWidget(self.elapsed_lbl)
        r1.addStretch()
        r1.addWidget(QLabel("Alerts"))
        self.sa_val = AnimatedNumber("0")
        self.sa_val.setObjectName("statValue")
        self.sa_val.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.sa_val.setMinimumWidth(60)
        r1.addWidget(self.sa_val)
        cl.addLayout(r1)

        cl.addSpacing(4)

        r2 = QHBoxLayout()
        r2.setSpacing(24)
        for attr, lbl_text in [('_avg_sess', 'Avg Volume'), ('_peak_sess', 'Peak Volume')]:
            box = QVBoxLayout()
            val = AnimatedNumber("0")
            val.setObjectName("statValue")
            val.setFont(QFont("Segoe UI", 14, QFont.Bold))
            val.setAlignment(Qt.AlignCenter)
            setattr(self, attr, val)
            box.addWidget(val, 0, Qt.AlignHCenter)
            sl = QLabel(lbl_text)
            sl.setObjectName("statLabel")
            sl.setAlignment(Qt.AlignCenter)
            box.addWidget(sl)
            r2.addLayout(box)
        cl.addLayout(r2)
        return c

    def _vol_card(self):
        c = NeoCard(shadow_radius=14)
        cl = QVBoxLayout(c)
        cl.setContentsMargins(18, 12, 18, 12)
        cl.setSpacing(4)

        lbl = QLabel("SYSTEM VOLUME")
        lbl.setObjectName("sectionTitle")
        cl.addWidget(lbl)
        cl.addSpacing(4)

        self.vslider = QSlider(Qt.Horizontal)
        self.vslider.setRange(0, 100)
        self.vslider.setValue(self._get_sys_vol())
        self.vslider.setTickInterval(10)
        self.vslider.setTickPosition(QSlider.TicksBelow)
        self.vslider.valueChanged.connect(self._vol_changed)
        cl.addWidget(self.vslider)

        r = QHBoxLayout()
        self.vdisp = AnimatedNumber(str(self.vslider.value()))
        self.vdisp.setObjectName("statValue")
        self.vdisp.setFont(QFont("Segoe UI", 14, QFont.Bold))
        r.addWidget(self.vdisp)
        r.addStretch()
        pl = QLabel("%")
        pl.setObjectName("statLabel")
        r.addWidget(pl)
        cl.addLayout(r)

        self.vstat = QLabel("Safe")
        self.vstat.setObjectName("volumeStatusSafe")
        self.vstat.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.vstat)
        return c

    def _controls_bar(self):
        f = QFrame()
        f.setObjectName("card")
        f.setStyleSheet("QFrame#card { background: #222222; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; }")
        h = QHBoxLayout(f)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(12)

        self.start_btn = QPushButton("Start Session")
        self.start_btn.setObjectName("primary")
        self.start_btn.setFixedSize(140, 44)
        self.start_btn.clicked.connect(self._toggle_session)
        h.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("accent")
        self.pause_btn.setFixedSize(140, 44)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._toggle_pause)
        h.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setFixedSize(140, 44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        h.addWidget(self.stop_btn)
        return f

    # ---- History Tab ----
    def _hist_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setSpacing(10)

        t = QLabel("Usage History")
        t.setObjectName("title")
        t.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lay.addWidget(t)

        week = get_week_stats()
        wc = NeoCard(shadow_radius=14)
        wl = QVBoxLayout(wc)
        wl.setContentsMargins(18, 14, 18, 14)
        wl.setSpacing(6)
        wl.addWidget(QLabel("Last 7 Days"))
        for d in week:
            dn = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%a %b %d")
            r = QHBoxLayout()
            dl = QLabel(dn)
            dl.setObjectName("statLabel")
            dl.setMinimumWidth(85)
            r.addWidget(dl)
            bar = QProgressBar()
            bar.setMaximum(int(self.config["max_daily_minutes"]))
            bar.setValue(int(d["minutes"]))
            bar.setMaximumHeight(8)
            bar.setTextVisible(False)
            r.addWidget(bar, 1)
            ml = QLabel(f"{d['minutes']:.0f}m")
            ml.setObjectName("statLabel")
            ml.setMinimumWidth(45)
            ml.setAlignment(Qt.AlignRight)
            r.addWidget(ml)
            wl.addLayout(r)
        lay.addWidget(wc)

        hc = NeoCard(shadow_radius=12)
        hl = QVBoxLayout(hc)
        hl.setContentsMargins(18, 14, 18, 14)
        self.h_text = QTextEdit()
        self.h_text.setReadOnly(True)
        self.h_text.setMaximumHeight(200)
        self._refresh_hist()
        hl.addWidget(self.h_text)
        lay.addWidget(hc)

        btn = QPushButton("Refresh")
        btn.setObjectName("ghost")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._refresh_hist)
        lay.addWidget(btn, 0, Qt.AlignLeft)
        lay.addStretch()
        return tab

    # ---- Settings Tab ----
    def _cfg_tab(self):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("cfgContent")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setSpacing(12)

        t = QLabel("Settings")
        t.setObjectName("title")
        t.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lay.addWidget(t)

        def slbl(s):
            l = QLabel(s)
            l.setObjectName("statLabel")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            l.setFixedWidth(150)
            l.setStyleSheet("color: rgba(255,255,255,0.55);")
            return l

        def ulbl(s):
            l = QLabel(s)
            l.setObjectName("statLabel")
            l.setStyleSheet("color: rgba(255,255,255,0.35);")
            return l

        def spin(k, lo, hi):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(self.config[k])
            s.setFixedWidth(160)
            return s

        lc = NeoCard(shadow_radius=14)
        gl = QGridLayout(lc)
        gl.setContentsMargins(20, 14, 20, 14)
        gl.setHorizontalSpacing(14)
        gl.setVerticalSpacing(9)
        gl.setColumnStretch(0, 0)
        gl.setColumnStretch(1, 1)
        gl.setColumnStretch(2, 0)

        gl.addWidget(slbl("MAX VOLUME"), 0, 0)
        self.sp_vol = spin("max_volume_pct", 10, 100)
        gl.addWidget(self.sp_vol, 0, 1, Qt.AlignLeft)
        gl.addWidget(ulbl("%"), 0, 2, Qt.AlignLeft)

        gl.addWidget(slbl("VOLUME CAP"), 1, 0)
        self.sp_cap = spin("volume_cap_pct", 10, 100)
        gl.addWidget(self.sp_cap, 1, 1, Qt.AlignLeft)
        gl.addWidget(ulbl("%"), 1, 2, Qt.AlignLeft)

        gl.addWidget(slbl("MAX SESSION"), 2, 0)
        self.sp_sess = spin("max_session_minutes", 5, 240)
        gl.addWidget(self.sp_sess, 2, 1, Qt.AlignLeft)
        gl.addWidget(ulbl("min"), 2, 2, Qt.AlignLeft)

        gl.addWidget(slbl("MAX DAILY"), 3, 0)
        self.sp_daily = spin("max_daily_minutes", 30, 600)
        gl.addWidget(self.sp_daily, 3, 1, Qt.AlignLeft)
        gl.addWidget(ulbl("min"), 3, 2, Qt.AlignLeft)

        gl.addWidget(slbl("BREAK EVERY"), 4, 0)
        self.sp_brk = spin("break_interval_minutes", 15, 120)
        gl.addWidget(self.sp_brk, 4, 1, Qt.AlignLeft)
        gl.addWidget(ulbl("min"), 4, 2, Qt.AlignLeft)

        gl.addWidget(slbl("BREAK LENGTH"), 5, 0)
        self.sp_dur = spin("break_duration_minutes", 1, 60)
        gl.addWidget(self.sp_dur, 5, 1, Qt.AlignLeft)
        gl.addWidget(ulbl("min"), 5, 2, Qt.AlignLeft)
        lay.addWidget(lc)

        ec = NeoCard(shadow_radius=12)
        el = QGridLayout(ec)
        el.setContentsMargins(20, 14, 20, 14)
        el.setHorizontalSpacing(14)
        el.setVerticalSpacing(9)
        el.setColumnStretch(0, 0)
        el.setColumnStretch(1, 1)

        el.addWidget(slbl("EQUIPMENT TYPE"), 0, 0)
        self.eq_combo = QComboBox()
        self.eq_combo.addItems(["In-Ear IEMs", "Wireless Earbuds", "Over-Ear Headphones"])
        self.eq_combo.setCurrentText(self.config["equipment_type"])
        self.eq_combo.setFixedWidth(160)
        self._style_combo_view(self.eq_combo)
        el.addWidget(self.eq_combo, 0, 1, Qt.AlignLeft)

        el.addWidget(slbl("EQUIPMENT NAME"), 1, 0)
        self.eq_name = QLineEdit(self.config.get("equipment_name", "Default"))
        self.eq_name.setFixedWidth(160)
        el.addWidget(self.eq_name, 1, 1, Qt.AlignLeft)
        lay.addWidget(ec)

        nc = NeoCard(shadow_radius=12)
        nl = QVBoxLayout(nc)
        nl.setContentsMargins(20, 14, 20, 14)
        nl.setSpacing(8)
        nl.addWidget(slbl("NOTIFICATIONS"))
        self.cb_cap = QCheckBox(f"Auto-cap volume to {self.config.get('volume_cap_pct', self.config['max_volume_pct'])}% (safe limit)")
        self.cb_cap.setChecked(self.config["volume_cap_enabled"])
        nl.addWidget(self.cb_cap)
        self.cb_vol = QCheckBox("Alert on high volume")
        self.cb_vol.setChecked(self.config["alert_on_volume"])
        nl.addWidget(self.cb_vol)
        self.cb_dur = QCheckBox("Alert on long sessions")
        self.cb_dur.setChecked(self.config["alert_on_duration"])
        nl.addWidget(self.cb_dur)
        self.cb_day = QCheckBox("Alert on daily limit")
        self.cb_day.setChecked(self.config["alert_on_daily_limit"])
        nl.addWidget(self.cb_day)
        lay.addWidget(nc)

        sb = QPushButton("Save Settings")
        sb.setObjectName("saveBtn")
        sb.setFixedWidth(160)
        sb.setFixedHeight(40)
        sb.clicked.connect(self._save)
        lay.addWidget(sb, 0, Qt.AlignLeft)
        lay.addStretch()
        scroll.setWidget(content)
        return tab

    # ---- Tips Tab ----
    def _tips_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setSpacing(10)

        t = QLabel("Ear Care Tips")
        t.setObjectName("title")
        t.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lay.addWidget(t)

        equip = self.config.get("equipment_type", "In-Ear IEMs")
        tips = TIPS.get(equip, TIPS["In-Ear IEMs"])

        tc = NeoCard(shadow_radius=16)
        tl = QVBoxLayout(tc)
        tl.setContentsMargins(18, 14, 18, 14)
        tl.setSpacing(6)
        eq_l = QLabel(f"  {equip}")
        eq_l.setObjectName("sectionTitle")
        tl.addWidget(eq_l)
        for i, tip in enumerate(tips, 1):
            lbl = QLabel(f"  {i}. {tip}")
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: rgba(255,255,255,0.6); padding: 5px 0;")
            tl.addWidget(lbl)
        lay.addWidget(tc)

        gc = NeoCard(shadow_radius=14)
        gl = QVBoxLayout(gc)
        gl.setContentsMargins(18, 14, 18, 14)
        gl.addWidget(slbl := QLabel("General Guidelines"))
        slbl.setObjectName("sectionTitle")
        for g in [
            "Follow the 60/60 rule: Max 60% volume for 60 minutes",
            "Take a 10-minute break every hour of listening",
            "If ears ring or feel full, stop immediately",
            "Use volume-limiting headphones for children",
            "Get a hearing test if you notice changes",
        ]:
            lbl = QLabel(f"    {g}")
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: rgba(255,255,255,0.6); padding: 5px 0;")
            gl.addWidget(lbl)
        lay.addWidget(gc)
        lay.addStretch()
        return tab

    # ---- Tray ----
    def _setup_tray(self):
        self._setup_ipc()
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        self.tray.setToolTip("Ear Health Monitor")
        m = QMenu()
        from PyQt5.QtGui import QPalette, QColor as _QColor
        _mPal = QPalette()
        _mPal.setColor(QPalette.Window,       _QColor("#222222"))
        _mPal.setColor(QPalette.Base,         _QColor("#222222"))
        _mPal.setColor(QPalette.Text,         _QColor("#eaeaea"))
        _mPal.setColor(QPalette.WindowText,   _QColor("#eaeaea"))
        _mPal.setColor(QPalette.Button,       _QColor("#222222"))
        _mPal.setColor(QPalette.ButtonText,   _QColor("#eaeaea"))
        _mPal.setColor(QPalette.Highlight,    _QColor("#eaeaea"))
        _mPal.setColor(QPalette.HighlightedText, _QColor("#1a1a1a"))
        m.setPalette(_mPal)
        sa = QAction("Show", self)
        sa.triggered.connect(self._show)
        m.addAction(sa)
        m.addSeparator()
        ta = QAction("Start", self)
        ta.triggered.connect(self._toggle_session)
        m.addAction(ta)
        xa = QAction("Stop", self)
        xa.triggered.connect(self._stop)
        m.addAction(xa)
        m.addSeparator()
        qa = QAction("Quit", self)
        qa.triggered.connect(self._quit)
        m.addAction(qa)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(lambda r: self._show() if r == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    # ---- Single Instance IPC ----
    def _setup_ipc(self):
        try:
            from PyQt5.QtNetwork import QLocalServer
            self._ipc = QLocalServer(self)
            self._ipc.removeServer("EarHealthMonitor_ipc")
            self._ipc.listen("EarHealthMonitor_ipc")
            self._ipc.newConnection.connect(self._ipc_new)
        except Exception:
            self._ipc = None

    def _ipc_new(self):
        try:
            c = self._ipc.nextPendingConnection()
            if c:
                c.readyRead.connect(self._ipc_read)
                c.disconnected.connect(c.deleteLater)
        except Exception:
            pass

    def _ipc_read(self, *_):
        try:
            s = self.sender()
            if s and s.isValid() and s.bytesAvailable():
                if b"show" in bytes(s.readAll()):
                    self._show()
        except Exception:
            pass

    # ---- Volume I/O ----
    def _get_sys_vol(self):
        try:
            from pycaw.pycaw import AudioUtilities
            d = AudioUtilities.GetSpeakers()
            if d and d.EndpointVolume:
                return int(d.EndpointVolume.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            pass
        return 50

    def _enforce_volume_cap(self) -> bool:
        if not self.config.get("volume_cap_enabled", True):
            return False
        cap = self.config.get("volume_cap_pct", self.config["max_volume_pct"])
        cur = self._get_sys_vol()
        if cur > cap:
            self._set_sys_vol(cap)
            now = time.time()
            if now - getattr(self, "_last_cap_at", 0) > 20:
                self._last_cap_at = now
                self.toast.show_toast("warning",
                    f"Volume capped to {cap}% — safe listening limit")
            return True
        return False

    def _set_sys_vol(self, v):
        try:
            from pycaw.pycaw import AudioUtilities
            d = AudioUtilities.GetSpeakers()
            if d and d.EndpointVolume:
                d.EndpointVolume.SetMasterVolumeLevelScalar(v / 100.0, None)
        except Exception:
            pass

    def _vol_changed(self, v):
        self.vdisp.set_value(v)
        if not self._syncing:
            self._set_sys_vol(v)
        if v > self.config["max_volume_pct"]:
            self.vstat.setText("Above safe limit")
            self.vstat.setObjectName("volumeStatusDanger")
        else:
            self.vstat.setText("Safe")
            self.vstat.setObjectName("volumeStatusSafe")
        self.vstat.style().unpolish(self.vstat)
        self.vstat.style().polish(self.vstat)

    # ---- Session Control ----
    def _toggle_session(self):
        if self.monitor.session_active:
            r = self.monitor.stop_session()
            self._session_end(r)
        else:
            self.monitor.start_session()
            self._session_start()

    def _toggle_pause(self):
        if not self.monitor.session_active:
            return
        if self._paused:
            self.monitor.resume_session()
            self._paused = False
            self.pause_btn.setText("Pause")
            self.ss_lbl.setText("Active")
            self.ss_lbl.setObjectName("sessionActive")
        else:
            self.monitor.pause_session()
            self._paused = True
            self.pause_btn.setText("Resume")
            self.ss_lbl.setText("Paused")
            self.ss_lbl.setObjectName("sessionPaused")
        self._repolish(self.ss_lbl)

    def _stop(self):
        if self.monitor.session_active:
            r = self.monitor.stop_session()
            self._session_end(r)

    def _session_start(self):
        self.start_btn.setText("Stop")
        self.start_btn.setObjectName("danger")
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.ss_lbl.setText("Active")
        self.ss_lbl.setObjectName("sessionActive")
        self._repolish(self.start_btn)
        self._repolish(self.ss_lbl)
        self.dot.set_status("safe")
        self.dot_lbl.setText("Active")
        self.statusBar().showMessage("  Monitoring started")

    def _session_end(self, rec):
        self.start_btn.setText("Start Session")
        self.start_btn.setObjectName("primary")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self.stop_btn.setEnabled(False)
        self._paused = False
        self.ss_lbl.setText("Inactive")
        self.ss_lbl.setObjectName("sessionEnded")
        self._repolish(self.start_btn)
        self._repolish(self.ss_lbl)
        self.dot.set_status("idle")
        self.dot_lbl.setText("Idle")
        if rec:
            self.toast.show_toast("info", f"Session: {rec.duration_minutes:.0f} min | Peak {rec.max_volume_pct:.0f}%")
            self.statusBar().showMessage(f"  Ended: {rec.duration_minutes:.0f} min, Avg {rec.avg_volume_pct:.0f}%")
        self._refresh_daily()

    def _on_alert(self, sev, msg):
        if sev == "critical":
            winsound.MessageBeep(winsound.MB_ICONHAND)
        elif sev == "warning":
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        self.toast.show_toast(sev, msg)
        self.tray.showMessage(sev.upper(), msg, QSystemTrayIcon.Warning, 4000)

    # ---- Timer Update ----
    def _update_display(self):
        capped = self._enforce_volume_cap()

        sv = self._get_sys_vol()
        if abs(sv - self.vslider.value()) > 2:
            self._syncing = True
            self.vslider.setValue(sv)
            self._syncing = False
        self.vdisp.set_value(sv)
        if sv > self.config["max_volume_pct"]:
            self.vstat.setText("Above safe limit")
            self.vstat.setObjectName("volumeStatusDanger")
        else:
            self.vstat.setText("Safe")
            self.vstat.setObjectName("volumeStatusSafe")
        self._repolish(self.vstat)

        if not self.monitor.session_active:
            return


        elapsed = self.monitor._pause_accum / 60.0 if self._paused else self.monitor._elapsed_minutes()
        mins = int(elapsed)
        secs = int((elapsed - mins) * 60)
        self.elapsed_lbl.setText(f"{mins}:{secs:02d}")

        alerts = self.monitor.check_volume(sv) + self.monitor.check_duration()
        for a in alerts:
            self.alert_signal.alert_triggered.emit(a["severity"], a["message"])

        s = self.monitor.volume_samples
        if s:
            self._avg_sess.set_value(sum(s) / len(s))
            self._peak_sess.set_value(max(s))
        self.sa_val.set_value(len(self.monitor.alerts_triggered))

        mx = self.config["max_session_minutes"]
        bi = self.config["break_interval_minutes"]

        if elapsed >= mx:
            st, sc, gs, ds = "LIMIT EXCEEDED", "critical", "critical", "critical"
            tr = "red"
        elif elapsed >= bi * 0.8:
            st, sc, gs, ds = "Break recommended", "warning", "warn", "warn"
            tr = "yellow"
        else:
            st, sc, gs, ds = "Active", "sessionActive", "safe", "safe"
            tr = "green"

        self.ss_lbl.setText(st)
        self.ss_lbl.setObjectName(sc)
        self._repolish(self.ss_lbl)
        self._update_gauge_today()
        self.dot.set_status(ds)
        if tr == "green":
            self.dot_lbl.setText("Active")
        elif tr == "yellow":
            self.dot_lbl.setText("Break soon")
        else:
            self.dot_lbl.setText("Over limit!")

    def _update_gauge_today(self):
        today = self.config["max_daily_minutes"]
        recorded = get_today_stats().total_minutes
        live = 0.0
        if self.monitor.session_active:
            live = self.monitor._pause_accum / 60.0 if self._paused else self.monitor._elapsed_minutes()
        total = recorded + live
        self.gauge.set_target(total, today)
        self.dbar.setMaximum(today)
        self.dbar.setValue(int(total))
        self.dlbl.setText(f"{total:.0f} / {today} min")
        if total >= today:
            self.gauge.set_status("critical")
        elif total >= today * 0.8:
            self.gauge.set_status("warn")
        else:
            self.gauge.set_status("safe")

    # ---- Refresh helpers ----
    def _refresh_daily(self):
        self._update_gauge_today()
        d = get_today_stats()
        self.sc_val.set_value(d.session_count)
        self.av_val.set_value(d.avg_volume_pct)

    def _refresh_hist(self):
        h = load_history()
        if not h:
            self.h_text.setText("No usage history yet.\nStart a session to begin tracking.")
            return
        lines = []
        for r in reversed(h[-50:]):
            s = str(r.get("start_time", "?"))[:16].replace("T", " ")
            dur = r.get("duration_minutes", 0)
            avg = r.get("avg_volume_pct", 0)
            mx = r.get("max_volume_pct", 0)
            al = len(r.get("alerts_triggered") or [])
            lines.append(f"[{s}]  {dur:5.0f}m  |  Avg {avg:4.0f}%  |  Peak {mx:4.0f}%  |  Alerts {al}")
        self.h_text.setText("\n".join(lines))

    def _save(self):
        self.config["max_volume_pct"] = self.sp_vol.value()
        self.config["volume_cap_pct"] = self.sp_cap.value()
        self.config["max_session_minutes"] = self.sp_sess.value()
        self.config["max_daily_minutes"] = self.sp_daily.value()
        self.config["break_interval_minutes"] = self.sp_brk.value()
        self.config["break_duration_minutes"] = self.sp_dur.value()
        self.config["equipment_type"] = self.eq_combo.currentText()
        self.config["equipment_name"] = self.eq_name.text().strip() or "Default"
        self.config["volume_cap_enabled"] = self.cb_cap.isChecked()
        self.config["alert_on_volume"] = self.cb_vol.isChecked()
        self.config["alert_on_duration"] = self.cb_dur.isChecked()
        self.config["alert_on_daily_limit"] = self.cb_day.isChecked()
        save_config(self.config)
        self.monitor.config = self.config
        self.cb_cap.setText(f"Auto-cap volume to {self.config['volume_cap_pct']}% (safe limit)")
        self.toast.show_toast("info", "Settings saved")
        self._refresh_daily()

    def _repolish(self, w):
        w.style().unpolish(w)
        w.style().polish(w)

    def _style_combo_view(self, combo):
        from PyQt5.QtGui import QPalette, QColor
        view = combo.view()
        pal = view.palette()
        pal.setColor(QPalette.Window, QColor(36, 36, 36))
        pal.setColor(QPalette.Base, QColor(36, 36, 36))
        pal.setColor(QPalette.Text, QColor(234, 234, 234))
        pal.setColor(QPalette.WindowText, QColor(234, 234, 234))
        pal.setColor(QPalette.Highlight, QColor(234, 234, 234))
        pal.setColor(QPalette.HighlightedText, QColor(26, 26, 26))
        view.setPalette(pal)

    def _show(self):
        self.showNormal()
        self.activateWindow()

    def _quit(self):
        if self.monitor.session_active:
            r = QMessageBox.question(self, "Active Session",
                "Stop session before quitting?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.Yes:
                self.monitor.stop_session()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self.tray.showMessage("Ear Health Monitor", "Running in background.", QSystemTrayIcon.Information, 2000)


def main():
    from PyQt5.QtCore import QSharedMemory
    mem = QSharedMemory("EarHealthMonitor_inst")
    if not mem.create(1):
        try:
            from PyQt5.QtNetwork import QLocalSocket
            s = QLocalSocket()
            s.connectToServer("EarHealthMonitor_ipc")
            if s.waitForConnected(400):
                s.write(b"show")
                s.flush()
                s.waitForBytesWritten(300)
                s.disconnectFromServer()
        except Exception:
            pass
        return

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Ear Health Monitor")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_QSS)
    w = MainWindow()
    w._single = mem
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
