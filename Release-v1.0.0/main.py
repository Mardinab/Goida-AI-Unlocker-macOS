import sys
import tempfile
import urllib.request
import subprocess
import os
import threading
import atexit
import time as _time
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect, QStackedWidget, QSizePolicy, QToolButton, QAbstractButton, QGridLayout
    from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QSize
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFontMetrics
    from PySide6.QtSvg import QSvgRenderer
except ImportError:
    print("Ошибка: библиотека PySide6 не установлена. Пожалуйста, установите ее командой: pip install PySide6")
    sys.exit(1)
from typing import Optional
import json
import textwrap as _tw

# ---------------- additional hosts configs ----------------
ADDITIONAL_HOSTS_URL = "https://raw.githubusercontent.com/AvenCores/Goida-AI-Unlocker/refs/heads/main/additional_hosts.py"
# ----------------------------------------------------------

APP_VERSION = "0.0.0"

# ----------------------- Safe temp removal helper -----------------------
def _safe_remove(path: str, retries: int = 3, delay: float = 0.3):
    """Attempt to remove a temporary file."""
    for _ in range(retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError:
            _time.sleep(delay)
        except Exception:
            break

    try:
        if os.path.exists(path):
            atexit.register(lambda p=path: os.path.exists(p) and os.remove(p))
    except Exception:
        pass

# ----------- Fetch remote additional hosts -------------------
def _fetch_remote_additional() -> tuple[str, str]:
    """Return (version, hosts_add) fetched from remote additional_hosts.py."""
    import time as _t
    try:
        raw_txt = urllib.request.urlopen(f"{ADDITIONAL_HOSTS_URL}?t={int(_t.time())}", timeout=10).read().decode("utf-8", errors="ignore")
        import re as _re, textwrap as _tw
        ver_match = _re.search(r'version_add\s*=\s*["\']([^"\']+)["\']', raw_txt)
        hosts_match = _re.search(r'hosts_add\s*=\s*"""(.*?)"""', raw_txt, _re.S)
        version = ver_match.group(1) if ver_match else ""
        hosts_block = hosts_match.group(1).strip() if hosts_match else ""
        hosts_block = _tw.dedent(hosts_block)
        return version, hosts_block
    except Exception:
        return "", ""

def check_installation():
    """Check if the hosts bypass is installed."""
    if sys.platform != 'darwin':
        return False
    hosts_path = "/etc/hosts"
    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return "# Блокировка реально плохих сайтов" in content
    except Exception:
        return False

def update_hosts_as_admin():
    """Download and install updated hosts file. Returns True on success."""
    if sys.platform != 'darwin':
        print("Эта функция предназначена только для macOS.")
        return False

    url = "https://raw.githubusercontent.com/ImMALWARE/dns.malw.link/refs/heads/master/hosts"
    temp_path: str | None = None
    script_path: str | None = None
    
    try:
        # Download hosts file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.hosts')
        os.close(temp_fd)

        content = urllib.request.urlopen(url).read().decode("utf-8", errors="ignore")

        # Add additional hosts block
        add_ver, add_hosts_remote = _fetch_remote_additional()
        if add_hosts_remote:
            extra_block = f"\n# additional_hosts_version {add_ver}\n{add_hosts_remote.strip()}\n"
            content += extra_block

        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Create shell script for admin operations
        script_fd, script_path = tempfile.mkstemp(suffix='.sh')
        os.close(script_fd)
        
        shell_script = f'''#!/bin/bash
cp "{temp_path}" /etc/hosts
chmod 644 /etc/hosts
dscacheutil -flushcache
killall -HUP mDNSResponder
'''
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(shell_script)
        
        os.chmod(script_path, 0o755)

        # Execute with admin privileges using AppleScript
        applescript = f'''
        do shell script "'{script_path}'" with administrator privileges
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            _time.sleep(1)
            return True
        else:
            print(f"Ошибка: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    finally:
        if temp_path:
            _safe_remove(temp_path)
        if script_path:
            _safe_remove(script_path)

def is_macos_dark_theme():
    """Check if macOS is using dark theme."""
    if sys.platform != 'darwin':
        return False
    try:
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and 'Dark' in result.stdout
    except Exception:
        return False

def get_stylesheet(dark):
    if dark:
        return {
            "main": """
                QMainWindow {
                    background: #1e2228;
                    border-radius: 16px;
                }
                QWidget {
                    border-radius: 16px;
                    background: #1e2228;
                }
                QWidget#titleBar {
                    background: transparent;
                    border-top-left-radius: 16px;
                    border-top-right-radius: 16px;
                    border-bottom-left-radius: 0;
                    border-bottom-right-radius: 0;
                    border-bottom: 1px solid #2d333b;
                }
            """,
            "label": """
                QLabel {
                    font-size: 18px;
                    padding: 16px 0 8px 0;
                    color: #f3f6fd;
                    font-weight: 500;
                }
            """,
            "button1": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2d7dff, stop:1 #2962d9);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #246cf0, stop:1 #235bcc);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e5ed2, stop:1 #1c52b0);
                    padding: 14px 0 10px 0;
                }
            """,
            "button2": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e06c75, stop:1 #d64c58);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b94a59, stop:1 #a43b47);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a84a57, stop:1 #973f4a);
                    padding: 14px 0 10px 0;
                }
            """,
            "theme": """
                QPushButton, QToolButton {
                    background: #e6e8ec;
                    color: #222;
                    border: 1.5px solid #cfd4db;
                    border-radius: 8px;
                    padding: 10px 0;
                    font-size: 15px;
                    font-weight: 500;
                }
                QPushButton:hover, QToolButton:hover {
                    background: #d1d4d8;
                }
                QPushButton:pressed, QToolButton:pressed {
                    background: #bfc3c9;
                    padding: 12px 0 8px 0;
                }
            """,
            "theme_center_small": """
                QPushButton {
                    background: #e6e8ec;
                    color: #222;
                    border: 1.5px solid #cfd4db;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                    min-width: 140px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #d1d4d8;
                }
                QPushButton:pressed {
                    background: #bfc3c9;
                    padding: 10px 16px 6px 16px;
                }
            """,
            "about_title_style": "font-size:25px; margin-bottom:4px;",
            "about_title_html": f"<b style='color:#f3f6fd;'>Goida AI Unlocker</b> <span style='font-size:15px; color:#bfc9db;'>(v{APP_VERSION} macOS)</span>",
            "about_info_html": "<span style='font-size:11px; color:#888;'>Оригинальный автор: AvenCores<br>macOS версия: seidenov</span>",
            "about_link_html": "<a href='#' style='color:#2d7dff; text-decoration:none; font-size:13px;'>⟵ В меню</a>",
        }
    else:
        return {
            "main": """
                QMainWindow {
                    background: #ffffff;
                    border-radius: 16px;
                }
                QWidget {
                    border-radius: 16px;
                    background: #ffffff;
                }
                QWidget#titleBar {
                    background: transparent;
                    border-top-left-radius: 16px;
                    border-top-right-radius: 16px;
                    border-bottom-left-radius: 0;
                    border-bottom-right-radius: 0;
                    border-bottom: 1px solid #e1e4e8;
                }
            """,
            "label": """
                QLabel {
                    font-size: 18px;
                    padding: 16px 0 8px 0;
                    color: #1a1a1a;
                    font-weight: 500;
                }
            """,
            "button1": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d4, stop:1 #0063b1);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #006cbd, stop:1 #005291);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005291, stop:1 #004677);
                    padding: 14px 0 10px 0;
                }
            """,
            "button2": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e06c75, stop:1 #d64c58);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b94a59, stop:1 #a43b47);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9e3f4c, stop:1 #8f3640);
                    padding: 14px 0 10px 0;
                }
            """,
            "theme": """
                QPushButton, QToolButton {
                    background: #f3f4f7;
                    color: #1a1a1a;
                    border: 1.5px solid #cfd4db;
                    border-radius: 8px;
                    padding: 10px 0;
                    font-size: 15px;
                    font-weight: 500;
                }
                QPushButton:hover, QToolButton:hover {
                    background: #e6e8ec;
                }
                QPushButton:pressed, QToolButton:pressed {
                    background: #d1d5db;
                    padding: 12px 0 8px 0;
                }
            """,
            "theme_center_small": """
                QPushButton {
                    background: #f3f4f7;
                    color: #1a1a1a;
                    border: 1.5px solid #cfd4db;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                    min-width: 140px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #e6e8ec;
                }
                QPushButton:pressed {
                    background: #d1d5db;
                    padding: 10px 16px 6px 16px;
                }
            """,
            "about_title_style": "font-size:25px; margin-bottom:4px;",
            "about_title_html": f"<b style='color:#1a1a1a;'>Goida AI Unlocker</b> <span style='font-size:15px; color:#555555;'>(v{APP_VERSION} macOS)</span>",
            "about_info_html": "<span style='font-size:11px; color:#666666;'>Оригинальный автор: AvenCores<br>macOS версия: seidenov</span>",
            "about_link_html": "<a href='#' style='color:#0078d4; text-decoration:none; font-size:13px;'>⟵ В меню</a>",
        }

class CustomWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_animating = False
        self.stacked_widget: Optional[QStackedWidget] = None
        self._current_animation: Optional[QPropertyAnimation] = None
        self.dark_theme = False
        self.styles = {}
        self.title_bar: Optional[QWidget] = None

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.title_bar is not None
            and self.title_bar.underMouse()
        ):
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragPos') and self.dragPos:
            delta = event.globalPosition().toPoint() - self.dragPos
            self.move(self.pos() + delta)
            self.dragPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragPos = None

# ----------------------- Hosts version helpers -----------------------

def _extract_update_line(content: bytes) -> str:
    """Return the second line (index 1) from hosts content."""
    try:
        return content.decode("utf-8", errors="ignore").splitlines()[1].strip()
    except Exception:
        return ""

def _extract_additional_version(text: str) -> str:
    """Return version string from line '# additional_hosts_version X'."""
    for line in text.splitlines():
        if line.lower().startswith("# additional_hosts_version"):
            parts = line.strip().split()
            if len(parts) >= 2:
                return parts[-1]
    return ""

def _get_remote_add_version() -> str:
    """Return remote version_add."""
    ver, _ = _fetch_remote_additional()
    return ver

def get_hosts_version_status() -> tuple[str, str]:
    """Return a tuple (status_word, color) describing hosts version state."""
    global _REMOTE_CACHE_TTL, _remote_main_line_cache, _remote_add_ver_cache
    try:
        _REMOTE_CACHE_TTL
    except NameError:
        _REMOTE_CACHE_TTL = 60.0
    try:
        _remote_main_line_cache
    except NameError:
        _remote_main_line_cache = None
    try:
        _remote_add_ver_cache
    except NameError:
        _remote_add_ver_cache = None

    def _get_remote_main_hosts_line_cached() -> str:
        global _remote_main_line_cache
        now = _time.time()
        if (
            _remote_main_line_cache is not None
            and isinstance(_remote_main_line_cache, tuple)
            and now - _remote_main_line_cache[0] < _REMOTE_CACHE_TTL
        ):
            return _remote_main_line_cache[1]
        import time as _t
        remote_url = f"https://raw.githubusercontent.com/ImMALWARE/dns.malw.link/refs/heads/master/hosts?t={int(_t.time())}"
        try:
            line = _extract_update_line(urllib.request.urlopen(remote_url, timeout=10).read())
        except Exception:
            line = ""
        _remote_main_line_cache = (now, line)
        return line

    def _get_remote_add_version_cached() -> str:
        global _remote_add_ver_cache
        now = _time.time()
        if (
            _remote_add_ver_cache is not None
            and isinstance(_remote_add_ver_cache, tuple)
            and now - _remote_add_ver_cache[0] < _REMOTE_CACHE_TTL
        ):
            return _remote_add_ver_cache[1]
        try:
            ver = _get_remote_add_version()
        except Exception:
            ver = ""
        _remote_add_ver_cache = (now, ver)
        return ver

    if sys.platform != "darwin":
        return "Не установлен", "#e06c75"

    hosts_path = "/etc/hosts"
    if not (os.path.exists(hosts_path) and check_installation()):
        return "Не установлен", "#e06c75"

    try:
        with open(hosts_path, "rb") as lf:
            raw_content = lf.read()
            local_line = _extract_update_line(raw_content)
            text_content = raw_content.decode("utf-8", errors="ignore")
            local_add_ver = _extract_additional_version(text_content)

        remote_line = _get_remote_main_hosts_line_cached()
        remote_add_ver = _get_remote_add_version_cached()

        up_to_date = (
            local_line == remote_line and local_line.startswith("#") and
            remote_add_ver and (local_add_ver == remote_add_ver)
        )
        if up_to_date:
            return "Актуально", "#43b581"
        else:
            return "Устарело", "#e06c75"
    except Exception:
        return "Устарело", "#e06c75"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QPushButton:focus { outline: none; }")

    def resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    # ------------------ SVG icon helpers ------------------
    ICON_CACHE: dict[tuple[str, int, str], QIcon] = {}
    RENDERER_CACHE: dict[str, QSvgRenderer] = {}

    def _tint_pixmap(pix: QPixmap, color: QColor) -> QPixmap:
        """Re-color a pixmap while preserving alpha."""
        if pix.isNull():
            return pix
        tinted = QPixmap(pix.size())
        tinted.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tinted)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, pix)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return tinted

    def get_icon(file_name: str, size_px: int | None = None, *, force_dark: bool = False, force_white: bool = False) -> QIcon:
        """Load an SVG from ./icons and tint it depending on current theme."""
        path = resource_path(os.path.join("icons", file_name))
        render_size = size_px or 48
        if force_white:
            tint = QColor("#ffffff")
        elif force_dark or (not main_window.dark_theme):
            tint = QColor("#1a1a1a")
        else:
            tint = QColor("#ffffff")

        cache_key = (path, render_size, tint.name())
        cached_icon = ICON_CACHE.get(cache_key)
        if cached_icon is not None:
            return cached_icon

        renderer = RENDERER_CACHE.get(path)
        if renderer is None:
            renderer = QSvgRenderer(path)
            RENDERER_CACHE[path] = renderer
        pix = QPixmap(render_size, render_size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()

        tinted = _tint_pixmap(pix, tint)
        icon = QIcon(tinted)
        ICON_CACHE[cache_key] = icon
        return icon

    def create_icon_label(file_name: str, size: int = 48) -> QLabel:
        """Return QLabel with a tinted icon pixmap."""
        icon = get_icon(file_name, size)
        label = QLabel()
        label.setPixmap(icon.pixmap(size, size))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("message_emoji")
        label.setProperty("icon_name", file_name)
        return label

    def refresh_icons(root_widget=None):
        """Re-tint all buttons/labels that carry 'icon_name' property."""
        if root_widget is None:
            root_widget = main_window
        for btn in root_widget.findChildren(QAbstractButton):
            name = btn.property("icon_name")
            if not name:
                continue
            force_dark = bool(btn.property("icon_force_dark"))
            force_white = bool(btn.property("icon_force_white"))
            btn.setIcon(get_icon(name, btn.iconSize().width(), force_dark=force_dark, force_white=force_white))
        for lbl in root_widget.findChildren(QLabel):
            name = lbl.property("icon_name")
            if not name:
                continue
            size = lbl.pixmap().width() if lbl.pixmap() else 32
            force_dark = bool(lbl.property("icon_force_dark"))
            force_white = bool(lbl.property("icon_force_white"))
            lbl.setPixmap(get_icon(name, size, force_dark=force_dark, force_white=force_white).pixmap(size, size))

    # --------- Load application version from app_info.json ---------
    try:
        with open(resource_path("app_info.json"), "r", encoding="utf-8") as _vf:
            APP_VERSION = json.load(_vf).get("version", APP_VERSION)
    except Exception:
        pass

    # Try to load icon
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    main_window = CustomWindow()
    main_window.stacked_widget = QStackedWidget()
    main_window.setWindowTitle("Goida AI Unlocker (macOS)")
    main_window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    main_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    main_window.dark_theme = is_macos_dark_theme()
    main_window.styles = get_stylesheet(main_window.dark_theme)
    main_window.setStyleSheet(main_window.styles["main"])
    if os.path.exists(icon_path):
        main_window.setWindowIcon(QIcon(icon_path))

    # Main container
    main_container = QWidget()
    main_layout = QVBoxLayout(main_container)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Title bar
    title_bar = QWidget()
    title_bar.setObjectName("titleBar")
    title_bar.setFixedHeight(32)
    main_window.title_bar = title_bar
    title_bar_layout = QHBoxLayout(title_bar)
    title_bar_layout.setContentsMargins(12, 0, 8, 0)
    title_bar_layout.setSpacing(0)
    title_label = QLabel("Goida AI Unlocker (macOS)")
    title_label.setStyleSheet("""
        QLabel {
            color: #666666;
            font-size: 13px;
            font-weight: bold;
            background: transparent;
        }
    """)
    title_bar_layout.addWidget(title_label)
    title_bar_layout.addStretch()
    minimize_button = QPushButton("─")
    minimize_button.setFixedSize(26, 26)
    minimize_button.clicked.connect(main_window.showMinimized)
    minimize_button.setStyleSheet("""
        QPushButton { background: transparent; color: #666666; border: none; font-size: 14px; font-weight: bold; }
        QPushButton:hover { color: #2d7dff; }
    """)
    close_button = QPushButton("×")
    close_button.setFixedSize(26, 26)
    close_button.clicked.connect(app.quit)
    close_button.setStyleSheet("""
        QPushButton { background: transparent; color: #666666; border: none; font-size: 18px; font-weight: bold; }
        QPushButton:hover { color: #e06c75; }
    """)
    title_bar_layout.addWidget(minimize_button)
    title_bar_layout.addWidget(close_button)
    main_layout.addWidget(title_bar)

    # Central widget
    central_widget = QWidget()
    outer_layout = QVBoxLayout(central_widget)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)
    outer_layout.addStretch()
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(24)
    layout.setContentsMargins(20, 20, 20, 20)
    outer_layout.addLayout(layout)
    outer_layout.addStretch()

    def fix_widget_size(w):
        w.setMinimumSize(main_window.width(), main_window.height() - title_bar.height())
        w.setMaximumSize(main_window.width(), main_window.height() - title_bar.height())

    main_window.resize(640, 640)

    def on_main_window_resize(event=None):
        fix_widget_size(central_widget)
        if main_window.stacked_widget:
            current = main_window.stacked_widget.currentWidget()
            if current:
                fix_widget_size(current)

    old_resize_event = main_window.resizeEvent
    def new_resize_event(self, event):
        old_resize_event(event)
        on_main_window_resize(event)
    main_window.resizeEvent = new_resize_event.__get__(main_window, CustomWindow)

    # App title
    app_title_label = QLabel()
    app_title_label.setObjectName("main_title")
    app_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    app_title_label.setTextFormat(Qt.TextFormat.RichText)
    app_title_label.setText(main_window.styles["about_title_html"])
    app_title_label.setStyleSheet(main_window.styles["about_title_style"])
    layout.addWidget(app_title_label)

    status = "Установлен" if check_installation() else "Не установлен"
    color = "#43b581" if status == "Установлен" else "#e06c75"
    textinformer = QLabel(f"ㅤОбход блокировок - <span style='color:{color}; font-weight:bold;'>{status}</span>ㅤ")
    textinformer.setTextFormat(Qt.TextFormat.RichText)
    textinformer.setAlignment(Qt.AlignmentFlag.AlignCenter)
    textinformer.setStyleSheet(main_window.styles["label"])

    # Version label
    version_label = QLabel("Проверка версии…")
    version_label.setTextFormat(Qt.TextFormat.RichText)
    version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    version_label.setStyleSheet(main_window.styles["label"])

    # Status container
    status_container = QWidget()
    status_container.setObjectName("status_block")
    status_vbox = QVBoxLayout(status_container)
    status_vbox.setContentsMargins(16, 12, 16, 12)
    status_vbox.setSpacing(4)
    status_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status_vbox.addWidget(textinformer)
    status_vbox.addWidget(version_label)

    _light_block = "background:#f3f4f7; border:1.5px solid #cfd4db; border-radius:12px;"
    _dark_block = "background:#2d333b; border:1.5px solid #3c434d; border-radius:12px;"
    status_container.setStyleSheet(_dark_block if main_window.dark_theme else _light_block)

    layout.addWidget(status_container)

    button = QPushButton(" Установить обход блокировок")
    button.setIcon(get_icon("settings.svg", 18, force_white=True))
    button.setIconSize(QSize(18, 18))
    button.setProperty("icon_name", "settings.svg")
    button.setProperty("icon_force_white", True)
    button.setStyleSheet(main_window.styles["button1"])
    
    button2 = QPushButton(" Удалить обход блокировок")
    button2.setIcon(get_icon("trash.svg", 18, force_white=True))
    button2.setIconSize(QSize(18, 18))
    button2.setProperty("icon_name", "trash.svg")
    button2.setProperty("icon_force_white", True)
    button2.setStyleSheet(main_window.styles["button2"])
    
    theme_button = QPushButton(" Сменить тему")
    theme_button.setIcon(get_icon("sun.svg", 18, force_dark=True))
    theme_button.setIconSize(QSize(18, 18))
    theme_button.setProperty("icon_name", "sun.svg")
    theme_button.setProperty("icon_force_dark", True)
    theme_button.setStyleSheet(main_window.styles["theme"])
    
    donate_button = QPushButton(" Донат")
    donate_button.setIcon(get_icon("heart.svg", 18, force_dark=True))
    donate_button.setIconSize(QSize(18, 18))
    donate_button.setProperty("icon_name", "heart.svg")
    donate_button.setProperty("icon_force_dark", True)
    donate_button.setStyleSheet(main_window.styles["theme"])
    
    about_button = QPushButton(" О программе")
    about_button.setIcon(get_icon("info.svg", 18, force_dark=True))
    about_button.setIconSize(QSize(18, 18))
    about_button.setProperty("icon_name", "info.svg")
    about_button.setProperty("icon_force_dark", True)
    about_button.setStyleSheet(main_window.styles["theme"])

    # Кнопка обновлений отключена до публикации на GitHub
    update_button = None
    # update_button = QPushButton(" Проверить обновления")
    # update_button.setIcon(get_icon("refresh.svg", 18, force_dark=True))
    # update_button.setIconSize(QSize(18, 18))
    # update_button.setProperty("icon_name", "refresh.svg")
    # update_button.setProperty("icon_force_dark", True)
    # update_button.setStyleSheet(main_window.styles["theme"])

    def restore_original_hosts():
        """Restore default hosts file."""
        if sys.platform != 'darwin':
            print("Эта функция предназначена только для macOS.")
            return False

        script_path: str | None = None
        try:
            default_hosts = (
                '##\n'
                '# Host Database\n'
                '#\n'
                '# localhost is used to configure the loopback interface\n'
                '# when the system is booting.  Do not change this entry.\n'
                '##\n'
                '127.0.0.1       localhost\n'
                '255.255.255.255 broadcasthost\n'
                '::1             localhost\n'
            )

            script_fd, script_path = tempfile.mkstemp(suffix='.sh')
            os.close(script_fd)
            
            shell_script = f'''#!/bin/bash
cat > /etc/hosts << 'EOF'
{default_hosts}
EOF
chmod 644 /etc/hosts
dscacheutil -flushcache
killall -HUP mDNSResponder
'''
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(shell_script)
            
            os.chmod(script_path, 0o755)

            applescript = f'''
            do shell script "'{script_path}'" with administrator privileges
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                _time.sleep(1)
                return True
            else:
                print(f"Ошибка: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
        finally:
            if script_path:
                _safe_remove(script_path)

    if main_window.stacked_widget:
        main_window.stacked_widget.addWidget(central_widget)
    main_layout.addWidget(main_window.stacked_widget)
    main_window.setCentralWidget(main_container)

    def animate_widget_switch(new_widget, on_finish=None):
        if not main_window.stacked_widget: return
        current_widget = main_window.stacked_widget.currentWidget()
        if not current_widget or current_widget == new_widget:
            main_window.stacked_widget.setCurrentWidget(new_widget)
            if on_finish: on_finish()
            return

        fix_widget_size(new_widget)
        effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(effect)
        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(180)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        def after_fade_out():
            if main_window.stacked_widget is not None:
                main_window.stacked_widget.setCurrentWidget(new_widget)
                effect2 = QGraphicsOpacityEffect(new_widget)
                new_widget.setGraphicsEffect(effect2)
                fade_in = QPropertyAnimation(effect2, b"opacity")
                fade_in.setDuration(180)
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                def clear_anim():
                    new_widget.setGraphicsEffect(None)
                    main_window._current_animation = None
                fade_in.finished.connect(clear_anim)
                if on_finish: fade_in.finished.connect(on_finish)
                main_window._current_animation = fade_in
                fade_in.start()

        fade_out.finished.connect(after_fade_out)
        main_window._current_animation = fade_out
        fade_out.start()

    def update_subwindow_styles():
        if not main_window.stacked_widget: return
        for i in range(main_window.stacked_widget.count()):
            w = main_window.stacked_widget.widget(i)
            if w is central_widget: continue
            w.setStyleSheet(main_window.styles["main"])
            for child in w.findChildren(QPushButton):
                text = child.text().lower()
                if any(keyword in text for keyword in ["донат", "о программе", "github", "вернуться", "меню", "telegram", "youtube", "rutube", "дзен", "dzen", "vk"]):
                    child.setStyleSheet(main_window.styles["theme"])
                elif "копировать" in text or "окей" in text:
                    child.setStyleSheet(main_window.styles["button1"])
                elif "удалить" in text:
                    child.setStyleSheet(main_window.styles["button2"])
                else: child.setStyleSheet(main_window.styles["button1"])

            for child in w.findChildren(QLabel):
                obj_name = child.objectName()
                if obj_name == "about_title":
                    child.setText(main_window.styles["about_title_html"])
                    child.setStyleSheet(main_window.styles["about_title_style"])
                elif obj_name == "about_info":
                    child.setText(main_window.styles["about_info_html"])
                elif obj_name == "about_link":
                    child.setText(main_window.styles["about_link_html"])
                elif obj_name == "message_emoji": continue
                else: child.setStyleSheet(main_window.styles["label"])

            refresh_icons(w)

    def show_message_and_return(msg, success=True, animate=True):
        message_widget = QWidget()
        vbox = QVBoxLayout(message_widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.setSpacing(24)
        vbox.setContentsMargins(20, 20, 20, 20)
        fix_widget_size(message_widget)

        card_container = QWidget()
        card_container.setObjectName("msg_card")
        card_container.setMinimumWidth(220)
        card_container.setMaximumWidth(600)
        card_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        card_layout = QVBoxLayout(card_container)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 24, 32, 24)

        light_style = "background:#f3f4f7; border:2.5px solid #cfd4db; border-radius:12px;"
        dark_style = "background:#2d333b; border:2.5px solid #3c434d; border-radius:12px;"
        card_container.setStyleSheet(dark_style if main_window.dark_theme else light_style)

        icon_file = "check-circle.svg" if success else "x-circle.svg"
        emoji_label = create_icon_label(icon_file, size=48)
        card_layout.addWidget(emoji_label)

        for line in msg.split("\n"):
            if not line.strip():
                continue
            lbl = QLabel(line)
            lbl.setWordWrap(False)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(lbl)

        ok_btn = QPushButton("Окей")
        card_layout.addWidget(ok_btn)

        vbox.addWidget(card_container)

        if main_window.stacked_widget:
            main_window.stacked_widget.addWidget(message_widget)
        update_subwindow_styles()

        if animate and main_window.stacked_widget:
            animate_widget_switch(message_widget)
        elif main_window.stacked_widget:
            main_window.stacked_widget.setCurrentWidget(message_widget)

        def return_to_main():
            def do_remove_message_widget():
                if main_window.stacked_widget: main_window.stacked_widget.removeWidget(message_widget)
                message_widget.deleteLater()
            animate_widget_switch(central_widget, on_finish=do_remove_message_widget)
        ok_btn.clicked.connect(return_to_main)

    def show_update_available(local_version: str, latest_version: str, dl_url: str):
        update_widget = QWidget()
        vbox = QVBoxLayout(update_widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.setSpacing(24)
        vbox.setContentsMargins(20, 20, 20, 20)
        fix_widget_size(update_widget)

        card_container = QWidget()
        card_container.setObjectName("update_card")
        card_container.setMinimumWidth(240)
        card_container.setMaximumWidth(600)
        card_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        card_layout = QVBoxLayout(card_container)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 24, 32, 24)

        light_style = "background:#f3f4f7; border:2.5px solid #cfd4db; border-radius:12px;"
        dark_style = "background:#2d333b; border:2.5px solid #3c434d; border-radius:12px;"
        card_container.setStyleSheet(dark_style if main_window.dark_theme else light_style)

        emoji_label = create_icon_label("alert.svg", size=48)
        emoji_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        emoji_label.setFixedHeight(48)
        card_layout.addWidget(emoji_label)

        installed_lbl = QLabel(f"ㅤУстановленная версия: <b>v{local_version}</b>ㅤ")
        installed_lbl.setTextFormat(Qt.TextFormat.RichText)
        installed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(installed_lbl)

        latest_lbl = QLabel(f"Последняя версия: <b>v{latest_version}</b>")
        latest_lbl.setTextFormat(Qt.TextFormat.RichText)
        latest_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(latest_lbl)

        label = QLabel("Доступна новая версия!")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(label)

        download_btn = QPushButton("Скачать")
        card_layout.addWidget(download_btn)

        ok_btn2 = QPushButton("Окей")
        card_layout.addWidget(ok_btn2)

        vbox.addWidget(card_container)

        if main_window.stacked_widget:
            main_window.stacked_widget.addWidget(update_widget)
        update_subwindow_styles()
        animate_widget_switch(update_widget)

        download_btn.clicked.connect(lambda: subprocess.call(['open', dl_url]))

        def return_to_main2():
            def do_remove_update_widget():
                if main_window.stacked_widget:
                    main_window.stacked_widget.removeWidget(update_widget)
                update_widget.deleteLater()
            animate_widget_switch(central_widget, on_finish=do_remove_update_widget)
        ok_btn2.clicked.connect(return_to_main2)

    def show_no_update_needed(local_version: str, latest_version: str):
        done_widget = QWidget()
        vbox = QVBoxLayout(done_widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.setSpacing(24)
        vbox.setContentsMargins(20, 20, 20, 20)
        fix_widget_size(done_widget)

        card_container = QWidget()
        card_container.setObjectName("update_card")
        card_container.setMinimumWidth(240)
        card_container.setMaximumWidth(600)
        card_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        card_layout = QVBoxLayout(card_container)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 24, 32, 24)

        light_style = "background:#f3f4f7; border:2.5px solid #cfd4db; border-radius:12px;"
        dark_style = "background:#2d333b; border:2.5px solid #3c434d; border-radius:12px;"
        card_container.setStyleSheet(dark_style if main_window.dark_theme else light_style)

        emoji_label = create_icon_label("check-circle.svg", size=40)
        emoji_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        emoji_label.setFixedHeight(48)
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setObjectName("message_emoji")
        emoji_label.setStyleSheet("font-size: 48px;")
        card_layout.addWidget(emoji_label)

        installed_lbl = QLabel(f"ㅤУстановленная версия: <b>v{local_version}</b>ㅤ")
        installed_lbl.setTextFormat(Qt.TextFormat.RichText)
        installed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(installed_lbl)

        latest_lbl = QLabel(f"ㅤПоследняя версия: <b>v{latest_version}</b>ㅤ")
        latest_lbl.setTextFormat(Qt.TextFormat.RichText)
        latest_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(latest_lbl)

        info_label = QLabel("ㅤУ вас установлена последняя версия.ㅤ")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(False)
        card_layout.addWidget(info_label)

        ok_btn = QPushButton("Окей")
        card_layout.addWidget(ok_btn)

        vbox.addWidget(card_container)

        if main_window.stacked_widget:
            main_window.stacked_widget.addWidget(done_widget)
        update_subwindow_styles()
        animate_widget_switch(done_widget)

        def return_to_main():
            def do_remove():
                if main_window.stacked_widget:
                    main_window.stacked_widget.removeWidget(done_widget)
                done_widget.deleteLater()
            animate_widget_switch(central_widget, on_finish=do_remove)
        ok_btn.clicked.connect(return_to_main)

    def check_for_updates():
        import json as _json
        if getattr(check_for_updates, "_running", False):
            return
        setattr(check_for_updates, "_running", True)

        def worker():
            try:
                with open(resource_path("app_info.json"), "r", encoding="utf-8") as _f:
                    _local = _json.load(_f)
                local_ver = _local.get("version", "0.0.0")
                import time as _t
                remote_url = _local.get("update_info_url")
                if not remote_url:
                    raise RuntimeError("URL обновления не найден.")
                remote_data = _json.loads(urllib.request.urlopen(f"{remote_url}?t={int(_t.time())}", timeout=10).read().decode("utf-8"))
                remote_ver = remote_data.get("version", "0.0.0")
                download_url = remote_data.get("download_url", "https://github.com/AvenCores/Goida-AI-Unlocker")

                def _parse(v):
                    return tuple(int(x) for x in v.strip("vV").split(".") if x.isdigit())
                newer = _parse(remote_ver) > _parse(local_ver)
                if newer:
                    QTimer.singleShot(0, main_window, lambda lv=local_ver, rv=remote_ver, u=download_url: show_update_available(lv, rv, u))
                else:
                    QTimer.singleShot(0, main_window, lambda lv=local_ver, rv=remote_ver: show_no_update_needed(lv, rv))
            except Exception as e:
                err = f"Не удалось проверить обновления.\n{e}"
                QTimer.singleShot(0, main_window, lambda m=err: show_message_and_return(m, success=False, animate=True))
            finally:
                setattr(check_for_updates, "_running", False)
        threading.Thread(target=worker, daemon=True).start()

    # update_button.clicked.connect(lambda: check_for_updates())  # Отключено

    def start_installation(action: str = "install"):
        """Show waiting window and perform installation/update/uninstall in background."""
        processing_widget = QWidget()
        vbox = QVBoxLayout(processing_widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.setSpacing(24)
        vbox.setContentsMargins(20, 20, 20, 20)
        fix_widget_size(processing_widget)

        card_container = QWidget()
        card_container.setObjectName("wait_card")
        card_container.setMinimumWidth(220)
        card_container.setMaximumWidth(600)
        card_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        card_layout = QVBoxLayout(card_container)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 24, 32, 24)

        light_style = "background:#f3f4f7; border:2.5px solid #cfd4db; border-radius:12px;"
        dark_style = "background:#2d333b; border:2.5px solid #3c434d; border-radius:12px;"
        card_container.setStyleSheet(dark_style if main_window.dark_theme else light_style)

        emoji_label = create_icon_label("clock.svg", size=48)
        card_layout.addWidget(emoji_label)

        if action == "install":
            msg_text = "Установка обхода...\nㅤПожалуйста, подождите.ㅤ"
        elif action == "update":
            msg_text = "Обновление обхода...\nㅤПожалуйста, подождите.ㅤ"
        else:
            msg_text = "Удаление обхода...\nㅤПожалуйста, подождите.ㅤ"

        for line in msg_text.split("\n"):
            if not line.strip():
                continue
            lbl = QLabel(line)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(False)
            card_layout.addWidget(lbl)

        vbox.addWidget(card_container)

        if main_window.stacked_widget:
            main_window.stacked_widget.addWidget(processing_widget)
        update_subwindow_styles()
        animate_widget_switch(processing_widget)

        def update_status_label():
            current_status = "Установлен" if check_installation() else "Не установлен"
            current_color = "#43b581" if current_status == "Установлен" else "#e06c75"
            textinformer.setText(f"ㅤОбход блокировок - <span style='color:{current_color}; font-weight:bold;'>{current_status}</span>ㅤ")
            update_version_label()

        def finish(ok_result):
            if ok_result:
                if action == "install":
                    success_msg = "Файл hosts успешно установлен!\nㅤВозможно потребуется перезапустить браузер.ㅤ"
                elif action == "update":
                    success_msg = "Файл hosts успешно обновлён!\nㅤВозможно потребуется перезапустить браузер.ㅤ"
                else:
                    success_msg = "Файл hosts успешно восстановлен!\nㅤВозможно потребуется перезапустить браузер.ㅤ"
                show_message_and_return(success_msg, success=True, animate=True)
            else:
                if action == "install":
                    error_msg = "Не удалось установить файл hosts.\nㅤПроверьте права доступа.ㅤ"
                elif action == "update":
                    error_msg = "Не удалось обновить файл hosts.\nㅤПроверьте права доступа.ㅤ"
                else:
                    error_msg = "Не удалось восстановить файл hosts.\nㅤПроверьте права доступа.ㅤ"
                show_message_and_return(error_msg, success=False, animate=True)

            def remove_processing():
                if main_window.stacked_widget and processing_widget in [main_window.stacked_widget.widget(i) for i in range(main_window.stacked_widget.count())]:
                    main_window.stacked_widget.removeWidget(processing_widget)
                processing_widget.deleteLater()
            QTimer.singleShot(400, remove_processing)

            QTimer.singleShot(500, update_status_label)

        def worker():
            if action in ("install", "update"):
                result = update_hosts_as_admin()
            else:
                result = restore_original_hosts()
            QTimer.singleShot(0, main_window, lambda res=result: finish(res))

        threading.Thread(target=worker, daemon=True).start()

    def on_install_click():
        if "Обновить" in button.text():
            start_installation("update")
        else:
            start_installation("install")

    def on_uninstall_click():
        start_installation("uninstall")

    button.clicked.connect(on_install_click)
    button2.clicked.connect(on_uninstall_click)

    def switch_theme():
        if main_window.is_animating: return
        main_window.is_animating = True
        animation_steps, time_interval = 15, 20

        def fade_out(step=1.0):
            if step >= 0:
                main_window.setWindowOpacity(step)
                QTimer.singleShot(time_interval, lambda: fade_out(step - 1.0 / animation_steps))
            else:
                main_window.setWindowOpacity(0)
                main_window.setUpdatesEnabled(False)
                main_window.dark_theme = not main_window.dark_theme
                main_window.styles = get_stylesheet(main_window.dark_theme)
                main_window.setStyleSheet(main_window.styles["main"])
                textinformer.setStyleSheet(main_window.styles["label"])
                app_title_label.setText(main_window.styles["about_title_html"])
                app_title_label.setStyleSheet(main_window.styles["about_title_style"])
                version_label.setStyleSheet(main_window.styles["label"])
                button.setStyleSheet(main_window.styles["button1"])
                button2.setStyleSheet(main_window.styles["button2"])
                theme_button.setStyleSheet(main_window.styles["theme"])
                donate_button.setStyleSheet(main_window.styles["theme"])
                about_button.setStyleSheet(main_window.styles["theme"])
                _light_block = "background:#f3f4f7; border:1.5px solid #cfd4db; border-radius:12px;"
                _dark_block = "background:#2d333b; border:1.5px solid #3c434d; border-radius:12px;"
                status_container.setStyleSheet(_dark_block if main_window.dark_theme else _light_block)
                update_subwindow_styles()
                refresh_icons()
                main_window.setUpdatesEnabled(True)
                fade_in()

        def fade_in(step=0.0):
            if step <= 1.0:
                main_window.setWindowOpacity(step)
                QTimer.singleShot(time_interval, lambda: fade_in(step + 1.0 / animation_steps))
            else:
                main_window.setWindowOpacity(1.0)
                main_window.is_animating = False

        fade_out()
    theme_button.clicked.connect(switch_theme)

    def show_donate_window():
        donate_widget = QWidget()
        donate_layout = QVBoxLayout(donate_widget)
        donate_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donate_layout.setSpacing(24)
        donate_layout.setContentsMargins(20, 20, 20, 20)

        fix_widget_size(donate_widget)

        card_container = QWidget()
        card_container.setObjectName("donate_card")
        card_container.setMaximumWidth(380)
        card_container.setMinimumWidth(240)

        card_layout = QVBoxLayout(card_container)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 24, 32, 24)

        title_lbl = QLabel("Поддержать автора")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size:22px; font-weight:600;")
        card_layout.addWidget(title_lbl)

        card = "2202 2050 7215 4401"
        card_lbl = QLabel(f"ㅤSBER: <b>{card}</b>ㅤ")
        card_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lbl.setStyleSheet("font-size:16px;")
        card_layout.addWidget(card_lbl)

        copy_btn = QPushButton("Скопировать номер карты")
        card_layout.addWidget(copy_btn)

        light_style = "background:#f3f4f7; border:2.5px solid #cfd4db; border-radius:12px;"
        dark_style = "background:#2d333b; border:2.5px solid #3c434d; border-radius:12px;"
        card_container.setStyleSheet(dark_style if main_window.dark_theme else light_style)

        donate_layout.addWidget(card_container)

        back_button = QPushButton("  В меню  ")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet(main_window.styles["theme"])
        donate_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        copy_btn.setStyleSheet(main_window.styles["button1"])

        def copy_card():
            QApplication.clipboard().setText(card)

            if getattr(copy_btn, "_animating", False):
                return
            setattr(copy_btn, "_animating", True)

            original_text = "Скопировать номер карты"
            success_text = "Скопировано"

            def fade_out_then_change():
                effect = QGraphicsOpacityEffect(copy_btn)
                copy_btn.setGraphicsEffect(effect)

                fade_out = QPropertyAnimation(effect, b"opacity", copy_btn)
                fade_out.setDuration(150)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)

                def change_text_and_fade_in():
                    copy_btn.setText(success_text)
                    fade_in = QPropertyAnimation(effect, b"opacity", copy_btn)
                    fade_in.setDuration(150)
                    fade_in.setStartValue(0.0)
                    fade_in.setEndValue(1.0)

                    def hold_then_revert():
                        def fade_out2():
                            fade_out_back = QPropertyAnimation(effect, b"opacity", copy_btn)
                            fade_out_back.setDuration(150)
                            fade_out_back.setStartValue(1.0)
                            fade_out_back.setEndValue(0.0)

                            def reset_text():
                                copy_btn.setText(original_text)
                                fade_in_back = QPropertyAnimation(effect, b"opacity", copy_btn)
                                fade_in_back.setDuration(150)
                                fade_in_back.setStartValue(0.0)
                                fade_in_back.setEndValue(1.0)

                                def clear():
                                    copy_btn.setGraphicsEffect(None)
                                    setattr(copy_btn, "_animating", False)
                                fade_in_back.finished.connect(clear)
                                fade_in_back.start()
                            fade_out_back.finished.connect(reset_text)
                            fade_out_back.start()

                        QTimer.singleShot(1200, fade_out2)

                    fade_in.finished.connect(hold_then_revert)
                    fade_in.start()

                fade_out.finished.connect(change_text_and_fade_in)
                fade_out.start()

            fade_out_then_change()

        def return_to_main():
            def do_remove_donate_widget():
                if main_window.stacked_widget: main_window.stacked_widget.removeWidget(donate_widget)
                donate_widget.deleteLater()
            animate_widget_switch(central_widget, on_finish=do_remove_donate_widget)

        copy_btn.clicked.connect(copy_card)
        back_button.clicked.connect(return_to_main)

        if main_window.stacked_widget:
            main_window.stacked_widget.addWidget(donate_widget)
        update_subwindow_styles()
        animate_widget_switch(donate_widget)
    donate_button.clicked.connect(show_donate_window)

    layout.addWidget(button)
    layout.addWidget(button2)
    theme_donate_hbox = QHBoxLayout()
    theme_donate_hbox.setSpacing(12)
    theme_donate_hbox.addWidget(theme_button)
    theme_donate_hbox.addWidget(donate_button)
    layout.addLayout(theme_donate_hbox)
    layout.addStretch()
    # Кнопка обновлений добавляется только если она создана
    if update_button is not None:
        layout.addWidget(update_button)
    layout.addWidget(about_button)

    def show_about_window():
        about_widget = QWidget()
        vbox = QVBoxLayout(about_widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.setSpacing(8)
        vbox.setContentsMargins(12, 12, 12, 12)

        icon_label = create_icon_label("bulb.svg", size=32)
        vbox.addWidget(icon_label)

        label_ver = QLabel()
        label_ver.setObjectName("about_title")
        label_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(label_ver)

        info = QLabel()
        info.setObjectName("about_info")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(info)

        github_btn = QToolButton()
        github_btn.setText("GitHub")
        github_btn.setIcon(get_icon("github.svg", 24, force_dark=True))
        github_btn.setIconSize(QSize(24, 24))
        github_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setStyleSheet(main_window.styles["theme"] + "\nQToolButton { font-size:13px; padding:6px 12px; }")
        github_btn.setProperty("icon_name", "github.svg")
        github_btn.setProperty("icon_force_dark", True)
        github_btn.clicked.connect(lambda: subprocess.call(['open', "https://github.com/AvenCores"]))

        # Кнопка GitHub macOS версии
        github_macos_btn = QToolButton()
        github_macos_btn.setText("GitHub (macOS)")
        github_macos_btn.setIcon(get_icon("github.svg", 24, force_dark=True))
        github_macos_btn.setIconSize(QSize(24, 24))
        github_macos_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        github_macos_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_macos_btn.setStyleSheet(main_window.styles["theme"] + "\nQToolButton { font-size:13px; padding:6px 12px; }")
        github_macos_btn.setProperty("icon_name", "github.svg")
        github_macos_btn.setProperty("icon_force_dark", True)
        github_macos_btn.clicked.connect(lambda: subprocess.call(['open', "https://github.com/seidenov"]))

        repo_btn = QToolButton()
        repo_btn.setText("Репозиторий")
        repo_btn.setIcon(get_icon("github.svg", 24, force_dark=True))
        repo_btn.setIconSize(QSize(24, 24))
        repo_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        repo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        repo_btn.setProperty("icon_name", "github.svg")
        repo_btn.setProperty("icon_force_dark", True)
        repo_btn.setStyleSheet(
            main_window.styles["theme"] +
            "\nQToolButton { font-size:13px; padding:6px 12px; background:qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e06c75, stop:1 #d64c58); color:white; border:1px solid #b94852; border-radius:8px; }\nQToolButton:pressed { background:#c94c57; }"
        )
        repo_btn.clicked.connect(lambda: subprocess.call(['open', "https://github.com/AvenCores/Goida-AI-Unlocker"]))
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        grid.addWidget(github_btn, 0, 0, alignment=Qt.AlignmentFlag.AlignHCenter)
        grid.addWidget(github_macos_btn, 0, 1, alignment=Qt.AlignmentFlag.AlignHCenter)

        social_buttons = [
            ("Telegram", "https://t.me/avencoresyt", "send.svg"),
            ("YouTube", "https://youtube.com/@avencores", "play.svg"),
            ("RuTube", "https://rutube.ru/channel/34072414", "video.svg"),
            ("Dzen", "https://dzen.ru/avencores", "book-open.svg"),
            ("VK", "https://vk.com/avencoresvk", "users.svg"),
        ]
        about_buttons = [github_btn, github_macos_btn, repo_btn]
        col_count = 3
        row = 0
        col = 2
        for label, url, icon_file in social_buttons:
            btn = QToolButton()
            btn.setText(label)
            btn.setIcon(get_icon(icon_file, 24, force_dark=True))
            btn.setIconSize(QSize(24, 24))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setProperty("icon_name", icon_file)
            btn.setProperty("icon_force_dark", True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(main_window.styles["theme"] + "\nQToolButton { font-size:13px; padding:6px 12px; }")
            btn.clicked.connect(lambda checked=False, u=url: subprocess.call(['open', u]))
            grid.addWidget(btn, row, col, alignment=Qt.AlignmentFlag.AlignHCenter)
            about_buttons.append(btn)
            col += 1
            if col >= col_count:
                row += 1
                col = 0

        vbox.addLayout(grid)
        repo_btn.setStyleSheet(main_window.styles["theme"] + "\nQToolButton { font-size:13px; padding:6px 12px; }")
        vbox.addSpacing(8)
        vbox.addWidget(repo_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addSpacing(8)

        def _equalize_about_button_widths():
            if not about_buttons:
                return
            def _req_w(b):
                fm = b.fontMetrics() if hasattr(b, "fontMetrics") else QFontMetrics(b.font())
                text_w = fm.horizontalAdvance(b.text())
                icon_w = b.iconSize().width() if hasattr(b, "iconSize") else 24
                base = max(text_w, icon_w)
                return base + 24
            ref_w = max(max(b.sizeHint().width(), _req_w(b)) for b in about_buttons)
            for b in about_buttons:
                b.setFixedWidth(ref_w)

        back_button = QPushButton("  В меню  ")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet(main_window.styles["theme"])

        def return_to_main():
            def do_remove_about_widget():
                if main_window.stacked_widget: main_window.stacked_widget.removeWidget(about_widget)
                about_widget.deleteLater()
            animate_widget_switch(central_widget, on_finish=do_remove_about_widget)
        back_button.clicked.connect(return_to_main)
        vbox.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        if main_window.stacked_widget: main_window.stacked_widget.addWidget(about_widget)
        update_subwindow_styles()
        QTimer.singleShot(0, lambda: _equalize_about_button_widths())
        animate_widget_switch(about_widget)
    about_button.clicked.connect(show_about_window)

    def update_version_label():
        """Refresh version_label text and adapt the install button caption."""
        now_ts = _time.time()
        last_run = getattr(update_version_label, "_last_run", 0.0)
        if getattr(update_version_label, "_running", False) or (now_ts - last_run) < 1.0:
            return
        setattr(update_version_label, "_running", True)
        setattr(update_version_label, "_last_run", now_ts)

        def worker():
            word, clr = get_hosts_version_status()
            def apply():
                version_label.setText(
                    f"Версия hosts - <span style='color:{clr}; font-weight:bold;'>{word}</span>")
                if word == "Устарело":
                    button.setText(" Обновить обход блокировок")
                else:
                    button.setText(" Установить обход блокировок")
            QTimer.singleShot(0, main_window, apply)
            setattr(update_version_label, "_running", False)
        threading.Thread(target=worker, daemon=True).start()

    # Initial version check
    update_version_label()

    main_window.show()
    on_main_window_resize()

    sys.exit(app.exec())

