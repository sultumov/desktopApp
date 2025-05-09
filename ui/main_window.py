from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QPushButton, QLabel, QLineEdit, 
    QTextEdit, QListWidget, QSplitter, QFileDialog,
    QStatusBar, QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QFrame, QToolBar, QToolButton, QMessageBox, QApplication, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction
import os
from .styles import MAIN_STYLE, DIALOG_STYLE
from services import ArxivService, AIService, StorageService
import logging

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
    
    def load_settings(self):
        """Загружает текущие настройки."""
        try:
            with open(".env") as f:
                for line in f:
                    if "=" not in line:
                        continue
                    key, value = line.strip().split("=", 1)
                    if key == "AI_SERVICE":
                        self.ai_service.setCurrentText(value)
                    elif key == "API_KEY":
                        self.api_key.setText(value)
                    elif key == "MODEL":
                        self.model.setCurrentText(value)
                    elif key == "LANGUAGE":
                        self.language.setCurrentText(value)
                    elif key == "RESULTS_COUNT":
                        self.results_count.setCurrentText(value)
        except FileNotFoundError:
            pass

    def accept(self):
        """Сохраняет настройки и закрывает диалог."""
        try:
            with open(".env", "w") as f:
                f.write(f"AI_SERVICE={self.ai_service.currentText()}\n")
                f.write(f"API_KEY={self.api_key.text()}\n")
                f.write(f"MODEL={self.model.currentText()}\n")
                f.write(f"LANGUAGE={self.language.currentText()}\n")
                f.write(f"RESULTS_COUNT={self.results_count.currentText()}\n")
            super().accept()
            if self.parent():
                self.parent().settings_changed()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить настройки: {str(e)}"
            )

class MainWindow(QMainWindow):
    def __init__(self):
        """Инициализирует главное окно приложения."""
        super().__init__()

        # Инициализация сервисов
        self.arxiv_service = ArxivService()
        self.ai_service = AIService()
        self.storage_service = StorageService()

        # Настройка главного окна
        self.setWindowTitle("ArXiv Assistant")
        self.setMinimumSize(1200, 800)

        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Применяем стили
        self.setStyleSheet(MAIN_STYLE)

        # Создание панели инструментов
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background: white;
                border-bottom: 1px solid #EEEEEE;
                spacing: 8px;
                padding: 4px;
            }
        """)
        self.addToolBar(toolbar)

        # Кнопка настроек
        settings_button = QToolButton()
        settings_button.setIcon(QIcon("ui/icons/settings.svg"))
        settings_button.setToolTip("Настройки")
        settings_button.clicked.connect(self.show_settings)
        settings_button.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background: #F5F5F5;
            }
            QToolButton:pressed {
                background: #E0E0E0;
            }
        """)
        toolbar.addWidget(settings_button)

        # Создание вкладок
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #666666;
                padding: 8px 16px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #2196F3;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover:!selected {
                background: #e0e0e0;
                color: #333333;
            }
            QTabBar::tab:selected:hover {
                color: #1976D2;
            }
        """)
        layout.addWidget(self.tab_widget)

        # Добавление вкладок
        self.tab_widget.addTab(
            self.create_search_tab(),
            QIcon("ui/icons/search-tab.svg"),
            "Поиск статей"
        )
        self.tab_widget.addTab(
            self.create_summary_tab(),
            QIcon("ui/icons/summary-tab.svg"),
            "Краткое содержание"
        )
        self.tab_widget.addTab(
            self.create_references_tab(),
            QIcon("ui/icons/references-tab.svg"),
            "Поиск источников"
        )
        self.tab_widget.addTab(
            self.create_library_tab(),
            QIcon("ui/icons/library-tab.svg"),
            "Моя библиотека"
        )

        # Создание строки состояния
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: white;
                color: #666666;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        
        # Загружаем статьи в библиотеку при запуске
        self.load_library_articles()

    def create_search_tab(self):
        """Создает вкладку поиска."""
        search_tab = QWidget()
        layout = QVBoxLayout(search_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Создаем панель поиска
        search_panel = QWidget()
        search_panel.setObjectName("searchPanel")
        search_layout = QVBoxLayout(search_panel)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(20)

        # Контейнер для поиска
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_container.setStyleSheet("""
            QWidget#searchContainer {
                background: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
            }
            QWidget#searchContainer:focus-within {
                border: 2px solid #2196F3;
                background: white;
            }
        """)
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(8, 8, 8, 8)
        search_container_layout.setSpacing(10)

        # Иконка поиска
        search_icon = QLabel()
        search_icon.setPixmap(QIcon("ui/icons/search.svg").pixmap(QSize(20, 20)))
        search_icon.setStyleSheet("QLabel { padding: 0; margin: 0; background: transparent; }")
        search_container_layout.addWidget(search_icon)

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.setFixedWidth(300)
        self.search_input.returnPressed.connect(self.search_articles)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 6px;
                color: #333333;
            }
            QLineEdit:focus {
                background: transparent;
            }
        """)
        search_container_layout.addWidget(self.search_input)

        # Фильтры поиска
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(8)

        # Фильтр по типу поиска
        self.search_type = QComboBox()
        self.search_type.addItems(["Везде", "Заголовок", "Аннотация", "Автор", "Категория"])
        self.search_type.setFixedWidth(120)
        self.search_type.setStyleSheet("""
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px 8px;
                background: white;
                color: #333333;
            }
            QComboBox:hover {
                border-color: #2196F3;
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
        """)
        filters_layout.addWidget(self.search_type)

        # Фильтр по дате
        self.date_filter = QComboBox()
        self.date_filter.addItems(["Любая дата", "За неделю", "За месяц", "За год"])
        self.date_filter.setFixedWidth(120)
        self.date_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px 8px;
                background: white;
                color: #333333;
            }
            QComboBox:hover {
                border-color: #2196F3;
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
        """)
        filters_layout.addWidget(self.date_filter)

        # Фильтр по сортировке
        self.sort_filter = QComboBox()
        self.sort_filter.addItems(["По релевантности", "По дате", "По цитируемости"])
        self.sort_filter.setFixedWidth(140)
        self.sort_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px 8px;
                background: white;
                color: #333333;
            }
            QComboBox:hover {
                border-color: #2196F3;
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
        """)
        filters_layout.addWidget(self.sort_filter)

        search_container_layout.addLayout(filters_layout)

        # Кнопка поиска
        search_button = QPushButton()
        search_button.setIcon(QIcon("ui/icons/search.svg"))
        search_button.setToolTip("Поиск")
        search_button.clicked.connect(self.search_articles)
        search_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 4px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        search_container_layout.addWidget(search_button)

        search_layout.addWidget(search_container)

        # Добавляем панель поиска в основной layout
        layout.addWidget(search_panel)

        # Создаем сплиттер для результатов и деталей
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Панель результатов
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(20)

        results_label = QLabel("Результаты поиска")
        results_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        results_layout.addWidget(results_label)

        # Список результатов поиска
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_article_info)
        self.results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
                padding: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #EEEEEE;
                padding: 12px;
                margin: 2px 4px;
                border-radius: 4px;
                background: #F8F9FA;
                color: #333333;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #1565C0;
                border: 1px solid #90CAF9;
            }
            QListWidget::item:hover:!selected {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                color: #1565C0;
            }
        """)
        results_layout.addWidget(self.results_list)

        # Кнопка "Загрузить еще"
        self.load_more_button = QPushButton("Загрузить еще")
        self.load_more_button.setVisible(False)
        self.load_more_button.clicked.connect(self.load_more_results)
        self.load_more_button.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px 16px;
                color: #1565C0;
                font-weight: bold;
                margin: 8px;
            }
            QPushButton:hover {
                background: #E3F2FD;
                border-color: #90CAF9;
            }
            QPushButton:pressed {
                background: #BBDEFB;
            }
        """)
        results_layout.addWidget(self.load_more_button)

        splitter.addWidget(results_panel)

        # Панель деталей
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(20, 20, 20, 20)
        details_layout.setSpacing(20)

        details_label = QLabel("Информация о статье")
        details_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        details_layout.addWidget(details_label)

        self.article_info = QTextEdit()
        self.article_info.setReadOnly(True)
        self.article_info.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background: white;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
                color: #333333;
            }
        """)
        details_layout.addWidget(self.article_info)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        # Кнопка скачивания PDF
        download_button = QPushButton()
        download_button.setIcon(QIcon("ui/icons/download.svg"))
        download_button.setToolTip("Скачать PDF")
        download_button.clicked.connect(self.download_article)
        download_button.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                border-radius: 4px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: #388E3C;
            }
            QPushButton:pressed {
                background: #1B5E20;
            }
        """)
        actions_layout.addWidget(download_button)

        summary_button = QPushButton()
        summary_button.setIcon(QIcon("ui/icons/summary.svg"))
        summary_button.setToolTip("Создать краткое содержание")
        summary_button.clicked.connect(self.create_summary)
        summary_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 4px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        actions_layout.addWidget(summary_button)

        refs_button = QPushButton()
        refs_button.setIcon(QIcon("ui/icons/references.svg"))
        refs_button.setToolTip("Найти источники")
        refs_button.clicked.connect(self.find_references)
        refs_button.setStyleSheet("""
            QPushButton {
                background: #FF9800;
                border-radius: 4px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: #F57C00;
            }
            QPushButton:pressed {
                background: #E65100;
            }
        """)
        actions_layout.addWidget(refs_button)

        save_button = QPushButton()
        save_button.setIcon(QIcon("ui/icons/save.svg"))
        save_button.setToolTip("Сохранить в библиотеку")
        save_button.clicked.connect(self.save_article)
        save_button.setStyleSheet("""
            QPushButton {
                background: #9C27B0;
                border-radius: 4px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: #7B1FA2;
            }
            QPushButton:pressed {
                background: #4A148C;
            }
        """)
        actions_layout.addWidget(save_button)

        actions_layout.addStretch()
        details_layout.addLayout(actions_layout)

        splitter.addWidget(details_panel)

        # Устанавливаем соотношение размеров панелей
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)
        return search_tab
    
    def create_summary_tab(self):
        """Создает вкладку с кратким содержанием."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Краткое содержание")
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
            "Здесь вы можете создать краткое содержание статьи с помощью искусственного интеллекта. "
            "Выберите статью на вкладке поиска и нажмите кнопку 'Создать краткое содержание'."
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

        # Текстовое поле для краткого содержания
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background: white;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
                color: #333333;
            }
        """)
        layout.addWidget(self.summary_text)

        # Панель действий
        actions_panel = QWidget()
        actions_layout = QHBoxLayout(actions_panel)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Кнопка копирования
        copy_button = QPushButton()
        copy_button.setIcon(QIcon("ui/icons/copy.svg"))
        copy_button.setToolTip("Копировать в буфер обмена")
        copy_button.clicked.connect(self.copy_summary)
        copy_button.setFixedSize(40, 40)
        copy_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        actions_layout.addWidget(copy_button)

        # Кнопка сохранения
        save_button = QPushButton()
        save_button.setIcon(QIcon("ui/icons/save.svg"))
        save_button.setToolTip("Сохранить в файл")
        save_button.clicked.connect(self.save_summary)
        save_button.setFixedSize(40, 40)
        save_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        actions_layout.addWidget(save_button)

        actions_layout.addStretch()
        layout.addWidget(actions_panel)

        return tab

    def copy_summary(self):
        """Копирует краткое содержание в буфер обмена."""
        text = self.summary_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.statusBar().showMessage("Краткое содержание скопировано в буфер обмена")
        else:
            self.statusBar().showMessage("Нет краткого содержания для копирования")

    def save_summary(self):
        """Сохраняет краткое содержание в файл."""
        text = self.summary_text.toPlainText()
        if not text:
            self.statusBar().showMessage("Нет краткого содержания для сохранения")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить краткое содержание",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.statusBar().showMessage("Краткое содержание сохранено в файл")
            except Exception as e:
                self.statusBar().showMessage(f"Ошибка при сохранении файла: {str(e)}")
    
    def create_references_tab(self):
        """Создает вкладку с источниками."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Поиск источников")
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
            "Здесь вы можете найти источники, цитируемые в статье. "
            "Выберите статью на вкладке поиска и нажмите кнопку 'Найти источники'."
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

        # Список источников
        self.references_list = QListWidget()
        self.references_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
                padding: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #EEEEEE;
                padding: 12px;
                margin: 2px 4px;
                border-radius: 4px;
                background: #F8F9FA;
                color: #333333;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #1565C0;
                border: 1px solid #90CAF9;
            }
            QListWidget::item:hover:!selected {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                color: #1565C0;
            }
        """)
        layout.addWidget(self.references_list)

        # Панель действий
        actions_panel = QWidget()
        actions_layout = QHBoxLayout(actions_panel)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Кнопка копирования
        copy_button = QPushButton()
        copy_button.setIcon(QIcon("ui/icons/copy.svg"))
        copy_button.setToolTip("Копировать в буфер обмена")
        copy_button.clicked.connect(self.copy_references)
        copy_button.setFixedSize(40, 40)
        copy_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        actions_layout.addWidget(copy_button)

        # Кнопка сохранения
        save_button = QPushButton()
        save_button.setIcon(QIcon("ui/icons/save.svg"))
        save_button.setToolTip("Сохранить в файл")
        save_button.clicked.connect(self.save_references)
        save_button.setFixedSize(40, 40)
        save_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        actions_layout.addWidget(save_button)

        actions_layout.addStretch()
        layout.addWidget(actions_panel)

        return tab

    def copy_references(self):
        """Копирует список источников в буфер обмена."""
        items = []
        for i in range(self.references_list.count()):
            items.append(self.references_list.item(i).text())
        
        if items:
            text = "\n".join(items)
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.statusBar().showMessage("Список источников скопирован в буфер обмена")
        else:
            self.statusBar().showMessage("Нет источников для копирования")

    def save_references(self):
        """Сохраняет список источников в файл."""
        items = []
        for i in range(self.references_list.count()):
            items.append(self.references_list.item(i).text())
        
        if not items:
            self.statusBar().showMessage("Нет источников для сохранения")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить список источников",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write("\n".join(items))
                self.statusBar().showMessage("Список источников сохранен в файл")
            except Exception as e:
                self.statusBar().showMessage(f"Ошибка при сохранении файла: {str(e)}")
    
    def create_library_tab(self):
        """Создает вкладку с библиотекой."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Моя библиотека")
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
            "Здесь хранятся сохраненные вами статьи. "
            "Вы можете просматривать, редактировать и удалять статьи из библиотеки."
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

        # Разделитель для списка и деталей
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Панель со списком статей
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(8)

        # Поле поиска
        search_container = QWidget()
        search_container.setFixedHeight(40)
        search_container.setStyleSheet("""
            QWidget {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }
            QWidget:focus-within {
                border: 1px solid #2196F3;
                background: white;
            }
        """)
        container_layout = QHBoxLayout(search_container)
        container_layout.setContentsMargins(12, 0, 12, 0)
        container_layout.setSpacing(8)

        # Иконка поиска
        search_icon = QLabel()
        search_icon.setPixmap(QIcon("ui/icons/search-tab.svg").pixmap(16, 16))
        search_icon.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        container_layout.addWidget(search_icon)

        # Поле поиска
        self.library_search = QLineEdit()
        self.library_search.setPlaceholderText("Поиск в библиотеке...")
        self.library_search.textChanged.connect(self.filter_library)
        self.library_search.setStyleSheet("""
            QLineEdit {
                border: none;
                background: #F5F5F5;
                font-size: 14px;
                padding: 8px;
                color: #333333;
            }
            QLineEdit:focus {
                background: white;
            }
        """)
        container_layout.addWidget(self.library_search)

        list_layout.addWidget(search_container)

        # Список статей
        self.library_list = QListWidget()
        self.library_list.itemClicked.connect(self.show_library_article)
        self.library_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
                padding: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #EEEEEE;
                padding: 12px;
                margin: 2px 4px;
                border-radius: 4px;
                background: #F8F9FA;
                color: #333333;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #1565C0;
                border: 1px solid #90CAF9;
            }
            QListWidget::item:hover:!selected {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                color: #1565C0;
            }
        """)
        list_layout.addWidget(self.library_list)

        splitter.addWidget(list_panel)

        # Панель с деталями статьи
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        self.library_details = QTextEdit()
        self.library_details.setReadOnly(True)
        self.library_details.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                background: white;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
                color: #333333;
            }
        """)
        details_layout.addWidget(self.library_details)

        # Панель действий
        actions_panel = QWidget()
        actions_layout = QHBoxLayout(actions_panel)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Кнопка удаления
        delete_button = QPushButton()
        delete_button.setIcon(QIcon("ui/icons/delete.svg"))
        delete_button.setToolTip("Удалить из библиотеки")
        delete_button.clicked.connect(self.delete_from_library)
        delete_button.setFixedSize(40, 40)
        delete_button.setStyleSheet("""
            QPushButton {
                background: #F44336;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #D32F2F;
            }
            QPushButton:pressed {
                background: #B71C1C;
            }
        """)
        actions_layout.addWidget(delete_button)

        # Кнопка экспорта
        export_button = QPushButton()
        export_button.setIcon(QIcon("ui/icons/export.svg"))
        export_button.setToolTip("Экспортировать")
        export_button.clicked.connect(self.export_article)
        export_button.setFixedSize(40, 40)
        export_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        actions_layout.addWidget(export_button)

        actions_layout.addStretch()
        details_layout.addLayout(actions_layout)

        splitter.addWidget(details_panel)

        # Установка пропорций разделителя
        splitter.setStretchFactor(0, 1)  # Список
        splitter.setStretchFactor(1, 2)  # Детали

        layout.addWidget(splitter)
        return tab
    
    def filter_library(self):
        """Фильтрует список статей в библиотеке."""
        query = self.library_search.text().lower()
        for i in range(self.library_list.count()):
            item = self.library_list.item(i)
            article = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(
                query not in article.title.lower() and
                not any(query in author.lower() for author in article.authors)
            )

    def show_library_article(self, item):
        """Отображает информацию о выбранной статье из библиотеки."""
        article = item.data(Qt.ItemDataRole.UserRole)
        if not article:
            return
        
        # Проверяем, скачана ли статья
        is_downloaded = self.is_article_downloaded(article.id)
        download_status = "✓ Статья скачана" if is_downloaded else "✗ Статья не скачана"

        # Форматируем дату публикации
        published_date = article.published
        if published_date:
            if isinstance(published_date, str):
                # Если это строка, просто используем её
                formatted_date = published_date
            else:
                # Если это объект datetime, форматируем
                try:
                    formatted_date = published_date.strftime('%d.%m.%Y')
                except:
                    formatted_date = str(published_date)
        else:
            formatted_date = "Не указана"

        info = f"""<h2>{article.title}</h2>
<p><b>Авторы:</b> {', '.join(article.authors)}</p>
<p><b>Дата публикации:</b> {formatted_date}</p>
<p><b>DOI:</b> {article.doi or 'Не указан'}</p>
<p><b>Категории:</b> {', '.join(article.categories)}</p>
<p><b>Статус:</b> {download_status}</p>
<h3>Аннотация</h3>
<p>{article.summary}</p>
"""
        self.library_details.setHtml(info)
        self.statusBar().showMessage(f"Выбрана статья: {article.title}")

    def delete_from_library(self):
        """Удаляет выбранную статью из библиотеки."""
        item = self.library_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для удаления")
            return

        article = item.data(Qt.ItemDataRole.UserRole)
        
        # Проверяем, есть ли файл статьи
        file_exists = self.is_article_downloaded(article.id)
        
        message = "Вы действительно хотите удалить статью из библиотеки?"
        if file_exists:
            message += "\nТакже будет удален PDF файл статьи."

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем файл, если он существует
                if file_exists:
                    file_path = self.get_article_path(article.id)
                    os.remove(file_path)

                # Удаляем из базы данных
                self.storage_service.delete_article(article.id)
                self.library_list.takeItem(self.library_list.row(item))
                self.library_details.clear()
                self.statusBar().showMessage("Статья удалена из библиотеки")
            except Exception as e:
                self.statusBar().showMessage(f"Ошибка при удалении статьи: {str(e)}")

    def export_article(self):
        """Экспортирует выбранную статью."""
        item = self.library_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для экспорта")
            return

        article = item.data(Qt.ItemDataRole.UserRole)
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт статьи",
            f"{article.title}.txt",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )

        if file_name:
            try:
                # Форматируем дату публикации
                published_date = article.published
                if published_date:
                    if isinstance(published_date, str):
                        # Если это строка, просто используем её
                        formatted_date = published_date
                    else:
                        # Если это объект datetime, форматируем
                        try:
                            formatted_date = published_date.strftime('%d.%m.%Y')
                        except:
                            formatted_date = str(published_date)
                else:
                    formatted_date = "Не указана"

                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(f"Название: {article.title}\n")
                    f.write(f"Авторы: {', '.join(article.authors)}\n")
                    f.write(f"Дата публикации: {formatted_date}\n")
                    f.write(f"DOI: {article.doi or 'Не указан'}\n")
                    f.write(f"Категории: {', '.join(article.categories)}\n\n")
                    f.write("Аннотация:\n")
                    f.write(article.summary)
                self.statusBar().showMessage("Статья экспортирована")
            except Exception as e:
                self.statusBar().showMessage(f"Ошибка при экспорте статьи: {str(e)}")
    
    # Слоты (методы обработки событий)
    def search_articles(self):
        """Выполняет поиск статей по запросу."""
        query = self.search_input.text().strip()
        if not query:
            self.statusBar().showMessage("Введите поисковый запрос")
            return
        
        # Отключаем кнопку поиска и показываем статус
        self.search_input.setEnabled(False)
        self.results_list.clear()
        self.article_info.clear()
        self.statusBar().showMessage("Выполняется поиск...")
        
        try:
            articles = self.arxiv_service.search_articles(query)
            
            if not articles:
                self.statusBar().showMessage("Статьи не найдены. Попробуйте изменить запрос.")
                self.load_more_button.setVisible(False)
                return
            
            # Добавляем статьи в список
            for article in articles:
                item = QListWidgetItem()
                item.setText(f"{article.title}\nАвторы: {', '.join(article.authors)}")
                item.setData(Qt.ItemDataRole.UserRole, article)
                self.results_list.addItem(item)
            
            # Показываем кнопку "Загрузить еще", если есть еще результаты
            self.load_more_button.setVisible(self.arxiv_service.has_more_results())
            
            self.statusBar().showMessage(f"Найдено статей: {len(articles)}")
            
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при поиске: {str(e)}")
        
        finally:
            # Включаем поле поиска обратно
            self.search_input.setEnabled(True)

    def load_more_results(self):
        """Загружает следующую страницу результатов поиска."""
        try:
            self.load_more_button.setEnabled(False)
            self.statusBar().showMessage("Загрузка дополнительных результатов...")
            
            articles = self.arxiv_service.load_more()
            
            if articles:
                for article in articles:
                    item = QListWidgetItem()
                    item.setText(f"{article.title}\nАвторы: {', '.join(article.authors)}")
                    item.setData(Qt.ItemDataRole.UserRole, article)
                    self.results_list.addItem(item)
                
                self.statusBar().showMessage(f"Загружено еще {len(articles)} статей")
            else:
                self.statusBar().showMessage("Больше статей не найдено")
                self.load_more_button.setVisible(False)
                return
            
            # Обновляем видимость кнопки
            self.load_more_button.setVisible(self.arxiv_service.has_more_results())
            
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при загрузке результатов: {str(e)}")
        
        finally:
            self.load_more_button.setEnabled(True)

    def show_article_info(self, item):
        """Отображает информацию о выбранной статье."""
        article = item.data(Qt.ItemDataRole.UserRole)
        if not article:
            return
        
        # Проверяем, скачана ли статья
        is_downloaded = self.is_article_downloaded(article.id)
        download_status = "✓ Статья скачана" if is_downloaded else "✗ Статья не скачана"

        # Форматируем дату публикации
        published_date = article.published
        if published_date:
            if isinstance(published_date, str):
                # Если это строка, просто используем её
                formatted_date = published_date
            else:
                # Если это объект datetime, форматируем
                try:
                    formatted_date = published_date.strftime('%d.%m.%Y')
                except:
                    formatted_date = str(published_date)
        else:
            formatted_date = "Не указана"

        info = f"""<h2>{article.title}</h2>
<p><b>Авторы:</b> {', '.join(article.authors)}</p>
<p><b>Дата публикации:</b> {formatted_date}</p>
<p><b>DOI:</b> {article.doi or 'Не указан'}</p>
<p><b>Категории:</b> {', '.join(article.categories)}</p>
<p><b>Статус:</b> {download_status}</p>
<h3>Аннотация</h3>
<p>{article.summary}</p>
"""
        self.article_info.setHtml(info)
        self.statusBar().showMessage(f"Выбрана статья: {article.title}")

    def create_summary(self):
        """Создает краткое содержание выбранной статьи."""
        item = self.results_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для создания краткого содержания")
            return

        article = item.data(Qt.ItemDataRole.UserRole)
        self.statusBar().showMessage("Создание краткого содержания...")
        
        try:
            summary = self.ai_service.create_summary(article)
            self.tab_widget.setCurrentIndex(1)  # Переключаемся на вкладку с кратким содержанием
            self.summary_text.setPlainText(summary)
            self.statusBar().showMessage("Краткое содержание создано")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при создании краткого содержания: {str(e)}")

    def find_references(self):
        """Ищет источники для выбранной статьи."""
        item = self.results_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для поиска источников")
            return

        article = item.data(Qt.ItemDataRole.UserRole)
        self.statusBar().showMessage("Поиск источников...")
        
        try:
            references = self.ai_service.find_references(article)
            self.tab_widget.setCurrentIndex(2)  # Переключаемся на вкладку с источниками
            self.references_list.clear()
            for ref in references:
                self.references_list.addItem(ref)
            self.statusBar().showMessage(f"Найдено источников: {len(references)}")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при поиске источников: {str(e)}")

    def save_article(self):
        """Сохраняет выбранную статью в библиотеку."""
        item = self.results_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для сохранения")
            return
        
        article = item.data(Qt.ItemDataRole.UserRole)
        self.statusBar().showMessage("Сохранение статьи...")
        
        try:
            # Создаем путь к файлу даже если файла еще нет
            file_path = os.path.join("storage", "articles", f"{article.id}.pdf")
            
            # Обновляем путь к файлу в статье
            article.file_path = file_path
            
            # Сохраняем статью в хранилище
            self.storage_service.add_article(article)
            
            # Обновляем список библиотеки
            self.load_library_articles()
            
            self.statusBar().showMessage("Статья сохранена в библиотеку")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при сохранении статьи: {str(e)}")

    def download_article(self):
        """Скачивает PDF версию статьи."""
        item = self.results_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для скачивания")
            return
        
        article = item.data(Qt.ItemDataRole.UserRole)
        if not article:
            return
        
        try:
            # Создаем имя файла на основе ID статьи
            file_name = os.path.join("storage", "articles", f"{article.id}.pdf")
            
            # Проверяем, существует ли уже файл
            if os.path.exists(file_name):
                reply = QMessageBox.question(
                    self,
                    "Файл существует",
                    "Статья уже скачана. Хотите открыть её?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(file_name)
                return

            self.statusBar().showMessage("Скачивание статьи...")
            
            # Скачиваем PDF
            self.arxiv_service.download_pdf(article, file_name)
            self.statusBar().showMessage(f"Статья сохранена в {file_name}")

            # Добавляем статью в библиотеку
            self.storage_service.add_article(article, file_name)
            
            # Обновляем список библиотеки
            self.load_library_articles()

            # Спрашиваем пользователя, хочет ли он открыть статью
            reply = QMessageBox.question(
                self,
                "Статья скачана",
                "Статья успешно скачана. Открыть её?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(file_name)
            
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при скачивании статьи: {str(e)}")

    def get_article_path(self, article_id):
        """Возвращает путь к файлу статьи в локальном хранилище."""
        return os.path.join("storage", "articles", f"{article_id}.pdf")

    def is_article_downloaded(self, article_id):
        """Проверяет, скачана ли статья."""
        return os.path.exists(self.get_article_path(article_id))

    def open_article(self, article_id):
        """Открывает статью из локального хранилища."""
        file_path = self.get_article_path(article_id)
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            self.statusBar().showMessage("Статья не найдена в локальном хранилище")

    def load_library_articles(self):
        """Загружает статьи из библиотеки."""
        # Очищаем текущий список
        self.library_list.clear()
        
        try:
            # Получаем статьи из хранилища
            articles = self.storage_service.get_articles()
            
            # Если статей нет, показываем сообщение
            if not articles:
                self.statusBar().showMessage("Библиотека пуста")
                return
                
            # Добавляем статьи в список
            for article in articles:
                item = QListWidgetItem()
                item.setText(f"{article.title}\nАвторы: {', '.join(article.authors)}")
                item.setData(Qt.ItemDataRole.UserRole, article)
                self.library_list.addItem(item)
                
            self.statusBar().showMessage(f"Загружено статей: {len(articles)}")
            
            # Применяем текущий фильтр
            self.filter_library()
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при загрузке библиотеки: {str(e)}")
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при загрузке библиотеки: {str(e)}")

    def show_settings(self):
        """Показывает диалог настроек."""
        dialog = SettingsDialog(self)
        dialog.exec()
            
    def settings_changed(self):
        """Обработчик изменения настроек."""
        self.statusBar().showMessage("Настройки сохранены. Перезапустите приложение для применения изменений.")

    def download_article(self):
        """Скачивает PDF версию статьи."""
        item = self.results_list.currentItem()
        if not item:
            self.statusBar().showMessage("Выберите статью для скачивания")
            return

        article = item.data(Qt.ItemDataRole.UserRole)
        if not article:
            return
        
        try:
            # Создаем имя файла на основе ID статьи
            file_name = os.path.join("storage", "articles", f"{article.id}.pdf")
            
            # Проверяем, существует ли уже файл
            if os.path.exists(file_name):
                reply = QMessageBox.question(
                    self,
                    "Файл существует",
                    "Статья уже скачана. Хотите открыть её?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(file_name)
                return

            self.statusBar().showMessage("Скачивание статьи...")
            
            # Скачиваем PDF
            self.arxiv_service.download_pdf(article, file_name)
            self.statusBar().showMessage(f"Статья сохранена в {file_name}")

            # Добавляем статью в библиотеку
            self.storage_service.add_article(article, file_name)
            
            # Обновляем список библиотеки
            self.load_library_articles()

            # Спрашиваем пользователя, хочет ли он открыть статью
            reply = QMessageBox.question(
                self,
                "Статья скачана",
                "Статья успешно скачана. Открыть её?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(file_name)

        except Exception as e:
            self.statusBar().showMessage(f"Ошибка при скачивании статьи: {str(e)}") 