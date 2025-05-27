"""Вкладка краткого содержания."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMessageBox,
    QPushButton, QHBoxLayout, QFileDialog,
    QProgressDialog, QDialog, QComboBox,
    QSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView

from ..custom_widgets import CustomSplitter, CollapsiblePanel
from ..components.article_details import ArticleDetails
from ..components.action_buttons import ActionButtons
from models.article import Article
from PyPDF2 import PdfReader
import os
from datetime import datetime

class SummarySettingsDialog(QDialog):
    """Диалог настроек генерации краткого содержания."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки краткого содержания")
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс диалога."""
        layout = QVBoxLayout(self)
        
        # Стиль краткого содержания
        style_label = QLabel("Стиль:")
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Академический",
            "Краткий обзор",
            "Детальный анализ",
            "Ключевые моменты"
        ])
        
        # Длина краткого содержания
        length_label = QLabel("Длина (слов):")
        self.length_spin = QSpinBox()
        self.length_spin.setRange(100, 2000)
        self.length_spin.setValue(500)
        self.length_spin.setSingleStep(50)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Размещение элементов
        layout.addWidget(style_label)
        layout.addWidget(self.style_combo)
        layout.addWidget(length_label)
        layout.addWidget(self.length_spin)
        layout.addWidget(buttons)
        
    def get_settings(self):
        """Возвращает выбранные настройки."""
        return {
            'style': self.style_combo.currentText(),
            'length': self.length_spin.value()
        }

class PDFPreviewDialog(QDialog):
    """Диалог предварительного просмотра PDF."""
    
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр PDF")
        self.setModal(True)
        self.resize(800, 600)
        
        # Проверяем существование файла
        if not os.path.exists(pdf_path):
            QMessageBox.critical(self, "Ошибка", f"Файл не найден: {pdf_path}")
            self.reject()
            return
            
        self.setup_ui(pdf_path)
        
    def setup_ui(self, pdf_path):
        """Настраивает интерфейс диалога."""
        layout = QVBoxLayout(self)
        
        try:
            # PDF просмотрщик
            self.pdf_view = QPdfView(self)
            self.document = QPdfDocument(self)
            
            # Загружаем документ и проверяем статус
            if not self.document.load(pdf_path):
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить PDF файл")
                self.reject()
                return
                
            self.pdf_view.setDocument(self.document)
            layout.addWidget(self.pdf_view)
            
            # Кнопки
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | 
                QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии PDF: {str(e)}")
            self.reject()

class SummaryTab(QWidget):
    """Вкладка с кратким содержанием статьи."""
    
    def __init__(self, parent=None):
        """Инициализирует вкладку краткого содержания.
        
        Args:
            parent: Родительский виджет (MainWindow)
        """
        super().__init__(parent)
        self.parent = parent
        self.current_article = None
        self.current_pdf_path = None
        self.setup_ui()
        
        # Включаем поддержку перетаскивания
        self.setAcceptDrops(True)
        
    def setup_ui(self):
        """Настраивает интерфейс вкладки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Создаем разделитель для верхней и нижней части
        self.summary_splitter = CustomSplitter(Qt.Orientation.Vertical, "summary_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.summary_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)
        
        # Восстановление размеров разделителя
        saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            saved_sizes = self.parent.user_settings.get_splitter_sizes("summary_splitter")

        # Верхняя панель (заголовок и описание)
        top_panel = self._create_info_panel()
        
        # Создаем сворачиваемую панель для заголовка
        header_collapsible = CollapsiblePanel("Информация")
        header_collapsible.set_content(top_panel)
        self.summary_splitter.addWidget(header_collapsible)
        
        # Нижняя панель (текст и кнопки)
        bottom_panel = self._create_content_panel()
        
        # Создаем сворачиваемую панель для содержимого
        content_collapsible = CollapsiblePanel("Содержание")
        content_collapsible.set_content(bottom_panel)
        self.summary_splitter.addWidget(content_collapsible)
        
        # Установка пропорций разделителя
        if saved_sizes:
            self.summary_splitter.setSizes(saved_sizes)
        else:
            self.summary_splitter.setStretchFactor(0, 1)  # Заголовок
            self.summary_splitter.setStretchFactor(1, 3)  # Содержание

        layout.addWidget(self.summary_splitter)
        
    def _create_info_panel(self):
        """Создает информационную панель."""
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Краткое содержание")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
            }
        """)
        top_layout.addWidget(title_label)

        # Описание
        description = QLabel(
            "Здесь вы можете создать краткое содержание статьи с помощью искусственного интеллекта. "
            "Выберите статью на вкладке поиска или перетащите PDF файл статьи сюда."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        top_layout.addWidget(description)

        # Панель с кнопками
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        # Кнопка для выбора файла
        file_button = QPushButton("Выбрать PDF файл")
        file_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 16px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        file_button.clicked.connect(self._select_pdf_file)
        button_layout.addWidget(file_button)

        # Кнопка для пересоздания краткого содержания
        self.regenerate_button = QPushButton("Пересоздать")
        self.regenerate_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.regenerate_button.clicked.connect(self._regenerate_summary)
        self.regenerate_button.setEnabled(False)
        button_layout.addWidget(self.regenerate_button)

        top_layout.addWidget(button_panel)
        
        return top_panel
        
    def _create_content_panel(self):
        """Создает панель содержания.
        
        Returns:
            Виджет панели содержания
        """
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # Текстовое поле для краткого содержания
        self.summary_text = ArticleDetails()
        bottom_layout.addWidget(self.summary_text)

        # Панель действий
        action_panel = QWidget()
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        # Стандартные кнопки действий
        self.action_buttons = ActionButtons(mode="summary")
        self.action_buttons.copy_clicked.connect(self._copy_summary)
        self.action_buttons.save_clicked.connect(self._save_summary)
        action_layout.addWidget(self.action_buttons)

        # Кнопка для поиска источников
        self.find_references_button = QPushButton("Найти источники")
        self.find_references_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.find_references_button.clicked.connect(self._find_references)
        self.find_references_button.setEnabled(False)
        action_layout.addWidget(self.find_references_button)

        bottom_layout.addWidget(action_panel)
        
        return bottom_panel
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обрабатывает начало перетаскивания файла."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.pdf') for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Обрабатывает сброс файла."""
        urls = event.mimeData().urls()
        pdf_files = [url.toLocalFile() for url in urls if url.toLocalFile().lower().endswith('.pdf')]
        
        if pdf_files:
            self._process_pdf_file(pdf_files[0])

    def _select_pdf_file(self):
        """Открывает диалог выбора PDF файла."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите PDF файл",
            "",
            "PDF файлы (*.pdf)"
        )
        
        if file_name:
            self._process_pdf_file(file_name)

    def _process_pdf_file(self, file_path: str):
        """Обрабатывает PDF файл."""
        try:
            # Показываем диалог предпросмотра
            preview_dialog = PDFPreviewDialog(file_path, self)
            if preview_dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Создаем и показываем индикатор прогресса
            progress = QProgressDialog("Обработка PDF файла...", "Отмена", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.show()

            # Читаем PDF файл
            reader = PdfReader(file_path)
            text = ""
            total_pages = len(reader.pages)
            
            for i, page in enumerate(reader.pages):
                if progress.wasCanceled():
                    return
                text += page.extract_text() + "\n"
                progress.setValue((i + 1) * 50 // total_pages)  # Первые 50% - чтение PDF

            # Создаем объект статьи
            file_name = os.path.basename(file_path)
            self.current_article = Article(
                id=f"local_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title=file_name,
                authors=["Неизвестный автор"],
                abstract=text[:1000] + "...",  # Используем начало текста как аннотацию
                year=datetime.now().year,
                published=datetime.now(),
                summary=text,
                doi=None,
                categories=[],
                url=f"file://{file_path}"
            )

            # Сохраняем путь к текущему PDF
            self.current_pdf_path = file_path

            # Создаем краткое содержание
            if hasattr(self.parent, 'ai_service'):
                progress.setLabelText("Генерация краткого содержания...")
                
                # Используем таймер для обновления прогресса
                timer = QTimer(self)
                current_progress = [50]  # Используем список для доступа из замыкания
                
                def update_progress():
                    if current_progress[0] < 90:
                        current_progress[0] += 1
                        progress.setValue(current_progress[0])
                
                timer.timeout.connect(update_progress)
                timer.start(100)  # Обновляем каждые 100 мс
                
                summary = self.parent.ai_service.create_summary(self.current_article)
                
                timer.stop()
                progress.setValue(100)
                
                self.set_summary(summary, self.current_article.title)
                self.find_references_button.setEnabled(True)
                self.regenerate_button.setEnabled(True)
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Сервис AI недоступен. Проверьте настройки приложения."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось обработать PDF файл: {str(e)}"
            )

    def _regenerate_summary(self):
        """Пересоздает краткое содержание с новыми параметрами."""
        if not self.current_article:
            return

        # Показываем диалог настроек
        settings_dialog = SummarySettingsDialog(self)
        if settings_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        settings = settings_dialog.get_settings()
        
        # Показываем индикатор прогресса
        progress = QProgressDialog("Генерация краткого содержания...", "Отмена", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(True)
        progress.show()

        # Используем таймер для обновления прогресса
        timer = QTimer(self)
        current_progress = [0]
        
        def update_progress():
            if current_progress[0] < 90:
                current_progress[0] += 1
                progress.setValue(current_progress[0])
        
        timer.timeout.connect(update_progress)
        timer.start(100)

        try:
            if hasattr(self.parent, 'ai_service'):
                # Добавляем параметры стиля и длины в запрос к AI
                summary = self.parent.ai_service.create_summary(
                    self.current_article,
                    style=settings['style'],
                    max_length=settings['length']
                )
                self.set_summary(summary, self.current_article.title)
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Сервис AI недоступен"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось создать краткое содержание: {str(e)}"
            )
        finally:
            timer.stop()
            progress.setValue(100)

    def _copy_summary(self):
        """Копирует краткое содержание в буфер обмена."""
        if hasattr(self.parent, 'copy_summary'):
            self.parent.copy_summary()
            
    def _save_summary(self):
        """Сохраняет краткое содержание в файл."""
        if hasattr(self.parent, 'save_summary'):
            self.parent.save_summary()

    def _find_references(self):
        """Переходит к поиску источников."""
        if self.current_article and hasattr(self.parent, 'tab_widget'):
            # Находим индекс вкладки с источниками
            for i in range(self.parent.tab_widget.count()):
                if self.parent.tab_widget.tabText(i) == "Поиск источников":
                    # Переключаемся на вкладку
                    self.parent.tab_widget.setCurrentIndex(i)
                    # Запускаем поиск источников
                    if hasattr(self.parent, 'find_references'):
                        self.parent.find_references(self.current_article)
                    break
            
    def set_summary(self, text, title=None):
        """Устанавливает краткое содержание.
        
        Args:
            text: Текст краткого содержания
            title: Заголовок (если есть)
        """
        self.summary_text.display_text(text, title)
        
    def clear_summary(self):
        """Очищает краткое содержание."""
        self.summary_text.clear_details()
        self.current_article = None
        self.find_references_button.setEnabled(False)
        
    def get_summary_text(self):
        """Возвращает текст краткого содержания.
        
        Returns:
            Текст краткого содержания
        """
        return self.summary_text.toPlainText() 