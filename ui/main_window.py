"""Главное окно приложения ArXiv Assistant."""

import sys
import logging
import os
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar,
    QToolButton, QTabWidget, QApplication, QDialog, 
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon

from services import ArxivService, AIService, StorageService, UserSettings
from services.cyberleninka_service import CyberleninkaService
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
            # Инициализация сервисов
            self.arxiv_service = ArxivService()
            self.cyberleninka_service = CyberleninkaService()
            self.ai_service = AIService()
            self.storage_service = StorageService()
            self.user_settings = UserSettings()

            # Настройка главного окна
            self.setup_ui()

            # Загружаем статьи в библиотеку при запуске
            self.load_library_articles()

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
            "ArXiv",
            "КиберЛенинка"
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
            
            # Проверяем язык запроса
            is_russian_query = bool(re.search('[а-яА-Я]', query))
            
            # Если запрос на русском, используем только КиберЛенинку
            if is_russian_query and source == "ArXiv":
                show_warning_message(
                    self,
                    "Русскоязычный запрос",
                    "Для поиска на русском языке используйте КиберЛенинку. Переключаем источник автоматически."
                )
                self.search_tab.set_source("КиберЛенинка")
                source = "КиберЛенинка"
            
            # Формируем поисковый запрос
            search_query = self._build_search_query(query, search_type, date_filter)
            
            # Отключаем элементы управления на время поиска
            self.search_tab._set_controls_enabled(False)
            
            try:
                # Выполняем поиск в зависимости от выбранного источника
                if source == "ArXiv":
                    # Для ArXiv переводим запрос на английский
                    translated_query = translate_text(search_query, 'en')
                    set_status_message(self.statusBar(), "Выполняется поиск в ArXiv...")
                    
                    articles = self.arxiv_service.search_articles(translated_query)
                    
                    if not articles:
                        set_status_message(self.statusBar(), "Статьи не найдены")
                        show_info_message(
                            self,
                            "Результаты поиска",
                            "По вашему запросу ничего не найдено. Попробуйте изменить запрос или параметры поиска."
                        )
                        return
                    
                    # Переводим результаты на русский
                    set_status_message(self.statusBar(), "Переводим результаты на русский язык...")
                    articles = self._translate_arxiv_articles(articles)
                    
                    # Обновляем UI
                    self.search_tab.display_results(articles)
                    set_status_message(self.statusBar(), f"Найдено статей: {len(articles)}")
                    
                elif source == "КиберЛенинка":
                    # Проверяем доступность сервиса
                    if not self.cyberleninka_service.check_availability():
                        show_warning_message(
                            self,
                            "КиберЛенинка временно недоступна",
                            "Сервис КиберЛенинки сейчас недоступен. Попробуйте позже."
                        )
                        return
                    
                    articles = self.cyberleninka_service.search_articles(search_query)
                    
                    if not articles:
                        show_info_message(
                            self,
                            "Нет результатов",
                            "По вашему запросу ничего не найдено. Попробуйте изменить запрос."
                        )
                        return
                        
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
    def create_summary(self):
        """Создает краткое содержание для выбранной статьи."""
        article = self.search_tab.results_list.get_selected_article()
        if not article:
            set_status_message(self.statusBar(), "Выберите статью для создания краткого содержания")
            return
            
        set_status_message(self.statusBar(), "Создание краткого содержания с помощью GigaChat...")
        
        # Используем GigaChat для создания краткого содержания
        summary = self.ai_service.create_summary(article)
        self.summary_tab.set_summary(summary, article.title)
        self.tab_widget.setCurrentIndex(1)  # Переключаемся на вкладку с кратким содержанием
        set_status_message(self.statusBar(), "Краткое содержание создано")
            
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
    def find_references(self, article=None):
        """Ищет источники для выбранной статьи.
        
        Args:
            article: Объект статьи (опционально). Если не указан, берется выбранная статья.
        """
        if article is None:
            article = self.search_tab.results_list.get_selected_article()
            
        if not article:
            set_status_message(self.statusBar(), "Выберите статью для поиска источников")
            return
            
        set_status_message(self.statusBar(), "Поиск источников и анализ текста статьи с помощью GigaChat...")
        
        try:
            # Используем ai_service для поиска источников через GigaChat
            references = self.ai_service.find_references(article)
            
            if not references:
                set_status_message(self.statusBar(), "Не удалось найти источники для данной статьи")
                return
                
            self.tab_widget.setCurrentIndex(2)  # Переключаемся на вкладку с источниками
            self.references_tab.clear_references()

                # Добавляем найденные источники в список
            for ref in references:
                self.references_tab.add_reference(ref)
            
            set_status_message(self.statusBar(), f"Найдено источников: {len(references)}")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}", exc_info=True)
            set_status_message(self.statusBar(), f"Ошибка при поиске источников: {str(e)}")
            
            # Добавляем информацию о проблеме на вкладку с источниками
            self.tab_widget.setCurrentIndex(2)  # Переключаемся на вкладку с источниками
            self.references_tab.clear_references()
            self.references_tab.add_reference("Не удалось найти источники для данной статьи")
            self.references_tab.add_reference(f"Причина: {str(e)}")
            self.references_tab.add_reference("Убедитесь, что у вас правильно настроен API ключ GigaChat в настройках")
            
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
        # Очищаем текущий список
        self.library_tab.clear_library()
        
        # Получаем статьи из хранилища
        articles = self.storage_service.get_articles()
        
        # Выводим отладочную информацию
        logger.info(f"Загружаем статьи из хранилища. Всего статей: {len(articles)}")
        
        # Если статей нет, показываем сообщение
        if not articles:
            logger.warning("Библиотека пуста - статьи не найдены")
            set_status_message(self.statusBar(), "Библиотека пуста")
            return
            
        # Добавляем статьи в список
        for article in articles:
            self.library_tab.add_library_article(article)
            
        set_status_message(self.statusBar(), f"Загружено статей: {len(articles)}")
            
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
    def download_article(self):
        """Скачивает PDF версию статьи."""
        article = self.search_tab.article_list.get_selected_article()
        if not article:
            # Если нет выбранной статьи в результатах поиска, проверяем библиотеку
            article = self.library_tab.get_selected_article()
            if not article:
                set_status_message(self.statusBar(), "Выберите статью для скачивания")
                return
            
        # Создаем имя файла на основе ID статьи
        file_name = os.path.join("storage", "articles", f"{article.id}.pdf")
        
        # Проверяем, существует ли уже файл
        if os.path.exists(file_name):
            if confirm_action(
                self,
                "Файл существует",
                "Статья уже скачана. Хотите открыть её?",
                default_yes=True
            ):
                success, message = open_file(file_name)
                set_status_message(self.statusBar(), message)
            return

        set_status_message(self.statusBar(), "Скачивание статьи...")
        
        # Скачиваем PDF
        self.arxiv_service.download_pdf(article, file_name)
        set_status_message(self.statusBar(), f"Статья сохранена в {file_name}")

        # Обновляем путь к файлу в статье и сохраняем в библиотеку
        article.file_path = file_name
        self.storage_service.add_article(article)
        
        # Обновляем список библиотеки
        self.load_library_articles()

        # Спрашиваем пользователя, хочет ли он открыть статью
        if confirm_action(
            self,
            "Статья скачана",
            "Статья успешно скачана. Открыть её?",
            default_yes=True
        ):
            success, message = open_file(file_name)
            if not success:
                set_status_message(self.statusBar(), message)

    def _on_source_changed(self, source: str):
        """Обрабатывает изменение источника поиска."""
        try:
            logger.info(f"Выбран источник: {source}")
            
            if source == "КиберЛенинка":
                # Проверяем доступность сервиса при переключении
                if not self.cyberleninka_service.check_availability():
                    show_warning_message(
                        self,
                        "КиберЛенинка временно недоступна",
                        "Сервис КиберЛенинки сейчас недоступен. Попробуйте позже или выберите другой источник."
                    )
                    # Возвращаемся к ArXiv
                    self.search_tab.set_source("ArXiv")
                    return
                    
            # Очищаем результаты поиска при смене источника
            self.search_tab.clear_results()
            
        except Exception as e:
            logger.error(f"Ошибка при смене источника: {str(e)}", exc_info=True)
            show_error_message(
                self,
                "Ошибка",
                "Произошла ошибка при смене источника. Попробуйте перезапустить приложение."
            ) 