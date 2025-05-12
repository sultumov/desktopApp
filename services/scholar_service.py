import os
from typing import List, Optional
import logging
from datetime import datetime
import arxiv

from models.article import Article, Author

class ScholarService:
    """Сервис для поиска и работы с научными статьями."""
    
    def __init__(self):
        """Инициализирует сервис для поиска научных статей."""
        self.search_results = []  # Кэш последних результатов поиска
        # Определяем источник данных
        self.default_source = "arxiv"
        
        # Настройки API
        self.sources = {
            "arxiv": {
                "name": "ArXiv",
                "description": "Поиск в ArXiv (препринты и научные статьи)",
                "method": self.search_arxiv
            }
        }
    
    def search_articles(self, query, limit=10, source=None):
        """
        Поиск статей по запросу в ArXiv.
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            source (str): Игнорируется, всегда используется ArXiv
            
        Returns:
            list: Список объектов Article
        """
        # Выполняем поиск через ArXiv
        articles = self.search_arxiv(query, limit)
            
        # Сохраняем результаты в кэше для последующего использования
        self._last_results = articles
        
        return articles
    
    def get_article_by_index(self, index: int) -> Optional[Article]:
        """
        Получает статью по индексу из кэшированных результатов.
        
        Args:
            index (int): Индекс статьи в кэше результатов
            
        Returns:
            Article: Объект статьи или None, если индекс вне диапазона
        """
        if not hasattr(self, '_last_results') or index < 0 or index >= len(self._last_results):
            return None
        
        return self._last_results[index]
    
    def get_available_sources(self) -> List[dict]:
        """
        Возвращает список доступных источников данных.
        
        Returns:
            Список источников в формате словарей {id, name, description}
        """
        sources = [
            {
                "id": "arxiv",
                "name": "ArXiv",
                "description": "Поиск в ArXiv (препринты и научные статьи)"
            }
        ]
            
        return sources 

    def search_arxiv(self, query, limit=10):
        """
        Поиск статей через ArXiv API.
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            
        Returns:
            list: Список объектов Article
        """
        try:
            # Создаем клиент ArXiv
            client = arxiv.Client()
            
            # Формируем поисковый запрос
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            articles = []
            
            # Получаем результаты
            for result in client.results(search):
                # Создаем список авторов
                authors = [Author(name=author.name) for author in result.authors]
                
                # Создаем объект статьи
                article = Article(
                    title=result.title,
                    authors=authors,
                    abstract=result.summary,
                    year=result.published.year if result.published else None,
                    journal="arXiv",  # ArXiv всегда будет источником
                    url=result.pdf_url,  # URL для PDF
                    citation_count=0,  # ArXiv API не предоставляет информацию о цитированиях
                    source="arxiv",
                    paper_id=result.entry_id,
                    doi=result.doi if hasattr(result, 'doi') else None
                )
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logging.error(f"Ошибка при поиске в ArXiv: {str(e)}")
            return [] 