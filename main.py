import sys
import json
import os
import csv
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QComboBox, QLineEdit, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt

from layouts import QFlowLayout
from utilities import (
    SettingsManager, Translator,
    LIGHT_THEME_QSS, DARK_THEME_QSS,
    DATA_FILE, SETTINGS_FILE
)
from widgets import (
    ThemeToggleButton, CreatePromptDialog, DetailsDialog, PromptCard, ExportSelectionDialog
)


class PromptBankApp(QMainWindow):
    def __init__(self, app_instance):
        super().__init__()
        self.parent_app = app_instance
        self.settings_manager = SettingsManager(SETTINGS_FILE)
        self.translator = Translator(self.settings_manager)
        self.is_dark_theme = self.settings_manager.get("is_dark_theme", False)
        self.prompts_list = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # --- 1. Bölüm: Üst Çubuk (Top Bar) ---
        self.top_bar_layout = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setFixedSize(400, 35)
        self.search_bar.textChanged.connect(self.filter_prompts)

        self.import_button = QPushButton()
        self.import_button.setFixedSize(130, 35)
        self.import_button.clicked.connect(self.import_backup)

        self.export_button = QPushButton()
        self.export_button.setFixedSize(130, 35)
        self.export_button.clicked.connect(self.export_backup)

        self.create_button = QPushButton()
        self.create_button.setObjectName("CreateButton")
        self.create_button.setFixedSize(130, 35)
        self.create_button.clicked.connect(self.open_create_dialog)

        self.top_bar_layout.addStretch(1)
        self.top_bar_layout.addWidget(self.search_bar)
        self.top_bar_layout.addStretch(1)
        self.top_bar_layout.addWidget(self.import_button)
        self.top_bar_layout.addWidget(self.export_button)
        self.top_bar_layout.addWidget(self.create_button)

        self.main_layout.addLayout(self.top_bar_layout)

        # --- 2. Bölüm: Kaydırma Alanı (Orta) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_content_widget)

        self.scroll_content_layout = QFlowLayout(self.scroll_content_widget)
        self.scroll_content_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_content_layout._h_spacing = 15
        self.scroll_content_layout._v_spacing = 15

        self.main_layout.addWidget(self.scroll_area, 1)

        # --- 3. Bölüm: Durum Çubuğu (Status Bar) ---
        self.status_bar_layout = QHBoxLayout()

        self.theme_toggle_button = ThemeToggleButton(self.translator)
        self.theme_toggle_button.clicked.connect(self.toggle_theme)

        self.language_combo = QComboBox()
        self.language_combo.setFixedSize(100, 35)
        self.language_combo.addItems(["English", "Türkçe"])
        self.language_combo.setItemData(0, "en");
        self.language_combo.setItemData(1, "tr")
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)

        self.status_bar_layout.addStretch(1)
        self.status_bar_layout.addWidget(self.theme_toggle_button)
        self.status_bar_layout.addWidget(self.language_combo)

        self.main_layout.addLayout(self.status_bar_layout)

        self.apply_theme()
        self.retranslate_ui()
        self.load_prompts_from_disk()

        self.showMaximized()

    def retranslate_ui(self):
        self.setWindowTitle(self.translator.get("window_title"))
        self.create_button.setText(self.translator.get("create_button"))
        self.theme_toggle_button.retranslate_ui(self.translator)
        self.search_bar.setPlaceholderText(self.translator.get("search_placeholder"))

        self.import_button.setText(self.translator.get("button_import"))
        self.export_button.setText(self.translator.get("button_export"))

        current_code = self.translator.get_current_language()
        index = self.language_combo.findData(current_code)
        if index != -1:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)

        for i in range(self.scroll_content_layout.count()):
            widget = self.scroll_content_layout.itemAt(i).widget()
            if isinstance(widget, PromptCard): widget.retranslate_ui(self.translator)

    def apply_theme(self):
        self.parent_app.setStyleSheet(DARK_THEME_QSS if self.is_dark_theme else LIGHT_THEME_QSS)
        self.theme_toggle_button.set_state(self.is_dark_theme)

    def toggle_theme(self):
        self.is_dark_theme = self.theme_toggle_button.is_dark_mode()
        self.apply_theme()
        self.settings_manager.set("is_dark_theme", self.is_dark_theme)

    def on_language_changed(self, index):
        new_lang_code = self.language_combo.itemData(index)
        if new_lang_code and new_lang_code != self.translator.get_current_language():
            self.translator.set_language(new_lang_code)
            self.retranslate_ui()

    def export_backup(self):
        # Open the new export dialog
        dialog = ExportSelectionDialog(self.translator, self)
        if dialog.exec():
            selected_format = dialog.get_selected_format()
            self.perform_export(selected_format)

    def perform_export(self, fmt):
        # Map format to extension and filter
        ext_map = {
            "json": ("json", "JSON Files (*.json)"),
            "xml": ("xml", "XML Files (*.xml)"),
            "csv": ("csv", "CSV Files (*.csv)"),
            "yaml": ("yaml", "YAML Files (*.yaml)"),
            "html": ("html", "HTML Files (*.html)"),
            "md": ("md", "Markdown Files (*.md)"),
            "txt": ("txt", "Text Files (*.txt)")
        }
        
        if fmt not in ext_map:
            return
            
        ext, filter_str = ext_map[fmt]
        title = self.translator.get("export_dialog_title")
        
        save_path, _ = QFileDialog.getSaveFileName(self, title, f"prompt_bank_backup.{ext}", filter_str)
        
        if not save_path:
            return
            
        try:
            if fmt == "json":
                self.export_to_json(save_path)
            elif fmt == "xml":
                self.export_to_xml(save_path)
            elif fmt == "csv":
                self.export_to_csv(save_path)
            elif fmt == "yaml":
                self.export_to_yaml(save_path)
            elif fmt == "html":
                self.export_to_html(save_path)
            elif fmt == "md":
                self.export_to_md(save_path)
            elif fmt == "txt":
                self.export_to_txt(save_path)
                
            QMessageBox.information(self,
                                    self.translator.get("export_success_title"),
                                    self.translator.get("export_success_text"))
            print(f"Exported to {save_path} as {fmt}")
            
        except Exception as e:
            print(f"Error exporting to {fmt}: {e}")
            QMessageBox.critical(self, "Error", f"Could not export file: {e}")

    def export_to_json(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.prompts_list, f, indent=4, ensure_ascii=False)

    def export_to_xml(self, filename):
        root = ET.Element("prompts")
        for prompt in self.prompts_list:
            prompt_elem = ET.SubElement(root, "prompt")
            for key, value in prompt.items():
                child = ET.SubElement(prompt_elem, key)
                child.text = str(value)
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ", level=0)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    def export_to_csv(self, filename):
        if not self.prompts_list:
            return
        
        all_keys = set()
        for prompt in self.prompts_list:
            all_keys.update(prompt.keys())
        
        fieldnames = sorted(list(all_keys))
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
            writer.writeheader()
            writer.writerows(self.prompts_list)

    def export_to_yaml(self, filename):
        # Simple custom YAML dumper to avoid dependencies
        with open(filename, "w", encoding="utf-8") as f:
            for prompt in self.prompts_list:
                f.write("- ")
                first = True
                for key, value in prompt.items():
                    if not first:
                        f.write("  ")
                    f.write(f"{key}: ")
                    # Handle multiline strings or special chars simply
                    val_str = str(value)
                    if "\n" in val_str or ":" in val_str:
                        # Block style for multiline
                        f.write("|\n")
                        for line in val_str.splitlines():
                            f.write(f"    {line}\n")
                    else:
                        f.write(f"{val_str}\n")
                    first = False
                f.write("\n")

    def export_to_html(self, filename):
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt Bank Export</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background: #f0f0f0; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .title { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #333; }
        .field { margin-bottom: 5px; }
        .label { font-weight: bold; color: #666; }
        .value { white-space: pre-wrap; }
        .positive { color: green; }
        .negative { color: red; }
    </style>
</head>
<body>
    <h1>Prompt Bank Export</h1>
"""
        for prompt in self.prompts_list:
            html_content += '    <div class="card">\n'
            title = prompt.get("title", "No Title")
            html_content += f'        <div class="title">{title}</div>\n'
            
            for key, value in prompt.items():
                if key == "title": continue
                val_str = str(value)
                if not val_str: continue
                
                cls = "value"
                if key == "prompt": cls += " positive"
                if key == "negative_prompt": cls += " negative"
                
                html_content += f'        <div class="field"><span class="label">{key}:</span> <span class="{cls}">{val_str}</span></div>\n'
            html_content += '    </div>\n'
            
        html_content += "</body>\n</html>"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

    def export_to_md(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Prompt Bank Export\n\n")
            for prompt in self.prompts_list:
                title = prompt.get("title", "No Title")
                f.write(f"## {title}\n")
                for key, value in prompt.items():
                    if key == "title": continue
                    val_str = str(value)
                    if not val_str: continue
                    f.write(f"**{key}:**\n{val_str}\n\n")
                f.write("---\n\n")

    def export_to_txt(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            for prompt in self.prompts_list:
                title = prompt.get("title", "No Title")
                f.write(f"=== {title} ===\n")
                for key, value in prompt.items():
                    if key == "title": continue
                    val_str = str(value)
                    if not val_str: continue
                    f.write(f"{key}: {val_str}\n")
                f.write("\n" + "="*30 + "\n\n")

    def import_backup(self):
        confirm_title = self.translator.get("import_confirm_title")
        confirm_text = self.translator.get("import_confirm_text")

        reply = QMessageBox.warning(self, confirm_title, confirm_text,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            return

        title = self.translator.get("import_dialog_title")
        filter = self.translator.get("import_dialog_filter")

        file_path, _ = QFileDialog.getOpenFileName(self, title, "", filter)

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    imported_data = json.load(f)

                # Başlığa göre birleştirme mantığı
                current_titles = {prompt.get('title') for prompt in self.prompts_list}
                new_prompts_added = 0

                for prompt_data in imported_data:
                    title = prompt_data.get('title')
                    if title and title not in current_titles:
                        self.prompts_list.append(prompt_data)
                        current_titles.add(title)
                        new_prompts_added += 1

                # Sadece yeni prompt eklendiyse kaydet ve yeniden yükle
                if new_prompts_added > 0:
                    self.save_prompts_to_disk()
                    self.reload_all_prompts()

                    QMessageBox.information(self,
                                            self.translator.get("import_success_title"),
                                            self.translator.get("import_success_text").format(count=new_prompts_added))
                else:
                    QMessageBox.information(self,
                                            self.translator.get("import_success_title"),
                                            self.translator.get("import_info_no_new"))

            except Exception as e:
                print(f"Error importing backup: {e}")
                QMessageBox.critical(self,
                                     self.translator.get("import_error_title"),
                                     self.translator.get("import_error_text"))

    def reload_all_prompts(self):
        while self.scroll_content_layout.count():
            child = self.scroll_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.load_prompts_from_disk()

    def filter_prompts(self):
        search_text = self.search_bar.text().lower()
        for i in range(self.scroll_content_layout.count()):
            widget = self.scroll_content_layout.itemAt(i).widget()
            if isinstance(widget, PromptCard):
                title = widget.prompt_data.get("title", "").lower()

                if search_text in title:
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def open_create_dialog(self):
        dialog = CreatePromptDialog(self.translator, self)
        dialog.prompt_created.connect(self.on_prompt_created)
        dialog.exec()

    def on_prompt_created(self, prompt_data):
        self.prompts_list.append(prompt_data)
        self.create_and_add_card(prompt_data)
        self.save_prompts_to_disk()

    def create_and_add_card(self, prompt_data):
        card = PromptCard(prompt_data, self.translator)
        card.edit_requested.connect(self.on_edit_requested)
        card.delete_requested.connect(self.on_delete_requested)
        self.scroll_content_layout.addWidget(card)

    def on_edit_requested(self, card_widget):
        dialog = CreatePromptDialog(self.translator, self, existing_data=card_widget.prompt_data)
        if dialog.exec():
            new_data = dialog.get_data_from_fields()
            try:
                index = self.prompts_list.index(card_widget.prompt_data)
                self.prompts_list[index] = new_data
            except ValueError:
                self.prompts_list.append(new_data)
            card_widget.update_card_ui(new_data)
            self.save_prompts_to_disk()

    def on_delete_requested(self, card_widget):
        data_to_delete = card_widget.prompt_data
        if data_to_delete in self.prompts_list: self.prompts_list.remove(data_to_delete)
        card_widget.deleteLater()
        self.save_prompts_to_disk()

    def save_prompts_to_disk(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.prompts_list, f, indent=4, ensure_ascii=False)
            print("Prompts saved successfully.")
        except Exception as e:
            print(f"Error saving prompts: {e}")

    def load_prompts_from_disk(self):
        if not os.path.exists(DATA_FILE): return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.prompts_list = json.load(f)
            for prompt_data in self.prompts_list:
                if "negative_prompt" not in prompt_data: prompt_data["negative_prompt"] = ""
                if "is_negative" not in prompt_data: prompt_data["is_negative"] = bool(prompt_data["negative_prompt"])
                if "is_positive" not in prompt_data:
                    prompt_data["is_positive"] = True

                self.create_and_add_card(prompt_data)
            print(f"Loaded {len(self.prompts_list)} prompts.")
        except Exception as e:
            print(f"Error loading prompts: {e}"); self.prompts_list = []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PromptBankApp(app_instance=app)
    sys.exit(app.exec())