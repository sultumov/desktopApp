"""Диалоговое окно настроек приложения."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt

from utils import (
    load_env_settings, save_env_settings, 
    show_error_message, log_exception, gui_exception_handler
)

class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, parent=None):
        """Инициализирует диалог настроек."""
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background: white;
            }
            QComboBox:hover {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(ui/icons/down-arrow.svg);
                width: 12px;
                height: 12px;
            }
            QDialogButtonBox {
                button-layout: spread;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Настройки приложения")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
            }
        """)
        layout.addWidget(title_label)

        # Описание
        description = QLabel(
            "Настройте параметры приложения для работы с ArXiv и AI-сервисами. "
            "Изменения вступят в силу после перезапуска приложения."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(description)

        # Форма настроек
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # AI-сервис
        self.ai_service = QComboBox()
        self.ai_service.addItems(["OpenAI", "Anthropic", "Google"])
        form_layout.addRow("AI-сервис:", self.ai_service)

        # API ключ
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API ключ:", self.api_key)

        # Модель
        self.model = QComboBox()
        self.model.addItems(["GPT-4", "GPT-3.5", "Claude-3", "Gemini"])
        form_layout.addRow("Модель:", self.model)

        # Язык
        self.language = QComboBox()
        self.language.addItems(["Русский", "English"])
        form_layout.addRow("Язык:", self.language)

        # Количество результатов
        self.results_count = QComboBox()
        self.results_count.addItems(["10", "20", "30", "50", "100"])
        form_layout.addRow("Результатов на странице:", self.results_count)

        layout.addLayout(form_layout)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        layout.addWidget(button_box)

        # Загрузка текущих настроек
        self.load_settings()
    
    @gui_exception_handler(show_error_message)
    def load_settings(self):
        """Загружает текущие настройки."""
        settings = load_env_settings('.env')
        
        # Устанавливаем значения, если они есть в настройках
        if 'AI_SERVICE' in settings:
            self.ai_service.setCurrentText(settings['AI_SERVICE'])
        if 'API_KEY' in settings:
            self.api_key.setText(settings['API_KEY'])
        if 'MODEL' in settings:
            self.model.setCurrentText(settings['MODEL'])
        if 'LANGUAGE' in settings:
            self.language.setCurrentText(settings['LANGUAGE'])
        if 'RESULTS_COUNT' in settings:
            self.results_count.setCurrentText(settings['RESULTS_COUNT'])

    @gui_exception_handler(show_error_message)
    def accept(self):
        """Сохраняет настройки и закрывает диалог."""
        # Формируем словарь с настройками
        settings = {
            'AI_SERVICE': self.ai_service.currentText(),
            'API_KEY': self.api_key.text(),
            'MODEL': self.model.currentText(),
            'LANGUAGE': self.language.currentText(),
            'RESULTS_COUNT': self.results_count.currentText()
        }
        
        # Сохраняем настройки
        success, message = save_env_settings('.env', settings)
        
        if success:
            super().accept()
            if self.parent():
                self.parent().settings_changed()
        else:
            show_error_message(self, "Ошибка", f"Не удалось сохранить настройки: {message}") 