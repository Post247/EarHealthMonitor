import time
import json
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional


if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(APP_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "usage_history.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "max_volume_pct": 60,
    "volume_cap_pct": 60,
    "max_session_minutes": 60,
    "max_daily_minutes": 180,
    "break_interval_minutes": 60,
    "break_duration_minutes": 10,
    "volume_cap_enabled": True,
    "alert_on_volume": True,
    "alert_on_duration": True,
    "alert_on_daily_limit": True,
    "equipment_type": "In-Ear IEMs",
    "equipment_name": "Default IEMs",
    "auto_start_monitoring": True,
}

TIPS = {
    "In-Ear IEMs": [
        "Use memory foam tips for better seal and comfort",
        "Clean eartips weekly with isopropyl alcohol",
        "Rotate between tip sizes if ears feel sore",
        "Avoid sharing earphones to prevent infections",
        "Let earphones air-dry after use before storing",
    ],
    "Wireless Earbuds": [
        "Clean charging case contacts weekly",
        "Remove earbuds when not playing audio",
        "Wipe earbuds with dry microfiber cloth after use",
        "Replace silicone tips every 3-6 months",
        "Store in case when not in use to reduce moisture",
    ],
    "Over-Ear Headphones": [
        "Stretch headband gently if clamp force is too high",
        "Replace ear pads every 6-12 months",
        "Air out ear cups after extended use",
        "Use a headphone stand to maintain shape",
        "Clean ear pads with mild soap solution monthly",
    ],
}


@dataclass
class SessionRecord:
    start_time: str
    end_time: str
    duration_minutes: float
    avg_volume_pct: float
    max_volume_pct: float
    equipment_type: str
    equipment_name: str
    alerts_triggered: list


@dataclass
class DailyStats:
    date: str
    total_minutes: float
    session_count: int
    avg_volume_pct: float
    max_volume_pct: float
    alerts_count: int


def load_config() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
                saved = json.load(f)
                config = DEFAULT_CONFIG.copy()
                if isinstance(saved, dict):
                    config.update(saved)
                return config
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_history() -> list:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError, ValueError):
            return []
    return []


def save_history(history: list):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def add_session(record: SessionRecord):
    history = load_history()
    history.append(asdict(record))
    save_history(history)


def get_today_stats() -> DailyStats:
    history = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    today_sessions = [
        s for s in history if s["start_time"].startswith(today)
    ]

    if not today_sessions:
        return DailyStats(
            date=today,
            total_minutes=0,
            session_count=0,
            avg_volume_pct=0,
            max_volume_pct=0,
            alerts_count=0,
        )

    total_min = sum(s["duration_minutes"] for s in today_sessions)
    count = len(today_sessions)
    avg_vol = sum(s["avg_volume_pct"] for s in today_sessions) / count
    max_vol = max(s["max_volume_pct"] for s in today_sessions)
    alerts = sum(len(s.get("alerts_triggered", [])) for s in today_sessions)

    return DailyStats(
        date=today,
        total_minutes=round(total_min, 1),
        session_count=count,
        avg_volume_pct=round(avg_vol, 1),
        max_volume_pct=round(max_vol, 1),
        alerts_count=alerts,
    )


def get_week_stats() -> list:
    history = load_history()
    today = datetime.now().date()
    week_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_sessions = [s for s in history if s["start_time"].startswith(day_str)]
        total = sum(s["duration_minutes"] for s in day_sessions)
        week_data.append({"date": day_str, "minutes": round(total, 1)})

    return week_data


class ListeningMonitor:
    def __init__(self, config: dict):
        self.config = config
        self.session_active = False
        self.session_start: Optional[float] = None
        self.volume_samples: list = []
        self.alerts_triggered: list = []
        self._last_volume_alert = 0
        self._last_break_alert = 0
        self._last_duration_alert = 0

    def start_session(self):
        self.session_active = True
        self.session_start = time.time()
        self.volume_samples = []
        self.alerts_triggered = []
        self.paused = False
        self._pause_accum = 0.0
        self._resume_point = self.session_start

    def pause_session(self):
        if self.session_active and not self.paused:
            self._pause_accum += time.time() - self._resume_point
            self.paused = True

    def resume_session(self):
        if self.session_active and self.paused:
            self._resume_point = time.time()
            self.paused = False

    def _elapsed_minutes(self) -> float:
        if not self.session_active or self.session_start is None:
            return 0.0
        if self.paused:
            return self._pause_accum / 60.0
        return (self._pause_accum + (time.time() - self._resume_point)) / 60.0

    def stop_session(self) -> Optional[SessionRecord]:
        if not self.session_active or self.session_start is None:
            return None

        duration = self._elapsed_minutes()
        avg_vol = (
            sum(self.volume_samples) / len(self.volume_samples)
            if self.volume_samples
            else 0
        )
        max_vol = max(self.volume_samples) if self.volume_samples else 0

        record = SessionRecord(
            start_time=datetime.fromtimestamp(self.session_start).isoformat(),
            end_time=datetime.now().isoformat(),
            duration_minutes=round(duration, 2),
            avg_volume_pct=round(avg_vol, 1),
            max_volume_pct=round(max_vol, 1),
            equipment_type=self.config.get("equipment_type", "Unknown"),
            equipment_name=self.config.get("equipment_name", "Unknown"),
            alerts_triggered=self.alerts_triggered.copy(),
        )

        add_session(record)
        self.session_active = False
        self.session_start = None
        return record

    def check_volume(self, current_volume_pct: float) -> list:
        if not self.session_active:
            return []

        self.volume_samples.append(current_volume_pct)
        new_alerts = []
        now = time.time()

        if self.config["alert_on_volume"] and current_volume_pct > self.config["max_volume_pct"]:
            if now - self._last_volume_alert > 300:
                alert = {
                    "type": "high_volume",
                    "message": f"Volume at {current_volume_pct:.0f}% exceeds safe limit of {self.config['max_volume_pct']}%",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "warning",
                }
                new_alerts.append(alert)
                self.alerts_triggered.append(alert)
                self._last_volume_alert = now

        return new_alerts

    def check_duration(self) -> list:
        if not self.session_active or self.session_start is None:
            return []

        elapsed_min = self._elapsed_minutes()
        new_alerts = []
        now = time.time()

        if self.config["alert_on_duration"]:
            max_min = self.config["max_session_minutes"]
            if elapsed_min >= max_min and now - self._last_duration_alert > 300:
                alert = {
                    "type": "session_too_long",
                    "message": f"Session duration {elapsed_min:.0f} min exceeds safe limit of {max_min} min",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "critical",
                }
                new_alerts.append(alert)
                self.alerts_triggered.append(alert)
                self._last_duration_alert = now

        if now - self._last_break_alert > 300:
            break_interval = self.config["break_interval_minutes"]
            if elapsed_min >= break_interval and elapsed_min % break_interval < 1:
                alert = {
                    "type": "break_reminder",
                    "message": f"Time for a {self.config['break_duration_minutes']}-minute break! You've been listening for {elapsed_min:.0f} min.",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "info",
                }
                new_alerts.append(alert)
                self._last_break_alert = now

        return new_alerts

    def get_session_info(self) -> dict:
        if not self.session_active:
            return {"active": False}

        elapsed = self._elapsed_minutes()
        avg_vol = (
            sum(self.volume_samples) / len(self.volume_samples)
            if self.volume_samples
            else 0
        )
        max_vol = max(self.volume_samples) if self.volume_samples else 0

        return {
            "active": True,
            "elapsed_minutes": round(elapsed, 1),
            "avg_volume": round(avg_vol, 1),
            "max_volume": round(max_vol, 1),
            "volume_samples": len(self.volume_samples),
            "alerts_triggered": len(self.alerts_triggered),
        }
