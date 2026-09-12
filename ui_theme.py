APP_QSS = """
* {
    font-family: "Segoe UI";
    color: #eaeaea;
    font-weight: 400;
}

QMainWindow, QWidget#root {
    background-color: #1a1a1a;
}

/* ---- Labels ---- */
QLabel {
    background: transparent;
}
QLabel#title {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 16px;
    font-weight: 700;
    color: #eaeaea;
    letter-spacing: 3px;
}
QLabel#subtitle {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.38);
    letter-spacing: 1px;
}
QLabel#sectionTitle {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 10px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.42);
    letter-spacing: 2px;
}
QLabel#statValue {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 22px;
    font-weight: 700;
    color: #eaeaea;
}
QLabel#statLabel {
    font-size: 9px;
    color: rgba(255, 255, 255, 0.32);
    letter-spacing: 1px;
}
QLabel#elapsed {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 32px;
    font-weight: 700;
    color: #eaeaea;
}
QLabel#sessionActive {
    font-size: 11px;
    font-weight: 600;
    color: #34d399;
    letter-spacing: 1px;
}
QLabel#sessionPaused {
    font-size: 11px;
    font-weight: 600;
    color: #fbbf24;
    letter-spacing: 1px;
}
QLabel#sessionEnded {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.32);
    letter-spacing: 1px;
}
QLabel#critical {
    color: #f87171;
    font-weight: 700;
}
QLabel#warning {
    color: #fbbf24;
    font-weight: 600;
}
QLabel#volumeStatusSafe {
    font-size: 10px;
    font-weight: 600;
    color: #34d399;
    letter-spacing: 1px;
}
QLabel#volumeStatusDanger {
    font-size: 10px;
    font-weight: 600;
    color: #f87171;
    letter-spacing: 1px;
}
QLabel#dailyLabel {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.42);
}

/* ---- Menu ---- */
QMenu {
    background-color: #222222;
    color: #eaeaea;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    color: #eaeaea;
    background: transparent;
    padding: 7px 22px;
    border-radius: 6px;
    font-size: 12px;
}
QMenu::item:selected {
    background: rgba(255, 255, 255, 0.12);
}
QMenu::item:disabled {
    color: rgba(255, 255, 255, 0.35);
}
QMenu::separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 4px 10px;
}

/* ---- Tab Widget ---- */
QTabWidget::pane {
    border: none;
    background: transparent;
}
QScrollArea {
    background: #1a1a1a;
    border: none;
}
QScrollBar:vertical {
    background: #1a1a1a;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.2);
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
QWidget#cfgContent {
    background: #1a1a1a;
}
QTabBar::tab {
    background: transparent;
    color: rgba(255, 255, 255, 0.32);
    padding: 10px 22px;
    border: none;
    border-bottom: 1.5px solid transparent;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    min-width: 65px;
}
QTabBar::tab:selected {
    color: #eaeaea;
    border-bottom-color: #eaeaea;
}
QTabBar::tab:hover:!selected {
    color: rgba(255, 255, 255, 0.6);
}

/* ---- Buttons ---- */
QPushButton#primary {
    background: #eaeaea;
    color: #1a1a1a;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
    border: 1.5px solid #eaeaea;
    border-radius: 12px;
    padding: 12px 20px;
}
QPushButton#primary:hover {
    background: #ffffff;
    border-color: #ffffff;
}
QPushButton#primary:pressed {
    background: #d0d0d0;
}
QPushButton#primary:disabled {
    background: transparent;
    border-color: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.18);
}
QPushButton#accent {
    background: transparent;
    color: #eaeaea;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
    border: 1.5px solid rgba(255, 255, 255, 0.4);
    border-radius: 12px;
    padding: 12px 20px;
}
QPushButton#accent:hover {
    border-color: #eaeaea;
    background: rgba(255, 255, 255, 0.06);
}
QPushButton#accent:disabled {
    border-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.15);
}
QPushButton#danger {
    background: transparent;
    color: #f87171;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
    border: 1.5px solid #f87171;
    border-radius: 12px;
    padding: 12px 20px;
}
QPushButton#danger:hover {
    background: rgba(248, 113, 113, 0.1);
    border-color: #fca5a5;
}
QPushButton#danger:disabled {
    border-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.15);
}
QPushButton#ghost {
    background: transparent;
    color: rgba(255, 255, 255, 0.5);
    font-family: "Cascadia Code", "Consolas", monospace;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 1px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 10px 18px;
}
QPushButton#ghost:hover {
    border-color: rgba(255, 255, 255, 0.25);
    color: #eaeaea;
}
QPushButton#saveBtn {
    background: #eaeaea;
    color: #1a1a1a;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
    border: 1.5px solid #eaeaea;
    border-radius: 12px;
    padding: 12px 20px;
}
QPushButton#saveBtn:hover {
    background: #ffffff;
}

/* ---- Slider ---- */
QSlider::groove:horizontal {
    border: none;
    height: 3px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 1.5px;
}
QSlider::handle:horizontal {
    width: 18px;
    height: 18px;
    margin: -8px 0;
    background: #eaeaea;
    border: none;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
}
QSlider::sub-page:horizontal {
    background: #eaeaea;
    border-radius: 1.5px;
}
QSlider::add-page:horizontal {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 1.5px;
}

/* ---- Progress Bar ---- */
QProgressBar {
    background: rgba(255, 255, 255, 0.06);
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    border-radius: 3px;
    background: #eaeaea;
}

/* ---- SpinBox ---- */
QSpinBox {
    background: rgba(255, 255, 255, 0.06);
    color: #eaeaea;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 6px 10px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    min-height: 20px;
    selection-background-color: rgba(255, 255, 255, 0.15);
}
QSpinBox:focus {
    border-color: rgba(255, 255, 255, 0.35);
}
QSpinBox::up-button, QSpinBox::down-button {
    background: transparent;
    border: none;
    border-radius: 4px;
    width: 18px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: rgba(255, 255, 255, 0.08);
}
QSpinBox::up-arrow, QSpinBox::down-arrow {
    width: 6px;
    height: 6px;
}

/* ---- ComboBox ---- */
QComboBox {
    background: rgba(255, 255, 255, 0.06);
    color: #eaeaea;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    min-height: 20px;
}
QComboBox:focus {
    border-color: rgba(255, 255, 255, 0.35);
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
}
QLineEdit {
    background: rgba(255, 255, 255, 0.06);
    color: #eaeaea;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    min-height: 20px;
    selection-background-color: rgba(255, 255, 255, 0.15);
}
QLineEdit:focus {
    border-color: rgba(255, 255, 255, 0.35);
}
QComboBox QAbstractItemView {
    background-color: #242424;
    color: #eaeaea;
    border: 1px solid rgba(255, 255, 255, 0.15);
    selection-background-color: #eaeaea;
    selection-color: #1a1a1a;
    outline: none;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 4px 10px;
    color: #eaeaea;
}
QComboBox QAbstractItemView::item:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #eaeaea;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #eaeaea;
    color: #1a1a1a;
}

/* ---- CheckBox ---- */
QCheckBox {
    color: rgba(255, 255, 255, 0.65);
    font-size: 12px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid rgba(255, 255, 255, 0.22);
    border-radius: 4px;
    background: transparent;
}
QCheckBox::indicator:checked {
    background: #eaeaea;
    border-color: #eaeaea;
}
QCheckBox::indicator:hover {
    border-color: rgba(255, 255, 255, 0.5);
}

/* ---- QTextEdit ---- */
QTextEdit {
    background: rgba(255, 255, 255, 0.04);
    color: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 11px;
    selection-background-color: rgba(255, 255, 255, 0.1);
}

/* ---- StatusBar ---- */
QStatusBar {
    background: #161616;
    color: rgba(255, 255, 255, 0.28);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 10px;
    padding: 3px 10px;
}

/* ---- ScrollBar ---- */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.25);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""