"""
Сервис для работы с локальным хранилищем статей.
"""

import os
import json
import logging
from typing import List, Optional
from models.article import Article

logger = logging.getLogger(__name__)

class StorageService:
    """Сервис для работы с локальным хранилищем статей."""
    
    def __init__(self):
        """Инициализирует сервис."""
        self.storage_dir = "storage"
        self.articles_file = os.path.join(self.storage_dir, "articles.json")
        os.makedirs(self.storage_dir, exist_ok=True)
        self._load_articles()

    def _load_articles(self):
        """Загружает статьи из файла."""
        try:
            if os.path.exists(self.articles_file):
                with open(self.articles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.articles = [Article(**article) for article in data]
            else:
                self.articles = []
        except Exception as e:
            logger.error(f"Ошибка при загрузке статей: {str(e)}")
            self.articles = []

    def _save_articles(self):
        """Сохраняет статьи в файл."""
        try:
            with open(self.articles_file, 'w', encoding='utf-8') as f:
                data = [article.__dict__ for article in self.articles]
                json.dump(data, f, ensure_ascii=False, indent=4, default=str)
        except Exception as e:
            logger.error(f"Ошибка при сохранении статей: {str(e)}")
            raise

    def get_articles(self) -> List[Article]:
        """Возвращает список всех статей."""
        return self.articles

    def get_article(self, article_id: str) -> Optional[Article]:
        """Возвращает статью по ID."""
        try:
            for article in self.articles:
                if article.id == article_id:
                    return article
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении статьи: {str(e)}")
            raise

    def add_article(self, article: Article):
        """Добавляет статью в хранилище."""
        try:
            if not self.get_article(article.id):
                self.articles.append(article)
                self._save_articles()
        except Exception as e:
            logger.error(f"Ошибка при добавлении статьи: {str(e)}")
            raise

    def delete_article(self, article_id: str):
        """Удаляет статью из хранилища."""
        try:
            self.articles = [a for a in self.articles if a.id != article_id]
            self._save_articles()
        except Exception as e:
            logger.error(f"Ошибка при удалении статьи: {str(e)}")
            raise

    def update_article(self, article: Article):
        """Обновляет статью в хранилище."""
        try:
            for i, a in enumerate(self.articles):
                if a.id == article.id:
                    self.articles[i] = article
                    self._save_articles()
                    return
        except Exception as e:
            logger.error(f"Ошибка при обновлении статьи: {str(e)}")
            raise 