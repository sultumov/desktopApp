"""Вкладка списка источников."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ..custom_widgets import CustomSplitter, CollapsiblePanel
from ..components.article_list import ArticleList
from ..components.article_details import ArticleDetails
from ..components.action_buttons import ActionButtons

class ReferencesTab(QWidget):
    """Вкладка со списком источников."""
    
    def __init__(self, parent=None):
        """Инициализирует вкладку списка источников.
        
        Args:
            parent: Родительский виджет (MainWindow)
        """
        super().__init__(parent)
        self.parent = parent
        self.current_article = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс вкладки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Создаем горизонтальный разделитель для списка и содержимого
        self.main_splitter = CustomSplitter(Qt.Orientation.Horizontal, "references_main_splitter")
        
        # Панель со списком локальных статей
        list_panel = self._create_list_panel()
        list_collapsible = CollapsiblePanel("Локальные статьи")
        list_collapsible.set_content(list_panel)
        self.main_splitter.addWidget(list_collapsible)
        
        # Панель с содержимым
        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Список источников")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
            }
        """)
        content_layout.addWidget(title_label)

        # Описание
        description = QLabel(
            "Здесь вы можете просмотреть список источников, "
            "использованных в статье."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        content_layout.addWidget(description)

        # Текстовое поле для списка источников
        self.references_view = ArticleDetails()
        content_layout.addWidget(self.references_view)

        # Панель действий
        self.action_buttons = ActionButtons(mode="references")
        
        # Подключаем сигналы
        self.action_buttons.copy_clicked.connect(self._copy_references)
        self.action_buttons.save_clicked.connect(self._save_references)
        
        content_layout.addWidget(self.action_buttons)
        
        # Добавляем панель с содержимым в главный разделитель
        self.main_splitter.addWidget(content_panel)
        
        # Установка пропорций разделителя
        self.main_splitter.setStretchFactor(0, 1)  # Список
        self.main_splitter.setStretchFactor(1, 3)  # Содержимое

        layout.addWidget(self.main_splitter)
        
    def _create_list_panel(self):
        """Создает панель со списком локальных статей."""
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
        self.local_search = QLineEdit()
        self.local_search.setPlaceholderText("Поиск в локальных статьях...")
        self.local_search.textChanged.connect(self._filter_local_articles)
        self.local_search.setStyleSheet("""
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
        container_layout.addWidget(self.local_search)

        list_layout.addWidget(search_container)

        # Список статей
        self.local_articles_list = ArticleList()
        self.local_articles_list.article_selected.connect(self._on_local_article_selected)
        list_layout.addWidget(self.local_articles_list)

        # Кнопка обновления
        refresh_button = QPushButton("Обновить список")
        refresh_button.clicked.connect(self._refresh_local_articles)
        refresh_button.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        list_layout.addWidget(refresh_button)
        
        return list_panel
        
    def _filter_local_articles(self):
        """Фильтрует список локальных статей."""
        self.local_articles_list.filter_articles(self.local_search.text())
        
    def _refresh_local_articles(self):
        """Обновляет список локальных статей."""
        try:
            # Очищаем список
            self.local_articles_list.clear_list()
            
            # Получаем список статей из сервиса
            if hasattr(self.parent, 'arxiv_service'):
                articles = self.parent.arxiv_service.get_local_articles()
                
                # Добавляем статьи в список
                for article in articles:
                    self.local_articles_list.add_article(article)
                    
                if hasattr(self.parent, 'statusBar'):
                    self.parent.statusBar().showMessage(f"Найдено локальных статей: {len(articles)}")
            
        except Exception as e:
            if hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Ошибка при обновлении списка: {str(e)}")
                
    def _on_local_article_selected(self, article):
        """Обрабатывает выбор локальной статьи."""
        try:
            if not article:
                return
                
            # Сохраняем текущую статью
            self.current_article = article
            
            # Получаем список источников
            if hasattr(self.parent, 'find_references'):
                self.parent.find_references(article)
                
        except Exception as e:
            if hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Ошибка при выборе статьи: {str(e)}")
                
    def set_references(self, references, title=None):
        """Отображает список источников.
        
        Args:
            references: Список источников
            title: Заголовок (опционально)
        """
        if isinstance(references, list):
            # Форматируем каждый источник
            formatted_refs = []
            for i, ref in enumerate(references, 1):
                if isinstance(ref, dict):
                    # Если источник - словарь с метаданными
                    ref_text = []
                    if ref.get('authors'):
                        ref_text.append(f"Авторы: {', '.join(ref['authors'])}")
                    if ref.get('year'):
                        ref_text.append(f"Год: {ref['year']}")
                    if ref.get('title'):
                        ref_text.append(f"Название: {ref['title']}")
                    if ref.get('journal'):
                        ref_text.append(f"Журнал: {ref['journal']}")
                    
                    formatted_refs.append(f"{i}. {' | '.join(ref_text)}")
                else:
                    # Если источник - просто текст
                    formatted_refs.append(f"{i}. {ref}")
                    
            text = "\n\n".join(formatted_refs)
        else:
            text = str(references)
            
        self.references_view.display_text(text, title)
        
    def clear_references(self):
        """Очищает список источников."""
        self.references_view.clear_details()
        
    def get_references_text(self):
        """Возвращает текст списка источников."""
        return self.references_view.toPlainText()
        
    def _copy_references(self):
        """Копирует список источников в буфер обмена."""
        if hasattr(self.parent, 'copy_references'):
            self.parent.copy_references()
            
    def _save_references(self):
        """Сохраняет список источников в файл."""
        if hasattr(self.parent, 'save_references'):
            self.parent.save_references() 