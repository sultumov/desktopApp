"""Компонент списка статей."""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

class ArticleList(QListWidget):
    """Компонент для отображения списка статей."""
    
    article_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        """Инициализирует список статей.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setup_ui()
        self.itemClicked.connect(self._on_item_clicked)
        
    def setup_ui(self):
        """Настраивает внешний вид списка."""
        self.setStyleSheet("""
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
        
    def add_article(self, article, display_text=None):
        """Добавляет статью в список.
        
        Args:
            article: Объект статьи
            display_text: Текст для отображения (если None, используется заголовок статьи)
        """
        if display_text is None:
            display_text = f"{article.title}\nАвторы: {', '.join(article.authors)}"
            
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, article)
        self.addItem(item)
        
    def clear_list(self):
        """Очищает список статей."""
        self.clear()
        
    def get_selected_article(self):
        """Возвращает выбранную статью.
        
        Returns:
            Объект статьи или None, если ничего не выбрано
        """
        item = self.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
        
    def _on_item_clicked(self, item):
        """Обрабатывает клик на элементе списка."""
        article = item.data(Qt.ItemDataRole.UserRole)
        self.article_selected.emit(article) 