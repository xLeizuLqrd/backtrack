from enum import Enum
class Language(Enum):
    RU = "ru"
    EN = "en"
class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"
COLORS = {
    "light": {
        "title_text": "#FF4E00",
        "main_text": "#2B2B2B",
        "main_bg": "#E5E5E5",
        "container_bg": "#FFFFFF",
        "tag_bg": "#E5E5E5",
    },
    "dark": {
        "title_text": "#A19BFD",
        "main_text": "#FFFFFF",
        "main_bg": "#2D2D2D",
        "container_bg": "#3A3A3A",
        "tag_bg": "#2D2D2D",
    }
}
TRANSLATIONS = {
    "ru": {
        "app_title": "backtrack",
        "screen1_choose": "Выберите файл",
        "screen1_open_file": "Открыть файл",
        "screen2_wait": "Подождите...",
        "screen2_subtitle": "Это может занять некоторое время",
        "screen2_cancel": "Отменить",
        "screen3_complete": "Процесс завершён!",
        "screen3_done": "Готово",
        "select_exe": "Выбрать EXE",
        "replace_file": "Заменить файл",
        "selected_file": "Выбранный файл:",
        "no_file_selected": "Файл не выбран",
        "menu": "Меню",
        "theme": "Тема",
        "language": "Язык",
        "light_theme": "Светлая",
        "dark_theme": "Темная",
        "success": "Успех",
        "file_replaced": "Файл успешно заменен!",
        "error": "Ошибка",
        "error_select_file": "Пожалуйста, выберите файл",
        "error_replace": "Ошибка при замене файла: {}",
        "admin_required": "Требуются права администратора",
        "admin_message": "Этот файл находится в системной папке. Требуются права администратора.",
        "file_dialog_title": "Выберите EXE файл",
        "exe_files": "EXE файлы",
        "all_files": "Все файлы",
    },
    "en": {
        "app_title": "backtrack",
        "screen1_choose": "Select a file",
        "screen1_open_file": "Open File",
        "screen2_wait": "Please wait...",
        "screen2_subtitle": "This may take a while",
        "screen2_cancel": "Cancel",
        "screen3_complete": "Process completed!",
        "screen3_done": "Done",
        "select_exe": "Select EXE",
        "replace_file": "Replace File",
        "selected_file": "Selected file:",
        "no_file_selected": "No file selected",
        "menu": "Menu",
        "theme": "Theme",
        "language": "Language",
        "light_theme": "Light",
        "dark_theme": "Dark",
        "success": "Success",
        "file_replaced": "File successfully replaced!",
        "error": "Error",
        "error_select_file": "Please select a file",
        "error_replace": "Error replacing file: {}",
        "admin_required": "Administrator rights required",
        "admin_message": "This file is in a system folder. Administrator rights are required.",
        "file_dialog_title": "Select EXE file",
        "exe_files": "EXE files",
        "all_files": "All files",
    }
}
def get_text(key: str, language: Language) -> str:
    """Получить текст для ключа на указанном языке"""
    return TRANSLATIONS[language.value].get(key, key)
def get_colors(theme: Theme) -> dict:
    """Получить цвета для темы"""
    return COLORS[theme.value]