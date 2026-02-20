import sys
import os
import json
import threading
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar,
    QStackedWidget, QMenu, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize, QPoint, QRectF
from PyQt5.QtGui import QFont, QMouseEvent, QFontDatabase, QPainter, QPainterPath, QColor, QLinearGradient, QBrush, QPen
from config import Language, Theme, get_text, get_colors
from utils import is_admin, is_system_folder, replace_exe_file
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
class RoundedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.current_bg_color = "#2D2D2D"
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, 25, 25)
        painter.fillPath(path, QColor(self.current_bg_color))
class InterLabel(QLabel):
    def __init__(self, text="", parent=None, size=14, weight=QFont.Normal):
        super().__init__(text, parent)
        self.setFont(self.get_inter_font(size, weight))
    
    def get_inter_font(self, size, weight):
        font = QFont("Inter", size)
        font.setWeight(weight)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setKerning(True)
        return font
class InterButton(QPushButton):
    def __init__(self, text="", parent=None, size=14, weight=QFont.Medium):
        super().__init__(text, parent)
        self.setFont(self.get_inter_font(size, weight))
        self.setCursor(Qt.PointingHandCursor)
    def get_inter_font(self, size, weight):
        font = QFont("Inter", size)
        font.setWeight(weight)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setKerning(True)
        return font
class CustomTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_pos = None
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        self.menu_button = QPushButton()
        self.menu_button.setText("☰")
        self.menu_button.setFixedSize(36, 36)
        self.menu_button.setCursor(Qt.PointingHandCursor)
        self.menu_button.setObjectName("menuButton")
        layout.addWidget(self.menu_button)
        layout.addStretch()
        self.app_title = InterLabel("backtrack", self, 18, QFont.Bold)
        self.app_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.app_title)
        layout.addStretch()
        self.close_button = QPushButton()
        self.close_button.setText("✕")
        self.close_button.setFixedSize(36, 36)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setObjectName("closeButton")
        layout.addWidget(self.close_button)
        self.setLayout(layout)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not (self.menu_button.geometry().contains(event.pos()) or 
                    self.close_button.geometry().contains(event.pos())):
                self.drag_pos = event.globalPos() - self.parent_window.frameGeometry().topLeft()
                event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.parent_window.move(event.globalPos() - self.drag_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        self.drag_pos = None
class ContentContainer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentContainer")
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 25)
        self.setLayout(layout)
class ProgressWorker(QObject):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    def __init__(self, original_exe: str, target_exe: str):
        super().__init__()
        self.original_exe = original_exe
        self.target_exe = target_exe
        self.is_cancelled = False
    def run(self):
        try:
            if is_system_folder(self.original_exe):
                if not is_admin():
                    self.finished.emit(False, "admin_required")
                    return
            for i in range(0, 85, 15):
                if self.is_cancelled:
                    self.finished.emit(False, "cancelled")
                    return
                self.progress_updated.emit(i)
                time.sleep(0.3)
            if self.is_cancelled:
                self.finished.emit(False, "cancelled")
                return
            if replace_exe_file(self.original_exe, self.target_exe):
                for i in range(85, 101, 5):
                    if self.is_cancelled:
                        self.finished.emit(False, "cancelled")
                        return
                    self.progress_updated.emit(i)
                    time.sleep(0.2)
                self.finished.emit(True, "file_replaced")
            else:
                self.finished.emit(False, "error_replace")
        except Exception as e:
            self.finished.emit(False, str(e))
    def cancel(self):
        self.is_cancelled = True
class ExeReplacerApp(RoundedWindow):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.current_language = Language.RU
        self.current_theme = Theme.LIGHT
        self.settings_file = os.path.join(get_app_dir(), "settings.json")
        self.progress_worker = None
        self.progress_thread = None
        self.load_settings()
        self.init_ui()
        self.apply_theme()
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_language = Language(settings.get('language', 'ru'))
                    self.current_theme = Theme(settings.get('theme', 'light'))
            except:
                pass
    def save_settings(self):
        settings = {
            'language': self.current_language.value,
            'theme': self.current_theme.value
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)
    def init_ui(self):
        self.setWindowTitle("backtrack")
        self.setGeometry(100, 100, 500, 600)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        titlebar = self.create_titlebar()
        main_layout.addWidget(titlebar)
        self.content_container = ContentContainer()
        self.stacked_widget = QStackedWidget()
        self.content_container.layout().addWidget(self.stacked_widget)
        main_layout.addWidget(self.content_container)
        main_widget.setLayout(main_layout)
        self.screen1 = self.create_screen1()
        self.screen2 = self.create_screen2()
        self.screen3 = self.create_screen3()
        self.stacked_widget.addWidget(self.screen1)
        self.stacked_widget.addWidget(self.screen2)
        self.stacked_widget.addWidget(self.screen3)
        self.show_screen(0)
    def create_screen1(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel("📄")
        icon_label.setFont(QFont("Segoe UI", 64))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addSpacing(10)
        choose_label = InterLabel(get_text("screen1_choose", self.current_language), self, 18, QFont.Medium)
        choose_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(choose_label)
        layout.addSpacing(20)
        self.screen1_button = InterButton(get_text('screen1_open_file', self.current_language), self, 15, QFont.Bold)
        self.screen1_button.setMinimumHeight(50)
        self.screen1_button.setMinimumWidth(280)
        self.screen1_button.setObjectName("primaryButton")
        self.screen1_button.clicked.connect(self.select_file)
        layout.addWidget(self.screen1_button, alignment=Qt.AlignCenter)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    def create_screen2(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel("⚡")
        icon_label.setFont(QFont("Segoe UI", 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addSpacing(5)
        self.wait_label = InterLabel(get_text("screen2_wait", self.current_language), self, 18, QFont.Bold)
        self.wait_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wait_label)
        self.subtitle_label = InterLabel(get_text("screen2_subtitle", self.current_language), self, 12, QFont.Normal)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("opacity: 0.7;")
        layout.addWidget(self.subtitle_label)
        layout.addSpacing(15)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setFormat("")
        self.progress_bar.setObjectName("progressBar")
        layout.addWidget(self.progress_bar)
        self.percent_label = InterLabel("0%", self, 14, QFont.Bold)
        self.percent_label.setAlignment(Qt.AlignCenter)
        self.percent_label.setObjectName("percentLabel")
        layout.addWidget(self.percent_label)
        layout.addSpacing(15)
        self.screen2_button = InterButton(get_text("screen2_cancel", self.current_language), self, 14, QFont.Medium)
        self.screen2_button.setMinimumHeight(45)
        self.screen2_button.setMinimumWidth(280)
        self.screen2_button.setObjectName("secondaryButton")
        self.screen2_button.clicked.connect(self.cancel_process)
        layout.addWidget(self.screen2_button, alignment=Qt.AlignCenter)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    def create_screen3(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel("✅")
        icon_label.setFont(QFont("Segoe UI", 64))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addSpacing(5)
        complete_label = InterLabel(get_text("screen3_complete", self.current_language), self, 20, QFont.Bold)
        complete_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(complete_label)
        line = QFrame()
        line.setFixedWidth(60)
        line.setFixedHeight(2)
        line.setObjectName("successLine")
        layout.addWidget(line, alignment=Qt.AlignCenter)
        layout.addSpacing(15)
        self.screen3_button = InterButton(get_text("screen3_done", self.current_language), self, 15, QFont.Bold)
        self.screen3_button.setMinimumHeight(50)
        self.screen3_button.setMinimumWidth(280)
        self.screen3_button.setObjectName("successButton")
        self.screen3_button.clicked.connect(self.return_to_screen1)
        layout.addWidget(self.screen3_button, alignment=Qt.AlignCenter)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    def create_titlebar(self) -> CustomTitleBar:
        titlebar = CustomTitleBar(self)
        titlebar.menu_button.clicked.connect(self.show_menu)
        titlebar.close_button.clicked.connect(self.close)
        self.titlebar = titlebar
        return titlebar
    def show_menu(self):
        if self.stacked_widget.currentIndex() != 0:
            return
        menu = QMenu(self)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        if self.current_theme == Theme.LIGHT:
            menu_style = """
                QMenu {
                    background-color: #FFFFFF;
                    color: #2B2B2B;
                    border: 1px solid #E0E0E0;
                    border-radius: 12px;
                    padding: 8px 0px;
                }
                QMenu::item {
                    padding: 10px 30px;
                    background-color: transparent;
                    font-size: 13px;
                    margin: 2px 8px;
                    border-radius: 6px;
                    font-family: 'Inter';
                }
                QMenu::item:selected {
                    background-color: #F5F5F5;
                    color: #FF4E00;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #E0E0E0;
                    margin: 8px 15px;
                }
            """
        else:
            menu_style = """
                QMenu {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    border: 1px solid #404040;
                    border-radius: 12px;
                    padding: 8px 0px;
                }
                QMenu::item {
                    padding: 10px 30px;
                    background-color: transparent;
                    font-size: 13px;
                    margin: 2px 8px;
                    border-radius: 6px;
                    font-family: 'Inter';
                }
                QMenu::item:selected {
                    background-color: #404040;
                    color: #A19BFD;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #404040;
                    margin: 8px 15px;
                }
            """
        menu.setStyleSheet(menu_style)
        menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        light_action = menu.addAction(get_text("light_theme", self.current_language))
        light_action.triggered.connect(lambda: self.set_theme(Theme.LIGHT))
        dark_action = menu.addAction(get_text("dark_theme", self.current_language))
        dark_action.triggered.connect(lambda: self.set_theme(Theme.DARK))
        menu.addSeparator()
        ru_action = menu.addAction("Русский")
        ru_action.triggered.connect(lambda: self.set_language(Language.RU))
        en_action = menu.addAction("English")
        en_action.triggered.connect(lambda: self.set_language(Language.EN))
        menu_button = self.titlebar.menu_button
        button_pos = menu_button.mapToGlobal(menu_button.rect().bottomLeft())
        button_pos.setY(button_pos.y() + 5)
        button_pos.setX(button_pos.x() - 5)
        menu.exec_(button_pos)
    def set_theme(self, theme: Theme):
        self.current_theme = theme
        self.save_settings()
        self.apply_theme()
    def set_language(self, language: Language):
        self.current_language = language
        self.save_settings()
        self.stacked_widget.removeWidget(self.screen1)
        self.stacked_widget.removeWidget(self.screen2)
        self.stacked_widget.removeWidget(self.screen3)
        self.screen1 = self.create_screen1()
        self.screen2 = self.create_screen2()
        self.screen3 = self.create_screen3()
        self.stacked_widget.addWidget(self.screen1)
        self.stacked_widget.addWidget(self.screen2)
        self.stacked_widget.addWidget(self.screen3)
        self.apply_theme()
        self.show_screen(0)
    def apply_theme(self):
        colors = get_colors(self.current_theme)
        if self.current_theme == Theme.LIGHT:
            bg_color = "#E5E5E5"
            container_color = "#FFFFFF"
            title_color = "#FF4E00"
            text_color = "#2B2B2B"
            titlebar_style = """
                QPushButton#menuButton, QPushButton#closeButton {
                    background-color: transparent;
                    border: 2px solid #FF4E00;
                    color: #FF4E00;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 18px;
                }
                QPushButton#menuButton:hover, QPushButton#closeButton:hover {
                    background-color: #FF4E00;
                    color: #2D2D2D;
                }
            """
            button_style = """
                QPushButton#primaryButton {
                    background-color: #FF4E00;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 12px 20px;
                }
                QPushButton#primaryButton:hover {
                    background-color: #E63D00;
                }
                QPushButton#secondaryButton {
                    background-color: #E5E5E5;
                    color: #2B2B2B;
                    border: 2px solid #FF4E00;
                    border-radius: 22px;
                    padding: 10px 20px;
                }
                QPushButton#secondaryButton:hover {
                    background-color: #FF4E00;
                    color: #2D2D2D;
                }
                QPushButton#successButton {
                    background-color: #00AA00;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 12px 20px;
                }
                QPushButton#successButton:hover {
                    background-color: #009900;
                }
            """
            progress_style = """
                QProgressBar#progressBar {
                    border: none;
                    border-radius: 4px;
                    background-color: #E5E5E5;
                }
                QProgressBar::chunk {
                    background-color: #FF4E00;
                    border-radius: 4px;
                }
            """
            percent_style = "color: #FF4E00;"
            line_style = "background-color: #00AA00; border-radius: 1px;"
        else:
            bg_color = "#2D2D2D"
            container_color = "#3A3A3A"
            title_color = "#A19BFD"
            text_color = "#FFFFFF"
            titlebar_style = """
                QPushButton#menuButton, QPushButton#closeButton {
                    background-color: transparent;
                    border: 2px solid #A19BFD;
                    color: #A19BFD;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 18px;
                }
                QPushButton#menuButton:hover, QPushButton#closeButton:hover {
                    background-color: #A19BFD;
                    color: #2D2D2D;
                }
            """
            button_style = """
                QPushButton#primaryButton {
                    background-color: #A19BFD;
                    color: #2D2D2D;
                    border: none;
                    border-radius: 25px;
                    padding: 12px 20px;
                }
                QPushButton#primaryButton:hover {
                    background-color: #8F86E8;
                }
                QPushButton#secondaryButton {
                    background-color: #3A3A3A;
                    color: #FFFFFF;
                    border: 2px solid #A19BFD;
                    border-radius: 22px;
                    padding: 10px 20px;
                }
                QPushButton#secondaryButton:hover {
                    background-color: #A19BFD;
                    color: #2D2D2D;
                }
                QPushButton#successButton {
                    background-color: #00AA00;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 12px 20px;
                }
                QPushButton#successButton:hover {
                    background-color: #009900;
                }
            """
            progress_style = """
                QProgressBar#progressBar {
                    border: none;
                    border-radius: 4px;
                    background-color: #2D2D2D;
                }
                QProgressBar::chunk {
                    background-color: #A19BFD;
                    border-radius: 4px;
                }
            """
            percent_style = "color: #A19BFD;"
            line_style = "background-color: #00AA00; border-radius: 1px;"
        self.current_bg_color = bg_color
        self.content_container.setStyleSheet(f"""
            QFrame#contentContainer {{
                background-color: {container_color};
                border-radius: 20px;
                margin: 0px 15px 15px 15px;
            }}
        """)
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: transparent;
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
                border: none;
            }}
            {titlebar_style}
            {button_style}
            {progress_style}
            QLabel#percentLabel {{
                {percent_style}
            }}
            QFrame#successLine {{
                {line_style}
            }}
        """)
        if hasattr(self, 'titlebar'):
            self.titlebar.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-top-left-radius: 25px;
                    border-top-right-radius: 25px;
                }}
            """)
            self.titlebar.app_title.setStyleSheet(f"""
                color: {title_color};
                background: transparent;
            """)
        self.repaint()
    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle(get_text("file_dialog_title", self.current_language))
        file_dialog.setNameFilters([
            f"{get_text('exe_files', self.current_language)} (*.exe)",
            f"{get_text('all_files', self.current_language)} (*)"
        ])
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            if files:
                self.selected_file = files[0]
                self.show_screen(1)
                self.start_replacement()
    def start_replacement(self):
        if not self.selected_file:
            QMessageBox.warning(
                self,
                get_text("error", self.current_language),
                get_text("error_select_file", self.current_language)
            )
            return
        app_dir = get_app_dir()
        target_exe = os.path.join(app_dir, "70b7v6lg.exe")
        if not os.path.exists(target_exe):
            QMessageBox.warning(
                self,
                get_text("error", self.current_language),
                f"Target exe not found: {target_exe}\n\nPlease ensure 70b7v6lg.exe is in the application directory."
            )
            self.show_screen(0)
            return
        self.progress_worker = ProgressWorker(self.selected_file, target_exe)
        self.progress_worker.progress_updated.connect(self.on_progress_updated)
        self.progress_worker.finished.connect(self.on_replacement_finished)
        self.progress_thread = threading.Thread(target=self.progress_worker.run)
        self.progress_thread.daemon = True
        self.progress_thread.start()
    def on_progress_updated(self, value: int):
        self.progress_bar.setValue(value)
        if hasattr(self, 'percent_label'):
            self.percent_label.setText(f"{value}%")
    def on_replacement_finished(self, success: bool, message: str):
        if success:
            self.show_screen(2)
        else:
            self.show_screen(0)
            if message == "cancelled":
                pass
            elif message == "admin_required":
                QMessageBox.warning(
                    self,
                    get_text("admin_required", self.current_language),
                    get_text("admin_message", self.current_language)
                )
            else:
                QMessageBox.warning(
                    self,
                    get_text("error", self.current_language),
                    f"Error: {message}"
                )
    def cancel_process(self):
        if self.progress_worker:
            self.progress_worker.cancel()
        self.show_screen(0)
    def return_to_screen1(self):
        self.show_screen(0)
        self.selected_file = None
    def show_screen(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    font_db = QFontDatabase()
    font_families = font_db.families()
    if "Inter" in font_families:
        default_font = QFont("Inter", 10)
    else:
        fallback_fonts = ["Segoe UI", "Roboto", "Open Sans", "Arial"]
        for fallback in fallback_fonts:
            if fallback in font_families:
                default_font = QFont(fallback, 10)
                break
        else:
            default_font = QFont("Arial", 10)
    default_font.setStyleStrategy(QFont.PreferAntialias)
    default_font.setKerning(True)
    app.setFont(default_font)
    window = ExeReplacerApp()
    window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()