import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDialog, QLineEdit, QFileDialog, QCheckBox,
    QMessageBox, QSizePolicy, QApplication
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize


class ThemeToggleButton(QPushButton):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setFixedSize(35    , 35)
        self.setCheckable(True)
        self.clicked.connect(self.update_text)
        self.update_text()

    def set_state(self, is_dark):
        self.setChecked(is_dark);
        self.update_text()

    def update_text(self):
        if self.isChecked():
            self.setText(self.translator.get("☀️"))
        else:
            self.setText(self.translator.get("🌙"))

    def is_dark_mode(self):
        return self.isChecked()

    def retranslate_ui(self, translator):
        self.translator = translator;
        self.update_text()


class CreatePromptDialog(QDialog):
    prompt_created = pyqtSignal(dict)

    def __init__(self, translator, parent=None, existing_data=None):
        super().__init__(parent);
        self.translator = translator;
        self.existing_data = existing_data
        self.setMinimumWidth(400);
        self.setLayout(QVBoxLayout())

        self.title_label = QLabel();
        self.title_input = QLineEdit()

        self.positive_prompt_check = QCheckBox()
        self.positive_prompt_check.clicked.connect(self.toggle_positive_prompt_input)

        self.prompt_label = QLabel()
        self.prompt_input = QTextEdit()
        self.prompt_input.setMinimumHeight(100);
        self.prompt_input.setObjectName("PositivePromptText")

        self.negative_prompt_check = QCheckBox()
        self.negative_prompt_check.clicked.connect(self.toggle_negative_prompt_input)
        self.negative_prompt_input = QTextEdit()
        self.negative_prompt_input.setMinimumHeight(70);
        self.negative_prompt_input.hide()
        self.negative_prompt_input.setObjectName("NegativePromptText")

        self.image_path = ""
        self.image_label = QLabel()
        self.image_button = QPushButton()
        self.image_button.clicked.connect(self.select_image)

        self.download_button = QPushButton()
        self.download_button.clicked.connect(self.download_image)
        self.download_button.hide()

        self.save_button = QPushButton();
        self.save_button.clicked.connect(self.save_and_close)

        self.layout().addWidget(self.title_label);
        self.layout().addWidget(self.title_input)

        self.layout().addWidget(self.positive_prompt_check)
        self.layout().addWidget(self.prompt_label);
        self.layout().addWidget(self.prompt_input)

        self.layout().addWidget(self.negative_prompt_check);
        self.layout().addWidget(self.negative_prompt_input)

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_button)
        image_layout.addWidget(self.download_button)
        image_layout.addStretch()
        image_layout.addWidget(self.image_label)
        self.layout().addLayout(image_layout)

        self.layout().addWidget(self.save_button)

        if self.existing_data:
            self.populate_fields()
        else:
            self.positive_prompt_check.setChecked(True)

        self.retranslate_ui()
        self.toggle_positive_prompt_input()
        self.toggle_negative_prompt_input()

    def retranslate_ui(self):
        if self.existing_data:
            self.setWindowTitle(self.translator.get("dialog_edit_title"))
        else:
            self.setWindowTitle(self.translator.get("dialog_create_title"))
        self.title_label.setText(self.translator.get("label_title"));
        self.prompt_label.setText(self.translator.get("label_prompt"))
        if not self.image_path: self.image_label.setText(self.translator.get("label_no_image"))
        self.image_button.setText(self.translator.get("button_select_image"));
        self.save_button.setText(self.translator.get("button_save"))
        self.positive_prompt_check.setText(self.translator.get("checkbox_positive"))
        self.negative_prompt_check.setText(self.translator.get("checkbox_negative"));
        self.negative_prompt_input.setPlaceholderText(self.translator.get("placeholder_negative"))
        self.download_button.setText(self.translator.get("button_download_image"))

    def populate_fields(self):
        self.title_input.setText(self.existing_data.get("title", ""));

        is_positive = self.existing_data.get("is_positive", True)
        self.positive_prompt_check.setChecked(is_positive)
        self.prompt_input.setPlainText(self.existing_data.get("prompt", ""))

        self.image_path = self.existing_data.get("image_path", "")
        if self.image_path and os.path.exists(self.image_path):
            self.image_label.setText(os.path.basename(self.image_path))
            self.download_button.show()
        else:
            self.image_label.setText(self.translator.get("label_no_image"))
            self.download_button.hide()

        is_negative = self.existing_data.get("is_negative", False);
        self.negative_prompt_check.setChecked(is_negative)
        if is_negative: self.negative_prompt_input.setPlainText(
            self.existing_data.get("negative_prompt", ""));

    def toggle_positive_prompt_input(self):
        is_visible = self.positive_prompt_check.isChecked()
        self.prompt_label.setVisible(is_visible)
        self.prompt_input.setVisible(is_visible)

    def toggle_negative_prompt_input(self):
        self.negative_prompt_input.setVisible(self.negative_prompt_check.isChecked())

    def select_image(self):
        title = self.translator.get("file_dialog_title");
        filter = self.translator.get("file_dialog_filter")
        file_name, _ = QFileDialog.getOpenFileName(self, title, "", filter)
        if file_name:
            self.image_path = file_name
            self.image_label.setText(os.path.basename(file_name))
            self.download_button.show()

    def download_image(self):
        if not self.image_path or not os.path.exists(self.image_path):
            print("Download Error: No image path or file not found.")
            return
        title = self.translator.get("file_dialog_save_title");
        filter = self.translator.get("file_dialog_save_filter")
        original_filename = os.path.basename(self.image_path)
        save_path, _ = QFileDialog.getSaveFileName(self, title, original_filename, filter)
        if save_path:
            try:
                shutil.copy(self.image_path, save_path);
                print(f"Image saved to: {save_path}")
            except Exception as e:
                print(f"Error saving image: {e}")

    def get_data_from_fields(self):
        is_positive = self.positive_prompt_check.isChecked()
        is_negative = self.negative_prompt_check.isChecked()

        return {
            "title": self.title_input.text(),
            "is_positive": is_positive,
            "prompt": self.prompt_input.toPlainText() if is_positive else "",
            "image_path": self.image_path,
            "is_negative": is_negative,
            "negative_prompt": self.negative_prompt_input.toPlainText() if is_negative else ""
        }

    def save_and_close(self):
        new_data = self.get_data_from_fields()

        if not new_data["title"]:
            print(self.translator.get("error_validation_failed"))
            QMessageBox.warning(self, "Validation Error", self.translator.get("error_validation_failed"))
            return

        has_image = bool(new_data["image_path"])
        has_positive = is_positive = self.positive_prompt_check.isChecked() and bool(new_data["prompt"])
        has_negative = self.negative_prompt_check.isChecked() and bool(new_data["negative_prompt"])

        if not (has_image or has_positive or has_negative):
            print(self.translator.get("error_validation_failed"))
            QMessageBox.warning(self, "Validation Error", self.translator.get("error_validation_failed"))
            return

        if not self.existing_data:
            self.prompt_created.emit(new_data)
        self.accept()


class DetailsDialog(QDialog):
    def __init__(self, translator, prompt_data, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.prompt_data = prompt_data

        self.setLayout(QVBoxLayout())
        self.setMinimumWidth(500)

        title = self.prompt_data.get("title", "No Title")
        prompt_text = self.prompt_data.get("prompt", "")
        is_positive = self.prompt_data.get("is_positive", True)
        is_negative = self.prompt_data.get("is_negative", False)
        negative_prompt_text = self.prompt_data.get("negative_prompt", "")

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.title_label.setWordWrap(True)
        self.layout().addWidget(self.title_label)

        self.copy_pos_button = QPushButton()
        self.copy_pos_button.clicked.connect(self.copy_positive)

        if is_positive and prompt_text:
            self.prompt_text_area = QTextEdit()
            self.prompt_text_area.setPlainText(prompt_text)
            self.prompt_text_area.setReadOnly(True)
            self.prompt_text_area.setObjectName("PositivePromptText")
            self.prompt_text_area.setMinimumHeight(150)
            self.layout().addWidget(self.prompt_text_area)
            self.layout().addWidget(self.copy_pos_button)
        else:
            self.copy_pos_button.hide()

        self.copy_neg_button = QPushButton()
        self.copy_neg_button.clicked.connect(self.copy_negative)

        if is_negative and negative_prompt_text:
            self.negative_prompt_text_area = QTextEdit()
            prefix = self.translator.get("prefix_negative")
            self.negative_prompt_text_area.setPlainText(f"{prefix}{negative_prompt_text}")
            self.negative_prompt_text_area.setReadOnly(True)
            self.negative_prompt_text_area.setObjectName("NegativePromptText")
            self.negative_prompt_text_area.setMinimumHeight(100)
            self.layout().addWidget(self.negative_prompt_text_area)
            self.layout().addWidget(self.copy_neg_button)
        else:
            self.copy_neg_button.hide()

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        self.layout().addWidget(self.close_button)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(self.translator.get("dialog_details_title"))
        self.close_button.setText(self.translator.get("button_close"))
        self.copy_pos_button.setText(self.translator.get("button_copy_positive"))
        self.copy_neg_button.setText(self.translator.get("button_copy_negative"))

    def copy_positive(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.prompt_data.get("prompt", ""))
        print("Positive prompt copied to clipboard.")

    def copy_negative(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.prompt_data.get("negative_prompt", ""))
        print("Negative prompt copied to clipboard.")


class PromptCard(QWidget):
    edit_requested = pyqtSignal(QWidget)
    delete_requested = pyqtSignal(QWidget)

    def __init__(self, prompt_data, translator):
        super().__init__()
        self.setObjectName("PromptCard")
        self.prompt_data = prompt_data
        self.translator = translator
        self.setFixedWidth(450)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        # DEĞİŞİKLİK: self.ui_container -> self.content_widget olarak yeniden adlandırıldı
        self.content_widget = None
        self.build_ui()

    def build_ui(self):
        # DEĞİŞİKLİK: self.ui_container -> self.content_widget olarak yeniden adlandırıldı
        if self.content_widget:
            self.main_layout.removeWidget(self.content_widget)
            self.content_widget.deleteLater()

        # DEĞİŞİKLİK: self.ui_container -> self.content_widget olarak yeniden adlandırıldı
        self.content_widget = QWidget()
        card_layout = QVBoxLayout(self.content_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        title = self.prompt_data.get("title", "No Title")
        image_path = self.prompt_data.get("image_path", "")

        self.image_label = QLabel()
        image_width = 450;
        image_height = 253
        self.image_label.setFixedSize(image_width, image_height)

        if image_path and os.path.exists(image_path):
            pixmap_original = QPixmap(image_path)
            pixmap_scaled = pixmap_original.scaled(image_width, image_height,
                                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                   Qt.TransformationMode.SmoothTransformation)
            x = (pixmap_scaled.width() - image_width) / 2;
            y = (pixmap_scaled.height() - image_height) / 2
            pixmap_cropped = pixmap_scaled.copy(int(x), int(y), image_width, image_height)
            self.image_label.setPixmap(pixmap_cropped);
            self.image_label.setObjectName("ImageLabel")
        else:
            self.image_label.setObjectName("ImagePlaceholder");
            self.image_label.setText(self.translator.get("placeholder_image"))
        card_layout.addWidget(self.image_label)

        # --- DEĞİŞİKLİK: Başlık (Title) alanı için layout değiştirildi ---
        # Başlık ve butonları içeren ana widget
        self.title_bar_widget = QWidget()
        self.title_bar_widget.setObjectName("PromptCard")

        # Ana layout dikey (QVBoxLayout) olacak: Üstte başlık, altta butonlar
        title_bar_main_layout = QVBoxLayout(self.title_bar_widget)
        title_bar_main_layout.setContentsMargins(10, 10, 10, 10)
        title_bar_main_layout.setSpacing(5)  # Başlık ve butonlar arası boşluk

        # Başlık etiketi
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 15pt; font-weight: bold;")
        self.title_label.setWordWrap(True)
        # Başlığı dikey layout'a ekle (tam genişlik kullanır)
        title_bar_main_layout.addWidget(self.title_label)

        # Butonlar için yatay (QHBoxLayout) bir layout oluştur
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # İç layout'ta ekstra margin olmasın
        button_layout.addStretch()  # Butonları sağa yasla

        # Details butonu
        self.details_button = QPushButton()
        self.details_button.setFixedSize(90, 25)  # Genişlik 110 -> 90
        self.details_button.clicked.connect(self.open_details_dialog)
        button_layout.addWidget(self.details_button)

        # Edit butonu
        self.edit_button = QPushButton()
        self.edit_button.setFixedSize(50, 25);  # Genişlik 60 -> 50
        self.edit_button.clicked.connect(self.request_edit)
        button_layout.addWidget(self.edit_button)

        # Delete butonu
        self.delete_button = QPushButton()
        self.delete_button.setFixedSize(75, 25);
        self.delete_button.clicked.connect(self.confirm_delete)
        button_layout.addWidget(self.delete_button)

        # Butonların olduğu yatay layout'u, ana dikey layout'a ekle
        title_bar_main_layout.addLayout(button_layout)
        # --- DEĞİŞİKLİK SONU ---

        card_layout.addWidget(self.title_bar_widget)

        # DEĞİŞİKLİK: self.ui_container -> self.content_widget olarak yeniden adlandırıldı
        self.main_layout.addWidget(self.content_widget)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        self.retranslate_card_buttons()

    def open_details_dialog(self):
        dialog = DetailsDialog(self.translator, self.prompt_data, self)
        dialog.exec()

    def confirm_delete(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translator.get("confirm_delete_title"))
        msg_box.setText(self.translator.get("confirm_delete_text"))
        msg_box.setIcon(QMessageBox.Icon.Warning)

        yes_button = msg_box.addButton(self.translator.get("button_yes"), QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton(self.translator.get("button_no"), QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_button)

        reply = msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            self.delete_requested.emit(self)

    def retranslate_card_buttons(self):
        self.details_button.setText(self.translator.get("button_details"))
        self.edit_button.setText(self.translator.get("button_edit"))
        self.delete_button.setText(self.translator.get("button_delete"))

    def retranslate_ui(self, translator):
        self.translator = translator
        self.retranslate_card_buttons()
        self.title_label.setText(self.prompt_data.get('title', 'No Title'))

        if not (self.prompt_data.get("image_path") and os.path.exists(self.prompt_data.get("image_path"))):
            self.image_label.setText(self.translator.get("placeholder_image"))

    def update_card_ui(self, new_data):
        self.prompt_data = new_data
        self.build_ui()

    def request_edit(self):
        self.edit_requested.emit(self)

    def sizeHint(self):
        # DEĞİŞİKLİK: self.ui_container -> self.content_widget olarak yeniden adlandırıldı
        return self.content_widget.sizeHint()