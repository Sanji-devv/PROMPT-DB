import os
import json

DATA_FILE = "prompts_data.json"
SETTINGS_FILE = "settings.json"
TRANSLATIONS_FILE = "translations.json"

LIGHT_THEME_QSS = """
    QWidget { background-color: #F0F0F0; color: #000000; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
    QMainWindow, QDialog { background-color: #F0F0F0; }
    QPushButton { background-color: #E0E0E0; border: 1px solid #C0C0C0; padding: 5px 10px; border-radius: 5px; }
    QPushButton:hover { background-color: #E8E8E8; }
    QPushButton#CreateButton { background-color: #007BFF; color: white; border: none; font-weight: bold; }
    QPushButton#CreateButton:hover { background-color: #0056b3; }
    QTextEdit, QLineEdit { background-color: #FFFFFF; color: #000000; border: 1px solid #C0C0C0; border-radius: 5px; padding: 5px; }
    QScrollArea { border: none; }
    #PromptCard { background-color: #FFFFFF; border: 1px solid #DDD; border-radius: 8px; }
    #ImagePlaceholder { background-color: #EEE; border: 1px solid #CCC; text-align: center; border-radius: 8px; color: #888; border-bottom-left-radius: 0; border-bottom-right-radius: 0;}
    #ImageLabel { border-top-left-radius: 8px; border-top-right-radius: 8px; }
    QCheckBox { color: #000000; }
    QTextEdit#PositivePromptText { color: #006400; border: 1px solid #AADDAA; }
    QTextEdit#NegativePromptText { color: #B00000; border: 1px solid #D9534F; }
    QComboBox { background-color: #E0E0E0; border: 1px solid #C0C0C0; padding: 5px; border-radius: 5px; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background-color: #FFFFFF; border: 1px solid #C0C0C0; }
"""

DARK_THEME_QSS = """
    QWidget { background-color: #2E2E2E; color: #E0E0E0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
    QMainWindow, QDialog { background-color: #2E2E2E; }
    QPushButton { background-color: #4A4A4A; border: 1px solid #606060; padding: 5px 10px; border-radius: 5px; color: #E0E0E0; }
    QPushButton:hover { background-color: #5A5A5A; }
    QPushButton#CreateButton { background-color: #007BFF; color: white; border: none; font-weight: bold; }
    QPushButton#CreateButton:hover { background-color: #0056b3; }
    QTextEdit, QLineEdit { background-color: #3A3A3A; color: #E0E0E0; border: 1px solid #606060; padding: 5px; }
    QScrollArea { border: none; }
    #PromptCard { background-color: #3A3A3A; border: 1px solid #505050; border-radius: 8px; }
    #ImagePlaceholder { background-color: #404040; border: 1px solid #606060; text-align: center; border-radius: 8px; color: #999; border-bottom-left-radius: 0; border-bottom-right-radius: 0;}
    #ImageLabel { border-top-left-radius: 8px; border-top-right-radius: 8px; }
    QCheckBox { color: #E0E0E0; }
    QTextEdit#PositivePromptText { color: #A0F0A0; border: 1px solid #008000; }
    QTextEdit#NegativePromptText { color: #F0A0A0; border: 1px solid #D9534F; }
    QComboBox { background-color: #4A4A4A; border: 1px solid #606060; padding: 5px; border-radius: 5px; color: #E0E0E0; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background-color: #3A3A3A; border: 1px solid #606060; color: #E0E0E0; }
"""

class SettingsManager:
    def __init__(self, filename):
        self.filename = filename
        self.settings = self.load_settings()

    def load_settings(self):
        defaults = {
            "is_dark_theme": False,
            "language": "en"
        }
        if not os.path.exists(self.filename): return defaults
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                settings_data = json.load(f)
            defaults.update(settings_data);
            return defaults
        except Exception as e:
            print(f"Error loading settings: {e}. Using defaults."); return defaults

    def save_settings(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
            print("Settings saved.")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value; self.save_settings()


class Translator:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.translations = {};
        self.load_translations()
        self.current_lang = self.settings_manager.get("language", "en")

    def load_translations(self):
        if not os.path.exists(TRANSLATIONS_FILE): print(f"Error: {TRANSLATIONS_FILE} not found!"); return
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Error loading translations: {e}")

    def get(self, key):
        return self.translations.get(self.current_lang, {}).get(key, key)

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code; self.settings_manager.set("language", lang_code)
        else:
            print(f"Warning: Language '{lang_code}' not found in translations.")

    def get_current_language(self):
        return self.current_lang