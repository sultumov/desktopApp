"""Компонент для отображения деталей статьи."""

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt

class ArticleDetails(QTextEdit):
    """Компонент для отображения подробной информации о статье."""
    
    def __init__(self, parent=None):
        """Инициализирует виджет деталей статьи.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает внешний вид виджета."""
        self.setReadOnly(True)
        self.setStyleSheet("""
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
        
    def display_article(self, article):
        """Отображает информацию о статье.
        
        Args:
            article: Объект статьи для отображения
        """
        if not article:
            self.clear()
            return
            
        # Формируем HTML для отображения информации о статье
        html = f"""
        <h2>{article.title}</h2>
        <p><b>Авторы:</b> {", ".join(article.authors)}</p>
        <p><b>Дата публикации:</b> {article.published.strftime("%d.%m.%Y")}</p>
        <p><b>Категории:</b> {", ".join(article.categories)}</p>
        <p><b>DOI:</b> {article.doi or "Нет данных"}</p>
        <p><b>Ссылка:</b> <a href="{article.url}">{article.url}</a></p>
        <h3>Аннотация</h3>
        <p>{article.summary}</p>
        """
        
        self.setHtml(html)
        
    def display_text(self, text, title=None):
        """Отображает произвольный текст.
        
        Args:
            text: Текст для отображения
            title: Заголовок текста (если есть)
        """
        html = ""
        if title:
            html += f"<h2>{title}</h2>"
            
        html += f"<p>{text}</p>"
        self.setHtml(html)
        
    def clear_details(self):
        """Очищает содержимое виджета."""
        self.clear() 