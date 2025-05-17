"""Компонент для отображения деталей статьи."""

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt

class ArticleDetails(QTextEdit):
    """Виджет для отображения деталей статьи."""
    
    def __init__(self, parent=None):
        """Инициализирует виджет деталей статьи.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                color: #2C3E50;
                background: white;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
            }
            
            QTextEdit:focus {
                border: 1px solid #3498DB;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает внешний вид виджета."""
        pass
        
    def display_article(self, article):
        """Отображает информацию о статье.
        
        Args:
            article: Объект статьи
        """
        html = f"""
            <style>
                h1 {{ color: #2C3E50; font-size: 20px; margin-bottom: 16px; }}
                h2 {{ color: #34495E; font-size: 16px; margin-top: 16px; margin-bottom: 8px; }}
                p {{ color: #2C3E50; margin: 8px 0; line-height: 1.6; }}
                .authors {{ color: #2980B9; }}
                .date {{ color: #7F8C8D; }}
                .categories {{ color: #16A085; }}
                .abstract {{ color: #2C3E50; background: #ECF0F1; padding: 12px; border-radius: 4px; }}
                .doi {{ color: #2980B9; text-decoration: none; }}
            </style>
            <h1>{article.title}</h1>
            <p class="authors">Авторы: {', '.join(article.authors)}</p>
            <p class="date">Дата публикации: {article.published.strftime('%d.%m.%Y')}</p>
            <p class="categories">Категории: {', '.join(article.categories)}</p>
            <h2>Аннотация</h2>
            <p class="abstract">{article.abstract}</p>
        """
        
        if article.doi:
            html += f'<p>DOI: <a class="doi" href="https://doi.org/{article.doi}">{article.doi}</a></p>'
            
        if article.url:
            html += f'<p>URL: <a class="doi" href="{article.url}">{article.url}</a></p>'
            
        self.setHtml(html)
        
    def display_text(self, text, title=None):
        """Отображает текст с форматированием.
        
        Args:
            text: Текст для отображения
            title: Заголовок (опционально)
        """
        html = f"""
            <style>
                h1 {{ color: #2C3E50; font-size: 20px; margin-bottom: 16px; }}
                p {{ color: #2C3E50; margin: 8px 0; line-height: 1.6; }}
            </style>
        """
        
        if title:
            html += f"<h1>{title}</h1>"
            
        html += f"<p>{text}</p>"
        
        self.setHtml(html)
        
    def clear_details(self):
        """Очищает отображаемую информацию."""
        self.clear() 