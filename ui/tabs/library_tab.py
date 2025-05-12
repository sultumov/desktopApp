"""Вкладка библиотеки статей."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ..custom_widgets import CustomSplitter, CollapsiblePanel
from ..components.article_list import ArticleList
from ..components.article_details import ArticleDetails
from ..components.action_buttons import ActionButtons

class LibraryTab(QWidget):
    """Вкладка с сохраненными статьями в библиотеке."""
    
    def __init__(self, parent=None):
        """Инициализирует вкладку библиотеки.
        
        Args:
            parent: Родительский виджет (MainWindow)
        """
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс вкладки."""
        layout = QVBoxLayout(self)
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

        # Настраиваемый разделитель для списка и деталей
        self.library_splitter = CustomSplitter(Qt.Orientation.Horizontal, "library_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.library_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)

        # Восстановление размеров разделителя
        saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            saved_sizes = self.parent.user_settings.get_splitter_sizes("library_splitter")

        # Панель со списком статей
        list_panel = self._create_list_panel()

        # Создаем сворачиваемую панель для списка
        list_collapsible = CollapsiblePanel("Список статей")
        list_collapsible.set_content(list_panel)
        
        self.library_splitter.addWidget(list_collapsible)

        # Панель с деталями статьи
        details_panel = self._create_details_panel()

        # Создаем сворачиваемую панель для деталей
        details_collapsible = CollapsiblePanel("Детали статьи")
        details_collapsible.set_content(details_panel)
        
        self.library_splitter.addWidget(details_collapsible)

        # Установка пропорций разделителя
        if saved_sizes:
            self.library_splitter.setSizes(saved_sizes)
        else:
            self.library_splitter.setStretchFactor(0, 1)  # Список
            self.library_splitter.setStretchFactor(1, 2)  # Детали

        layout.addWidget(self.library_splitter)
        
    def _create_list_panel(self):
        """Создает панель списка статей.
        
        Returns:
            Виджет панели списка
        """
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
        self.library_search.textChanged.connect(self._filter_library)
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
        self.library_list = ArticleList()
        self.library_list.article_selected.connect(self._show_library_article)
        list_layout.addWidget(self.library_list)
        
        return list_panel
        
    def _create_details_panel(self):
        """Создает панель деталей статьи.
        
        Returns:
            Виджет панели деталей
        """
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        # Текстовое поле для деталей
        self.library_details = ArticleDetails()
        details_layout.addWidget(self.library_details)

        # Панель действий
        self.action_buttons = ActionButtons(mode="library")
        
        # Подключаем сигналы
        self.action_buttons.delete_clicked.connect(self._delete_from_library)
        self.action_buttons.export_clicked.connect(self._export_article)
        
        details_layout.addWidget(self.action_buttons)
        
        return details_panel
        
    def _filter_library(self):
        """Фильтрует список статей по поисковому запросу."""
        if hasattr(self.parent, 'filter_library'):
            self.parent.filter_library(self.library_search.text())
            
    def _show_library_article(self, article):
        """Отображает информацию о выбранной статье."""
        self.library_details.display_article(article)
        if hasattr(self.parent, 'statusBar'):
            self.parent.statusBar().showMessage(f"Выбрана статья: {article.title}")
            
    def _delete_from_library(self):
        """Удаляет статью из библиотеки."""
        if hasattr(self.parent, 'delete_from_library'):
            self.parent.delete_from_library()
            
    def _export_article(self):
        """Экспортирует статью."""
        if hasattr(self.parent, 'export_article'):
            self.parent.export_article()
            
    def add_library_article(self, article):
        """Добавляет статью в список библиотеки.
        
        Args:
            article: Объект статьи
        """
        self.library_list.add_article(article)
        
    def clear_library(self):
        """Очищает список библиотеки."""
        self.library_list.clear_list()
        self.library_details.clear_details()
        
    def get_selected_article(self):
        """Возвращает выбранную статью из библиотеки.
        
        Returns:
            Объект статьи или None, если ничего не выбрано
        """
        return self.library_list.get_selected_article() 