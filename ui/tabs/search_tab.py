"""Вкладка поиска статей."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QSpinBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon
import logging
from typing import Optional
import re

from ..custom_widgets import CustomSplitter, CollapsiblePanel
from ..components.article_list import ArticleList
from ..components.article_details import ArticleDetails
from ..components.action_buttons import ActionButtons
from models.article import Article
from services.gigachat_service import GigaChatService
from services.arxiv_service import ArxivService
from utils.translator import translate_text

# Настройка логгера
logger = logging.getLogger(__name__)

class SearchTab(QWidget):
    """Вкладка для поиска статей и отображения результатов."""
    
    # Сигнал о смене источника поиска
    source_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Инициализирует вкладку поиска.
        
        Args:
            parent: Родительский виджет (MainWindow)
        """
        super().__init__(parent)
        self.parent = parent
        # Инициализируем сервисы
        self.gigachat_service = GigaChatService()
        self.arxiv_service = ArxivService()
        # По умолчанию используем ArxivService для поиска
        self.search_service = self.arxiv_service
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс вкладки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Создаем разделитель для верхней и нижней части
        self.search_splitter = CustomSplitter(Qt.Orientation.Vertical, "search_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.search_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)
        
        # Восстановление размеров разделителя
        saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            saved_sizes = self.parent.user_settings.get_splitter_sizes("search_splitter")

        # Создаем панель поиска
        search_panel = self._create_search_panel()
        
        # Создаем сворачиваемую панель для поиска
        search_collapsible = CollapsiblePanel("Поиск статей")
        search_collapsible.set_content(search_panel)
        self.search_splitter.addWidget(search_collapsible)

        # Создаем разделитель для списка и деталей
        self.search_results_splitter = CustomSplitter(Qt.Orientation.Horizontal, "search_results_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.search_results_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)
        
        # Восстановление размеров разделителя результатов
        results_saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            results_saved_sizes = self.parent.user_settings.get_splitter_sizes("search_results_splitter")

        # Список результатов
        results_panel = self._create_results_panel()
        
        # Создаем сворачиваемую панель для результатов
        results_collapsible = CollapsiblePanel("Результаты поиска")
        results_collapsible.set_content(results_panel)
        self.search_results_splitter.addWidget(results_collapsible)

        # Панель с деталями статьи
        details_panel = self._create_details_panel()
        
        # Создаем сворачиваемую панель для деталей
        details_collapsible = CollapsiblePanel("Детали статьи")
        details_collapsible.set_content(details_panel)
        self.search_results_splitter.addWidget(details_collapsible)

        # Установка пропорций разделителя результатов
        if results_saved_sizes:
            self.search_results_splitter.setSizes(results_saved_sizes)
        else:
            self.search_results_splitter.setStretchFactor(0, 1)  # Результаты
            self.search_results_splitter.setStretchFactor(1, 2)  # Детали

        self.search_splitter.addWidget(self.search_results_splitter)

        # Установка пропорций основного разделителя
        if saved_sizes:
            self.search_splitter.setSizes(saved_sizes)
        else:
            self.search_splitter.setStretchFactor(0, 1)  # Поиск
            self.search_splitter.setStretchFactor(1, 4)  # Результаты и детали

        layout.addWidget(self.search_splitter)
        
    def _create_search_panel(self):
        """Создает панель поиска.
        
        Returns:
            Виджет панели поиска
        """
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

        # Выбор источника
        self.source_combo = QComboBox()
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        search_container_layout.addWidget(self.source_combo)

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите поисковый запрос...")
        self.search_input.setFixedWidth(300)
        self.search_input.returnPressed.connect(self._search_articles)
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

        # Количество результатов
        self.results_count = QSpinBox()
        self.results_count.setRange(1, 100)
        self.results_count.setValue(10)
        search_container_layout.addWidget(QLabel("Результатов:"))
        search_container_layout.addWidget(self.results_count)

        # Кнопка поиска
        self.search_button = QPushButton("Поиск")
        self.search_button.setStyleSheet("""
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
        """)
        self.search_button.clicked.connect(self._search_articles)
        search_container_layout.addWidget(self.search_button)

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

        filters_layout.addStretch()
        search_container_layout.addLayout(filters_layout)
        search_layout.addWidget(search_container)
        
        return search_panel
        
    def _create_results_panel(self):
        """Создает панель результатов поиска.
        
        Returns:
            Виджет панели результатов
        """
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(16, 16, 16, 16)
        results_layout.setSpacing(16)

        # Заголовок результатов
        results_title = QLabel("Результаты поиска")
        results_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
        """)
        results_layout.addWidget(results_title)

        # Список результатов
        self.results_list = ArticleList()
        self.results_list.article_selected.connect(self._show_article_info)
        results_layout.addWidget(self.results_list)

        # Кнопка загрузки дополнительных результатов
        load_more_button = QPushButton("Загрузить еще")
        load_more_button.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
            QPushButton:pressed {
                background-color: #9E9E9E;
            }
        """)
        load_more_button.clicked.connect(self._load_more_results)
        results_layout.addWidget(load_more_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        return results_panel
        
    def _create_details_panel(self):
        """Создает панель деталей статьи.
        
        Returns:
            Виджет панели деталей
        """
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(16, 16, 16, 16)
        details_layout.setSpacing(16)

        # Заголовок деталей
        details_title = QLabel("Информация о статье")
        details_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
        """)
        details_layout.addWidget(details_title)

        # Текстовое поле для деталей
        self.article_details = ArticleDetails()
        details_layout.addWidget(self.article_details)

        # Панель действий
        self.action_buttons = ActionButtons(mode="search")
        
        # Подключаем сигналы
        self.action_buttons.summary_clicked.connect(self._create_summary)
        self.action_buttons.references_clicked.connect(self._find_references)
        self.action_buttons.save_clicked.connect(self._save_article)
        self.action_buttons.download_clicked.connect(self._download_article)
        
        details_layout.addWidget(self.action_buttons)
        
        return details_panel
        
    @pyqtSlot(str)
    def _on_source_changed(self, source: str):
        """Обработчик смены источника поиска."""
        if source == "КиберЛенинка":
            self.search_service = self.cyberleninka_service
        else:  # ArXiv
            self.search_service = self.arxiv_service
        self.source_changed.emit(source)
        
    @pyqtSlot()
    def _search_articles(self):
        """Выполняет поиск статей."""
        if not self.search_service:
            logger.error("Сервис поиска не установлен")
            return

        query = self.search_input.text().strip()
        if not query:
            logger.warning("Пустой поисковый запрос")
            return

        try:
            # Отключаем кнопку поиска и показываем статус
            self.search_button.setEnabled(False)
            self.search_button.setText("Поиск...")
            
            # Очищаем предыдущие результаты
            self.clear_results()
            
            # Получаем параметры поиска
            limit = self.results_count.value()
            search_type = self.search_type.currentText()
            
            # Модифицируем запрос в зависимости от типа поиска
            if search_type == "Заголовок":
                query = f"ti:{query}"
            elif search_type == "Автор":
                query = f"au:{query}"
            elif search_type == "Аннотация":
                query = f"abs:{query}"
            elif search_type == "Категория":
                query = f"cat:{query}"
            
            # Выполняем поиск
            articles = self.search_service.search_articles(
                query=query,
                limit=limit,
                page=1
            )
            
            if not articles:
                logger.info("Поиск не дал результатов")
                return
                
            # Добавляем результаты
            for article in articles:
                self.add_search_result(article)
                
            logger.info(f"Найдено {len(articles)} статей")
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {str(e)}", exc_info=True)
        finally:
            # Восстанавливаем кнопку поиска
            self.search_button.setEnabled(True)
            self.search_button.setText("Поиск")
            
    @pyqtSlot()
    def _load_more_results(self):
        """Загружает дополнительные результаты поиска."""
        if hasattr(self.parent, 'load_more_results'):
            self.parent.load_more_results()
            
    @pyqtSlot(Article)
    def _show_article_info(self, article: Article):
        """Отображает информацию о выбранной статье."""
        self.article_details.display_article(article)
        if hasattr(self.parent, 'statusBar'):
            self.parent.statusBar().showMessage(f"Выбрана статья: {article.title}")
            
    @pyqtSlot()
    def _create_summary(self):
        """Создает краткое содержание для выбранной статьи."""
        if hasattr(self.parent, 'create_summary'):
            self.parent.create_summary()
            
    @pyqtSlot()
    def _find_references(self):
        """Ищет источники для выбранной статьи."""
        if hasattr(self.parent, 'find_references'):
            self.parent.find_references()
            
    @pyqtSlot()
    def _save_article(self):
        """Сохраняет выбранную статью в библиотеку."""
        if hasattr(self.parent, 'save_article'):
            self.parent.save_article()
            
    @pyqtSlot()
    def _download_article(self):
        """Скачивает PDF версию статьи."""
        if hasattr(self.parent, 'download_article'):
            self.parent.download_article()
            
    def add_source_selector(self, sources: list[str]):
        """Добавляет селектор источников поиска.
        
        Args:
            sources: Список доступных источников
        """
        self.source_combo.clear()
        self.source_combo.addItems(sources)
        # По умолчанию выбираем ArXiv
        self.source_combo.setCurrentText("ArXiv")
        
    def set_search_service(self, service):
        """Устанавливает сервис поиска.
        
        Args:
            service: Сервис поиска
        """
        self.search_service = service
        if service and hasattr(service, 'check_availability'):
            if not service.check_availability():
                logger.error("Сервис поиска недоступен")
                self.search_button.setEnabled(False)
                self.search_button.setText("Сервис недоступен")
            else:
                self.search_button.setEnabled(True)
                self.search_button.setText("Поиск")
            
    def add_search_result(self, article):
        """Добавляет статью в список результатов поиска.
        
        Args:
            article: Объект статьи
        """
        # Переводим заголовок и аннотацию на русский, если они на английском
        try:
            if article.title and not self._is_russian(article.title):
                article.title = translate_text(article.title, target_lang='ru')
            if article.abstract and not self._is_russian(article.abstract):
                article.abstract = translate_text(article.abstract, target_lang='ru')
        except Exception as e:
            logger.error(f"Ошибка при переводе: {str(e)}")
            
        self.results_list.add_article(article)
        
    def clear_results(self):
        """Очищает список результатов поиска."""
        self.results_list.clear_list()
        self.article_details.clear_details() 
        
    def _is_russian(self, text: str) -> bool:
        """Проверяет, является ли текст русским.
        
        Args:
            text: Проверяемый текст
            
        Returns:
            True, если текст на русском языке
        """
        # Проверяем наличие кириллических символов
        return bool(re.search('[а-яА-Я]', text)) 