"""Компонент для отображения списка статей."""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
import logging

logger = logging.getLogger(__name__)

class ArticleList(QListWidget):
    """Виджет для отображения списка статей."""
    
    # Сигналы
    article_selected = pyqtSignal(object)
    create_mindmap = pyqtSignal(str)  # Сигнал для создания интеллект-карты
    find_references = pyqtSignal(str)  # Сигнал для поиска источников
    
    def __init__(self, parent=None):
        """Инициализирует список статей.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 4px;
            }
            
            QListWidget::item {
                color: #2C3E50;
                background: white;
                border-bottom: 1px solid #ECF0F1;
                padding: 8px;
            }
            
            QListWidget::item:selected {
                color: white;
                background: #3498DB;
                border-radius: 4px;
            }
            
            QListWidget::item:hover:!selected {
                background: #ECF0F1;
                border-radius: 4px;
            }
        """)
        self.articles = []
        self.currentItemChanged.connect(self._on_item_changed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def add_article(self, article):
        """Добавляет статью в список.
        
        Args:
            article: Объект статьи
        """
        try:
            if not article:
                logger.warning("Попытка добавить пустую статью")
                return
                
            logger.info(f"Добавление статьи в список: {article.title}")
            
            # Создаем текст для отображения
            title = getattr(article, 'title', 'Без названия')
            authors = getattr(article, 'authors', [])
            published = getattr(article, 'published', None)
            
            display_text = title
            
            if authors:
                display_text += f"\nАвторы: {', '.join(authors[:3])}"
                if len(authors) > 3:
                    display_text += " и др."
                    
            if published:
                try:
                    date_str = published.strftime('%d.%m.%Y')
                    display_text += f"\nДата: {date_str}"
                except:
                    logger.warning(f"Не удалось отформатировать дату для статьи: {title}")
                    pass
            
            # Создаем элемент списка
            item = QListWidgetItem(display_text)
            item.setData(100, article)  # Сохраняем статью в пользовательских данных
            
            self.addItem(item)
            self.articles.append(article)
            
            logger.info(f"Статья успешно добавлена в список: {title}")
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении статьи в список: {str(e)}", exc_info=True)
            
    def clear_list(self):
        """Очищает список статей."""
        self.clear()
        self.articles = []
        
    def get_selected_article(self):
        """Возвращает выбранную статью.
        
        Returns:
            Объект статьи или None
        """
        try:
            current = self.currentItem()
            if current:
                return current.data(100)
            return None
        except Exception as e:
            print(f"Ошибка при получении выбранной статьи: {str(e)}")
            return None
            
    def _on_item_changed(self, current, previous):
        """Обработчик изменения выбранного элемента.
        
        Args:
            current: Текущий элемент
            previous: Предыдущий элемент
        """
        try:
            if current:
                article = current.data(100)
                if article:
                    self.article_selected.emit(article)
        except Exception as e:
            print(f"Ошибка при обработке выбора статьи: {str(e)}")
            
    def filter_articles(self, filter_text):
        """Фильтрует список статей по тексту.
        
        Args:
            filter_text: Текст для фильтрации
        """
        try:
            filter_text = filter_text.lower()
            
            for i in range(self.count()):
                item = self.item(i)
                article = item.data(100)
                
                if not article:
                    continue
                    
                # Получаем данные для поиска
                title = getattr(article, 'title', '').lower()
                authors = [a.lower() for a in getattr(article, 'authors', [])]
                abstract = getattr(article, 'abstract', '').lower()
                
                # Проверяем совпадение
                visible = (
                    filter_text in title or
                    any(filter_text in author for author in authors) or
                    filter_text in abstract
                )
                
                item.setHidden(not visible)
                
        except Exception as e:
            print(f"Ошибка при фильтрации статей: {str(e)}")

    def _show_context_menu(self, position):
        """Показывает контекстное меню.
        
        Args:
            position: Позиция курсора
        """
        try:
            # Получаем выбранную статью
            article = self.get_selected_article()
            if not article:
                return
                
            # Создаем меню
            menu = QMenu(self)
            
            # Добавляем пункты меню
            open_action = menu.addAction("Открыть в браузере")
            mindmap_action = menu.addAction("Создать интеллект-карту")
            references_action = menu.addAction("Найти источники")
            
            # Показываем меню
            action = menu.exec(QCursor.pos())
            
            # Обрабатываем выбор пункта меню
            if action == open_action:
                if hasattr(article, 'url') and article.url:
                    import webbrowser
                    webbrowser.open(article.url)
            elif action == mindmap_action:
                if hasattr(article, 'id'):
                    self.create_mindmap.emit(article.id)
            elif action == references_action:
                if hasattr(article, 'id'):
                    self.find_references.emit(article.id)
                    
        except Exception as e:
            print(f"Ошибка при показе контекстного меню: {str(e)}") 