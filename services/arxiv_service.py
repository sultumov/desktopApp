"""
Сервис для работы с ArXiv API.
"""

import logging
import arxiv
from datetime import datetime
from typing import List, Optional
from models.article import Article

logger = logging.getLogger(__name__)

class ArxivService:
    """Сервис для работы с ArXiv API."""

    def __init__(self):
        """Инициализирует сервис."""
        self.client = arxiv.Client()
        self.search_results = []

    def search_articles(self, query: str) -> List[Article]:
        """Выполняет поиск статей по запросу."""
        try:
            logger.info(f"Поиск статей по запросу: {query}")
            search = arxiv.Search(
                query=query,
                max_results=10,
                sort_by=arxiv.SortCriterion.Relevance
            )

            self.search_results = []
            for result in self.client.results(search):
                article = Article(
                    id=result.entry_id,
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    year=result.published.year,
                    published=result.published,
                    summary=result.summary,
                    doi=result.doi,
                    categories=[cat for cat in result.categories],
                    url=result.pdf_url
                )
                self.search_results.append(article)

            logger.info(f"Найдено статей: {len(self.search_results)}")
            return self.search_results

        except Exception as e:
            logger.error(f"Ошибка при поиске статей: {str(e)}")
            raise

    def get_article_by_index(self, index: int) -> Optional[Article]:
        """Возвращает статью по индексу из результатов поиска."""
        try:
            if 0 <= index < len(self.search_results):
                return self.search_results[index]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении статьи по индексу: {str(e)}")
            raise

    def get_article_text(self, article: Article) -> str:
        """Получает текст статьи."""
        try:
            # TODO: Реализовать загрузку и извлечение текста из PDF
            return "Текст статьи временно недоступен"
        except Exception as e:
            logger.error(f"Ошибка при получении текста статьи: {str(e)}")
            raise 