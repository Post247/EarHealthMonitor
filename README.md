# Ear Health Monitor

A Windows desktop app (PyQt5) that protects your hearing while listening on a PC.

## Features

- **Live volume monitoring** — reads the real system audio level and shows it on an animated slider
- **60/60 safe-listening guard** — flags volume already above your safe limit
- **Auto volume cap** — optionally clamps the system volume to a configurable safe percentage (20s cooldown with a toast warning)
- **Session tracking** — start/stop/pause listening sessions with elapsed time, avg/peak volume and alert counts
- **Time limits** — per-session, daily and break-interval limits with desktop toasts
- **Usage history** — last 7 days bar chart + past-session log (stored locally in `data/`)
- **Equipment profiles** — In-Ear IEMs / Wireless Earbuds / Over-Ear Headphones, each with tailored ear-care tips
- **Tray integration** — runs in the system tray; single-instance enforcement (second launch focuses the existing window)
- **Nothing-OS-style dark UI** — monospace, minimal, high contrast

## Requirements

- Python 3.8+
- PyQt5
- pycaw (for volume control)

```bash
pip install PyQt5 pycaw
```

## Running

Run the built binary with `EarHealthMonitor.bat`, or from source:

```bash
python app.py
```

The app minimises to the system tray on close — quit via the tray menu.

## Build (PyInstaller)

```bash
python -m PyInstaller --onefile --windowed --name "EarHealthMonitor" \
  --add-data "monitor.py;." --add-data "widgets.py;." --add-data "ui_theme.py;." app.py
```

## Configuration

Settings (volume cap, session limits, break length, equipment, notification toggles) are
saved to `data/config.json`. Usage data is stored in `data/usage_history.json`.