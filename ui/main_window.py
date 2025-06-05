"""Главное окно приложения ArXiv Assistant."""

import sys
import logging
import os
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar,
    QToolButton, QTabWidget, QApplication, QDialog, 
    QMessageBox, QFileDialog, QProgressDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from PyPDF2 import PdfReader

from services import ArxivService, AIService, StorageService, UserSettings
from services.mindmap_service import MindMapService
from .dialogs.settings_dialog import SettingsDialog
from .tabs.search_tab import SearchTab
from .tabs.summary_tab import SummaryTab
from .tabs.references_tab import ReferencesTab
from .tabs.library_tab import LibraryTab
from .styles import MAIN_STYLE

from utils import (
    save_text_to_file, export_article_to_file, open_file, confirm_file_action,
    copy_to_clipboard, show_info_message, show_error_message, show_warning_message, 
    set_status_message, delay_call, confirm_action,
    log_exception, safe_execute, exception_handler, gui_exception_handler,
    download_pdf, is_valid_pdf, load_json_settings, save_json_settings, 
    load_env_settings, save_env_settings, get_config_dir, get_user_data_dir,
    UserSettingsManager
)
from utils.translator import translate_text

# Настройка логгера
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        """Инициализирует главное окно приложения."""
        super().__init__()
        
        try:
            logger.info("Инициализация главного окна")
            
            # Инициализация сервисов
            logger.info("Инициализация ArxivService")
            self.arxiv_service = ArxivService()
            logger.info("Инициализация AIService")
            self.ai_service = AIService()
            logger.info("Инициализация StorageService")
            self.storage_service = StorageService()
            logger.info("Инициализация UserSettings")
            self.user_settings = UserSettings()
            logger.info("Инициализация MindMapService")
            self.mindmap_service = MindMapService()  # Добавляем сервис для интеллект-карт

            # Настройка главного окна
            self.setup_ui()

            # Загружаем статьи в библиотеку при запуске
            self.load_library_articles()

            # Подключаем сигналы
            self.search_tab.article_list.create_mindmap.connect(self.create_mindmap)
            self.search_tab.article_list.find_references.connect(self.find_references)

            logger.info("Главное окно успешно инициализировано")

        except Exception as e:
            logger.error(f"Ошибка при инициализации главного окна: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Ошибка",
                "Произошла ошибка при инициализации приложения. Проверьте логи для деталей."
            )
        
    def setup_ui(self):
        """Настраивает пользовательский интерфейс."""
        # Настройка главного окна
        self.setWindowTitle("ArXiv Assistant")
        self.setMinimumSize(1200, 800)
        
        # Восстановление размера и позиции окна
        window_size = self.user_settings.get_window_size()
        window_position = self.user_settings.get_window_position()
        
        if window_size:
            self.resize(window_size[0], window_size[1])
        if window_position:
            self.move(window_position[0], window_position[1])
            
        # Применяем стили
        self.setStyleSheet(MAIN_STYLE)
            
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Создание панели инструментов
        self.create_toolbar()
        
        # Создание вкладок
        self.create_tabs()
        layout.addWidget(self.tab_widget)
        
        # Создание строки состояния
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: white;
                color: #666666;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)
        
        # Таймер для сохранения настроек при изменении размера окна
        self.resize_timer = QTimer()
        self.resize_timer.setInterval(500)  # Задержка в 500 мс
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.save_window_size)
        
        # Добавляем выбор источника в поисковую вкладку
        self.search_tab.add_source_selector([
            "ArXiv"
        ])
        
        # Подключаем обработчик выбора источника
        self.search_tab.source_changed.connect(self._on_source_changed)
        
    def create_toolbar(self):
        """Создает панель инструментов."""
        toolbar = QToolBar()
        toolbar.setMovable(True)
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
        
    def create_tabs(self):
        """Создает и настраивает вкладки приложения."""
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
        
        # Восстановление текущей вкладки
        current_tab = self.user_settings.get_current_tab()
        
        # Создание вкладок
        self.search_tab = SearchTab(self)
        self.summary_tab = SummaryTab(self)
        self.references_tab = ReferencesTab(self)
        self.library_tab = LibraryTab(self)
        
        # Добавление вкладок
        self.tab_widget.addTab(
            self.search_tab,
            QIcon("ui/icons/search-tab.svg"),
            "Поиск статей"
        )
        self.tab_widget.addTab(
            self.summary_tab,
            QIcon("ui/icons/summary-tab.svg"),
            "Краткое содержание"
        )
        self.tab_widget.addTab(
            self.references_tab,
            QIcon("ui/icons/references-tab.svg"),
            "Поиск источников"
        )
        self.tab_widget.addTab(
            self.library_tab,
            QIcon("ui/icons/library-tab.svg"),
            "Моя библиотека"
        )
        
        # Установка текущей вкладки
        if current_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_tab)
            
        # Отслеживание изменения вкладки
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Добавляем источники поиска
        self.search_tab.add_source_selector(["ArXiv"])
        # Устанавливаем ArXiv как источник по умолчанию
        self.search_tab.set_source("ArXiv")
        
    def resizeEvent(self, event):
        """Обрабатывает событие изменения размера окна."""
        super().resizeEvent(event)
        self.resize_timer.start()
        
    def moveEvent(self, event):
        """Обрабатывает событие перемещения окна."""
        super().moveEvent(event)
        self.resize_timer.start()
        
    def save_window_size(self):
        """Сохраняет размер и позицию окна."""
        self.user_settings.set_window_size(self.width(), self.height())
        self.user_settings.set_window_position(self.x(), self.y())
        self.user_settings.save_settings()
        
    def tab_changed(self, index):
        """Обрабатывает изменение текущей вкладки."""
        self.user_settings.set_current_tab(index)
        self.user_settings.save_settings()
        
    def splitter_sizes_changed(self, name, sizes):
        """Обрабатывает изменение размеров разделителей."""
        self.user_settings.set_splitter_sizes(name, sizes)
        self.user_settings.save_settings()
        
    def closeEvent(self, event):
        """Обрабатывает событие закрытия окна."""
        # Сохраняем размеры и позицию окна
        self.user_settings.set_window_size(self.width(), self.height())
        self.user_settings.set_window_position(self.x(), self.y())
        
        # Сохраняем текущую вкладку
        self.user_settings.set_current_tab(self.tab_widget.currentIndex())
        
        # Сохраняем настройки
        self.user_settings.save_settings()
        
        # Продолжаем обработку события закрытия
        super().closeEvent(event)
        
    def show_settings(self):
        """Показывает диалог настроек."""
        dialog = SettingsDialog(self)
        dialog.exec()
            
    def settings_changed(self):
        """Обработчик изменения настроек."""
        set_status_message(self.statusBar(), "Настройки сохранены. Перезапустите приложение для применения изменений.")
        
    # Методы для работы с поиском статей
    @gui_exception_handler()
    def _translate_arxiv_articles(self, articles: list) -> list:
        """Переводит данные статей ArXiv на русский язык."""
        try:
            for article in articles:
                article.title = translate_text(article.title, 'ru')
                if article.abstract:
                    article.abstract = translate_text(article.abstract, 'ru')
                if article.categories:
                    translated_categories = []
                    for category in article.categories:
                        translated = translate_text(category, 'ru')
                        translated_categories.append(translated)
                    article.categories = translated_categories
            return articles
        except Exception as e:
            logger.error(f"Ошибка при переводе статей: {str(e)}", exc_info=True)
            return articles

    @gui_exception_handler()
    def search_articles(self, query=None, search_type=None, date_filter=None):
        """Выполняет поиск статей."""
        try:
            if not query:
                return
                
            # Получаем текущий источник
            source = self.search_tab.get_current_source()
            logger.info(f"Поиск статей. Источник: {source}, Запрос: {query}, Тип: {search_type}, Фильтр: {date_filter}")
            
            # Формируем поисковый запрос
            search_query = self._build_search_query(query, search_type, date_filter)
            logger.info(f"Сформирован поисковый запрос: {search_query}")
            
            # Отключаем элементы управления на время поиска
            self.search_tab._set_controls_enabled(False)
            
            try:
                # Выполняем поиск в зависимости от источника
                if source == "ArXiv":
                    # Для ArXiv переводим запрос на английский если есть русские символы
                    if bool(re.search('[а-яА-Я]', search_query)):
                        translated_query = translate_text(search_query, 'en')
                        logger.info(f"Запрос переведен на английский: {translated_query}")
                        set_status_message(self.statusBar(), "Выполняется поиск в ArXiv...")
                        articles = self.arxiv_service.search_articles(translated_query)
                        # Переводим результаты обратно на русский
                        articles = self._translate_arxiv_articles(articles)
                    else:
                        logger.info("Поиск на ArXiv без перевода")
                        articles = self.arxiv_service.search_articles(search_query)
                    
                    if not articles:
                        logger.info("Статьи не найдены")
                        show_info_message(
                            self,
                            "Нет результатов",
                            "По вашему запросу ничего не найдено. Попробуйте изменить запрос."
                        )
                        return
                        
                    logger.info(f"Найдено статей: {len(articles)}")
                    
                    # Отображаем результаты
                    self.search_tab.clear_results()  # Очищаем предыдущие результаты
                    for article in articles:
                        self.search_tab.add_search_result(article)
                        logger.debug(f"Добавлена статья: {article.title}")
                    
                    # Обновляем статус
                    set_status_message(self.statusBar(), f"Найдено статей: {len(articles)}")
                        
            except Exception as e:
                logger.error(f"Ошибка при поиске статей: {str(e)}", exc_info=True)
                show_error_message(
                    self,
                    "Ошибка поиска",
                    f"Произошла ошибка при поиске в {source}: {str(e)}"
                )
                return
                
            finally:
                # Включаем элементы управления обратно
                self.search_tab._set_controls_enabled(True)
                
        except Exception as e:
            logger.error(f"Ошибка при поиске статей: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка поиска",
                "Произошла ошибка при поиске статей. Проверьте подключение к интернету и попробуйте снова."
            )
            
    def _build_search_query(self, query, search_type, date_filter):
        """Формирует запрос поиска с учетом типа и фильтра даты."""
        modified_query = query
        
        # Учитываем тип поиска
        if search_type == "Название":
            modified_query = f"ti:{query}"
        elif search_type == "Авторы":
            modified_query = f"au:{query}"
        elif search_type == "Аннотация":
            modified_query = f"abs:{query}"
        elif search_type == "Категория":
            modified_query = f"cat:{query}"
            
        # Учитываем фильтр даты
        if date_filter == "За неделю":
            modified_query = f"{modified_query} AND submittedDate:[NOW-7DAYS TO NOW]"
        elif date_filter == "За месяц":
            modified_query = f"{modified_query} AND submittedDate:[NOW-1MONTH TO NOW]"
        elif date_filter == "За год":
            modified_query = f"{modified_query} AND submittedDate:[NOW-1YEAR TO NOW]"
            
        return modified_query
            
    @gui_exception_handler()
    def load_more_results(self):
        """Загружает дополнительные результаты поиска."""
        set_status_message(self.statusBar(), "Загрузка дополнительных результатов...")
        
        results = self.arxiv_service.load_more()
        
        # Добавляем результаты в список
        for article in results:
            self.search_tab.add_search_result(article)
            
        set_status_message(self.statusBar(), f"Загружено еще {len(results)} статей")
            
    # Методы для работы с кратким содержанием
    @gui_exception_handler()
    def create_summary(self, article=None):
        """Создает краткое содержание статьи.
        
        Args:
            article: Объект статьи (опционально)
        """
        try:
            # Если статья не передана, берем текущую
            if not article:
                article = self.summary_tab.get_current_article()
                
            if not article:
                show_warning_message(
                    self,
                    "Выберите статью",
                    "Пожалуйста, выберите статью для создания краткого содержания."
                )
                return
                
            logger.info(f"Создание краткого содержания для статьи: {article.title}")
            
            # Очищаем ID статьи от URL и версии
            article_id = article.id
            if '/' in article_id:
                article_id = article_id.split('/')[-1]  # Берем последнюю часть после /
            if 'v' in article_id:
                article_id = article_id.split('v')[0]  # Убираем версию
            
            # Проверяем наличие PDF
            pdf_path = None
            if hasattr(article, 'local_pdf_path') and article.local_pdf_path:
                pdf_path = article.local_pdf_path
            elif hasattr(article, 'pdf_url'):
                # Скачиваем PDF если есть URL
                storage_dir = os.path.join("storage", "articles")
                os.makedirs(storage_dir, exist_ok=True)
                pdf_path = os.path.join(storage_dir, f"{article_id}.pdf")
                if not os.path.exists(pdf_path):
                    logger.info(f"Скачивание PDF для статьи {article.title}")
                    if article.source == "arxiv":
                        self.arxiv_service.download_pdf(article, pdf_path)
                    elif article.source == "cyberleninka":
                        self.cyberleninka_service.download_pdf(article, pdf_path)
                    else:
                        show_warning_message(
                            self,
                            "Неподдерживаемый источник",
                            f"Скачивание PDF не поддерживается для источника: {article.source}"
                        )
                        return
                article.local_pdf_path = pdf_path
                
            if not pdf_path or not os.path.exists(pdf_path):
                show_warning_message(
                    self,
                    "PDF не найден",
                    "Для создания краткого содержания необходимо сначала скачать PDF файл статьи."
                )
                # Предлагаем скачать PDF
                if confirm_action(
                    self,
                    "Скачать PDF",
                    "Хотите скачать PDF-версию статьи?",
                    default_yes=True
                ):
                    self.download_article(article)
                return
                
            # Показываем прогресс
            progress = QProgressDialog(
                "Создание краткого содержания...",
                "Отмена",
                0, 100,
                self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            progress.show()
            
            try:
                # Извлекаем текст из PDF
                reader = PdfReader(pdf_path)
                text = ""
                total_pages = len(reader.pages)
                
                for i, page in enumerate(reader.pages):
                    if progress.wasCanceled():
                        return
                    text += page.extract_text() + "\n"
                    progress.setValue((i + 1) * 50 // total_pages)  # Первые 50% - чтение PDF
                
                # Создаем краткое содержание с помощью AI сервиса
                summary = self.ai_service.create_summary(
                    text,
                    style="academic",
                    length="medium"
                )
                progress.setValue(75)  # 75% - создание краткого содержания
                
                # Сохраняем краткое содержание в статью
                article.summary = summary
                article.full_text = text
                
                # Сохраняем обновленную статью
                self.storage_service.update_article(article)
                progress.setValue(90)  # 90% - сохранение статьи
                
                # Отображаем результат в вкладке Summary
                self.summary_tab.set_article(article)
                self.summary_tab.set_summary(summary, article.title)
                
                # Переключаемся на вкладку Summary
                self.tab_widget.setCurrentWidget(self.summary_tab)
                progress.setValue(100)  # 100% - готово
                
                # Обновляем статус
                set_status_message(self.statusBar(), "Краткое содержание создано")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке PDF: {str(e)}", exc_info=True)
                show_error_message(
                    self,
                    "Ошибка",
                    f"Произошла ошибка при обработке PDF: {str(e)}"
                )
            finally:
                progress.close()
            
        except Exception as e:
            logger.error(f"Ошибка при создании краткого содержания: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка",
                f"Произошла ошибка при создании краткого содержания: {str(e)}"
            )
            
    @gui_exception_handler()
    def copy_summary(self):
        """Копирует краткое содержание в буфер обмена."""
        text = self.summary_tab.get_summary_text()
        success, message = copy_to_clipboard(text)
        set_status_message(self.statusBar(), message)
            
    @gui_exception_handler()
    def save_summary(self):
        """Сохраняет краткое содержание в файл."""
        text = self.summary_tab.get_summary_text()
        success, message = save_text_to_file(
            self, 
            text, 
            "Сохранить краткое содержание"
        )
        set_status_message(self.statusBar(), message)
                
    # Методы для работы с источниками
    @gui_exception_handler()
    def find_references(self, article_id: str):
        """Ищет источники для статьи.
        
        Args:
            article_id: Идентификатор статьи
        """
        try:
            # Получаем статью
            article = self.search_tab.article_list.get_selected_article()
            if not article:
                show_warning_message(
                    self,
                    "Выберите статью",
                    "Пожалуйста, выберите статью для поиска источников."
                )
                return
                
            logger.info(f"Поиск источников для статьи: {article.title}")
            
            # Проверяем наличие PDF
            if not hasattr(article, 'pdf_url') and not hasattr(article, 'local_pdf_path'):
                show_warning_message(
                    self,
                    "PDF не найден",
                    "Для поиска источников необходимо сначала скачать PDF файл статьи."
                )
                # Предлагаем скачать PDF
                if confirm_action(
                    self,
                    "Скачать PDF",
                    "Хотите скачать PDF-версию статьи?",
                    default_yes=True
                ):
                    self.download_article()
                return
                
            # Если PDF еще не скачан, скачиваем его
            if not hasattr(article, 'local_pdf_path'):
                pdf_path = os.path.join("storage", "articles", f"{article.id}.pdf")
                if not os.path.exists(pdf_path):
                    logger.info("Скачивание PDF для поиска источников")
                    self.arxiv_service.download_pdf(article, pdf_path)
                article.local_pdf_path = pdf_path
                
            # Показываем прогресс
            progress = QProgressDialog(
                "Поиск источников...",
                "Отмена",
                0, 100,
                self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            
            # Извлекаем источники из PDF
            references = self.ai_service.extract_references(article.local_pdf_path)
            
            if not references:
                show_warning_message(
                    self,
                    "Нет источников",
                    "Не удалось найти источники в статье."
                )
                return
                
            # Сохраняем источники в статью
            article.references = references
            
            # Отображаем результат в вкладке References
            self.references_tab.set_article(article)
            self.references_tab.set_references(references)
            
            # Переключаемся на вкладку References
            self.tab_widget.setCurrentWidget(self.references_tab)
            
            # Обновляем статус
            set_status_message(self.statusBar(), f"Найдено {len(references)} источников")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка",
                f"Произошла ошибка при поиске источников: {str(e)}"
            )
            
    @gui_exception_handler()
    def copy_references(self):
        """Копирует список источников в буфер обмена."""
        references = self.references_tab.get_references()
        if references:
            text = "\n\n".join(references)
            success, message = copy_to_clipboard(text)
            set_status_message(self.statusBar(), message)
        else:
            set_status_message(self.statusBar(), "Нет источников для копирования")
            
    @gui_exception_handler()
    def save_references(self):
        """Сохраняет список источников в файл."""
        references = self.references_tab.get_references()
        if not references:
            set_status_message(self.statusBar(), "Нет источников для сохранения")
            return

        text = "\n\n".join(references)
        success, message = save_text_to_file(
            self, 
            text, 
            "Сохранить источники"
        )
        set_status_message(self.statusBar(), message)
                
    # Методы для работы с библиотекой
    @gui_exception_handler()
    def load_library_articles(self):
        """Загружает статьи из библиотеки."""
        try:
            # Очищаем список
            self.library_tab.clear_library()
            
            # Получаем статьи из хранилища
            articles = self.storage_service.get_articles()
            
            # Добавляем статьи в список
            for article in articles:
                self.library_tab.add_library_article(article)
                
            # Обновляем списки в других вкладках
            self.summary_tab.local_articles_list.clear_list()
            self.references_tab.local_articles_list.clear_list()
            
            for article in articles:
                self.summary_tab.local_articles_list.add_article(article)
                self.references_tab.local_articles_list.add_article(article)
                
            # Обновляем статус
            self.statusBar().showMessage(f"Загружено статей: {len(articles)}")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке статей: {str(e)}", exc_info=True)
            self.statusBar().showMessage("Ошибка при загрузке статей")
            
    @gui_exception_handler()
    def filter_library(self, filter_text):
        """Фильтрует статьи в библиотеке по тексту."""
        articles = self.storage_service.get_articles()
        self.library_tab.clear_library()
        
        for article in articles:
            if (
                filter_text.lower() in article.title.lower() or
                filter_text.lower() in ", ".join(article.authors).lower() or
                filter_text.lower() in ", ".join(article.categories).lower() or
                (article.summary and filter_text.lower() in article.summary.lower())
            ):
                self.library_tab.add_library_article(article)
                
    @gui_exception_handler()
    def delete_from_library(self):
        """Удаляет выбранную статью из библиотеки."""
        article = self.library_tab.get_selected_article()
        if not article:
            set_status_message(self.statusBar(), "Выберите статью для удаления")
            return
            
        # Запрашиваем подтверждение
        if confirm_action(
            self,
            "Удаление статьи",
            f"Вы уверены, что хотите удалить статью '{article.title}'?"
        ):
            self.storage_service.remove_article(article.id)
            self.load_library_articles()
            set_status_message(self.statusBar(), "Статья удалена из библиотеки")
                
    @gui_exception_handler()
    def export_article(self):
        """Экспортирует выбранную статью."""
        article = self.library_tab.get_selected_article()
        if not article:
            set_status_message(self.statusBar(), "Выберите статью для экспорта")
            return
            
        success, message = export_article_to_file(
            self, 
            article, 
            "Экспортировать статью"
        )
        set_status_message(self.statusBar(), message)
                
    @gui_exception_handler()
    def save_article(self):
        """Сохраняет метаданные выбранной статьи в библиотеку."""
        article = self.search_tab.article_list.get_selected_article()
        if not article:
            set_status_message(self.statusBar(), "Выберите статью для сохранения")
            return
        
        set_status_message(self.statusBar(), "Сохранение статьи в библиотеку...")
        
        # Проверяем, существует ли PDF файл
        pdf_path = os.path.join("storage", "articles", f"{article.id}.pdf")
        if os.path.exists(pdf_path):
            # Если файл существует, сохраняем путь к нему
            article.file_path = pdf_path
        else:
            # Иначе просто сохраняем метаданные без файла
            article.file_path = None
        
        # Сохраняем статью в хранилище
        self.storage_service.add_article(article)
        
        # Обновляем список библиотеки
        self.load_library_articles()
        
        set_status_message(self.statusBar(), "Метаданные статьи сохранены в библиотеку")
        
        # Предлагаем скачать PDF, если его нет
        if not os.path.exists(pdf_path):
            if confirm_action(
                self,
                "Скачать PDF",
                "Хотите скачать PDF-версию статьи?",
                default_yes=True
            ):
                self.download_article()
            
    @gui_exception_handler()
    def download_article(self, article=None):
        """Скачивает PDF версию статьи.
        
        Args:
            article: Объект статьи (опционально)
        """
        try:
            # Если статья не передана, берем текущую
            if not article:
                article = self.search_tab.article_list.get_selected_article()
                
            if not article:
                show_warning_message(
                    self,
                    "Выберите статью",
                    "Пожалуйста, выберите статью для скачивания."
                )
                return
                
            logger.info(f"Скачивание статьи: {article.title}")
            
            # Определяем путь для сохранения
            storage_dir = os.path.join("storage", "articles")
            os.makedirs(storage_dir, exist_ok=True)
            
            # Очищаем ID статьи от URL и версии
            article_id = article.id
            if '/' in article_id:
                article_id = article_id.split('/')[-1]  # Берем последнюю часть после /
            if 'v' in article_id:
                article_id = article_id.split('v')[0]  # Убираем версию
                
            pdf_path = os.path.join(storage_dir, f"{article_id}.pdf")
            
            # Скачиваем PDF
            if article.source == "arxiv":
                self.arxiv_service.download_pdf(article, pdf_path)
            elif article.source == "cyberleninka":
                self.cyberleninka_service.download_pdf(article, pdf_path)
            else:
                show_warning_message(
                    self,
                    "Неподдерживаемый источник",
                    f"Скачивание PDF не поддерживается для источника: {article.source}"
                )
                return
                
            # Сохраняем путь к PDF в объект статьи
            article.local_pdf_path = pdf_path
            
            # Обновляем статью в хранилище
            self.storage_service.update_article(article)
            
            # Показываем сообщение об успехе
            set_status_message(self.statusBar(), "PDF успешно скачан")
            
            # После успешного скачивания создаем краткое содержание
            self.create_summary(article)
            
        except Exception as e:
            logger.error(f"Ошибка при скачивании PDF: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка",
                f"Произошла ошибка при скачивании PDF: {str(e)}"
            )

    def _on_source_changed(self, source: str):
        """Обрабатывает изменение источника поиска."""
        try:
            logger.info(f"Выбран источник: {source}")
            
            # Очищаем результаты поиска при смене источника
            self.search_tab.clear_results()
            
        except Exception as e:
            logger.error(f"Ошибка при смене источника: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка",
                "Произошла ошибка при смене источника. Попробуйте перезапустить приложение."
            ) 

    @gui_exception_handler()
    def create_mindmap(self, article_id: str):
        """Создает интеллект-карту для статьи.
        
        Args:
            article_id: Идентификатор статьи
        """
        try:
            # Получаем ключевые слова
            keywords = self.cyberleninka_service.extract_keywords(article_id)
            
            if not keywords:
                show_warning_message(
                    self,
                    "Нет ключевых слов",
                    "Не удалось найти ключевые слова в статье."
                )
                return
                
            # Получаем статью
            article = self.cyberleninka_service.get_article(article_id)
            if not article:
                show_error_message(
                    self,
                    "Ошибка",
                    "Не удалось получить информацию о статье."
                )
                return
                
            # Создаем интеллект-карту
            mindmap_path = self.mindmap_service.create_mindmap(article, keywords)
            
            if mindmap_path:
                # Открываем изображение
                os.startfile(mindmap_path)
            else:
                show_error_message(
                    self,
                    "Ошибка",
                    "Не удалось создать интеллект-карту."
                )
                
        except Exception as e:
            logger.error(f"Ошибка при создании интеллект-карты: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка",
                f"Произошла ошибка при создании интеллект-карты: {str(e)}"
            ) 