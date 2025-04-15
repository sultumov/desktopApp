import os
from typing import List, Optional
import requests
import requests_cache
from scholarly import scholarly
from bs4 import BeautifulSoup
import PyPDF2
import io
import time
import logging

from models.article import Article, Author

# Устанавливаем кэш для API запросов, чтобы уменьшить нагрузку и ускорить работу
requests_cache.install_cache('scholar_cache', expire_after=86400)  # кэш на 24 часа

class ScholarService:
    """Сервис для поиска и работы с научными статьями."""
    
    def __init__(self):
        """Инициализирует сервис для поиска научных статей."""
        self.search_results = []  # Кэш последних результатов поиска
        # Определяем источник данных из env или используем Google Scholar по умолчанию
        self.default_source = os.getenv("SCHOLAR_SOURCE", "google_scholar")
        # API ключ для Semantic Scholar (не обязательный для базового использования)
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        
        # Настройки API
        self.sources = {
            "google_scholar": {
                "name": "Google Scholar",
                "description": "Поиск в Google Scholar",
                "method": self.search_google_scholar
            },
            "semantic_scholar": {
                "name": "Semantic Scholar",
                "description": "Поиск в Semantic Scholar (включая цитирования)",
                "method": self.search_semantic_scholar
            }
        }
    
    def search_articles(self, query, limit=10, source=None):
        """
        Поиск статей по запросу в выбранном источнике.
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            source (str): Источник данных ('google_scholar' или 'semantic_scholar')
            
        Returns:
            list: Список объектов Article
        """
        # Если источник не указан, используем источник по умолчанию
        if not source:
            source = os.getenv("SCHOLAR_SOURCE", "google_scholar")
        
        # Поиск в зависимости от выбранного источника
        if source == "semantic_scholar":
            articles = self.search_semantic_scholar(query, limit)
        else:
            articles = self.search_google_scholar(query, limit)
            
        # Сохраняем результаты в кэше для последующего использования
        self._last_results = articles
        
        return articles
    
    def search_google_scholar(self, query, limit=10):
        """
        Поиск статей через Google Scholar.
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            
        Returns:
            list: Список объектов Article
        """
        try:
            search_query = scholarly.search_pubs(query)
            results = []
            
            # Получаем запрошенное количество результатов
            for _ in range(limit):
                try:
                    pub = next(search_query)
                    
                    # Создаем объект статьи
                    article = Article(
                        title=pub.get("bib", {}).get("title", ""),
                        authors=[author for author in pub.get("bib", {}).get("author", [])],
                        venue=pub.get("bib", {}).get("venue", ""),
                        year=pub.get("bib", {}).get("pub_year"),
                        abstract=pub.get("bib", {}).get("abstract", ""),
                        url=pub.get("pub_url"),
                        citation_count=pub.get("num_citations", 0),
                        source="google_scholar"
                    )
                    
                    results.append(article)
                    
                except StopIteration:
                    break
                    
            return results
            
        except Exception as e:
            logging.error(f"Ошибка при поиске в Google Scholar: {str(e)}")
            return []
    
    def search_semantic_scholar(self, query, limit=10):
        """
        Поиск статей через API Semantic Scholar.
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            
        Returns:
            list: Список объектов Article
        """
        try:
            # Базовый URL API Semantic Scholar
            base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            
            # Параметры запроса
            params = {
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,venue,abstract,url,citationCount,influentialCitationCount,externalIds,paperId,referenceCount"
            }
            
            # Добавляем API ключ, если он доступен
            headers = {}
            api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
            if api_key:
                headers["x-api-key"] = api_key
            
            # Выполняем запрос
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            
            # Обрабатываем результаты
            results = response.json().get("data", [])
            articles = []
            
            for result in results:
                # Извлекаем авторов
                authors = []
                for author in result.get("authors", []):
                    authors.append(Author(name=author.get("name", "")))
                
                # Если нет авторов, добавляем Unknown
                if not authors:
                    authors.append(Author(name="Unknown"))
                
                # Создаем объект статьи
                article = Article(
                    title=result.get("title", ""),
                    authors=authors,
                    abstract=result.get("abstract", ""),
                    year=result.get("year", 0),
                    journal=result.get("venue", ""),
                    url=result.get("url", ""),
                    citation_count=result.get("citationCount", 0),
                    reference_count=result.get("referenceCount", 0),
                    paper_id=result.get("paperId", ""),
                    source="semantic_scholar",
                    doi=result.get("externalIds", {}).get("DOI", "")
                )
                
                articles.append(article)
            
            return articles
        
        except Exception as e:
            logging.error(f"Ошибка при поиске в Semantic Scholar: {str(e)}")
            return []
    
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
    
    def get_article_text(self, article: Article) -> str:
        """
        Получает полный текст статьи, если он доступен.
        
        Args:
            article: Объект статьи
            
        Returns:
            Строка с полным текстом статьи или сообщение об ошибке
        """
        # Если полный текст уже загружен
        if article.full_text:
            return article.full_text
        
        # Если статья имеет локальный файл
        if article.file_path and os.path.exists(article.file_path):
            return self._extract_text_from_file(article.file_path)
        
        # Если есть URL, пытаемся загрузить текст
        if article.url:
            try:
                response = requests.get(article.url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # PDF-файл
                    if 'application/pdf' in content_type:
                        return self._extract_text_from_pdf(io.BytesIO(response.content))
                    
                    # HTML-страница
                    elif 'text/html' in content_type:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Пытаемся найти основной текст статьи
                        # Это может зависеть от структуры сайта
                        article_text = ''
                        
                        # Типичные контейнеры для текста статей
                        containers = soup.select('.article-content, .paper-content, .full-text, article, .content')
                        if containers:
                            article_text = containers[0].get_text(separator='\n')
                        else:
                            # Если не нашли контейнер, берем весь текст
                            article_text = soup.get_text(separator='\n')
                        
                        # Сохраняем текст в статье для кэширования
                        article.full_text = article_text
                        return article_text
            except Exception as e:
                return f"Не удалось загрузить текст статьи: {str(e)}"
        
        # Для статей из Semantic Scholar пытаемся получить полный текст через их API
        if hasattr(article, 'paper_id') and article.paper_id and article.source == "Semantic Scholar":
            try:
                # Добавляем задержку, чтобы избежать ограничения API
                time.sleep(1)
                
                # URL для получения полного текста
                url = f"https://api.semanticscholar.org/graph/v1/paper/{article.paper_id}?fields=tldr,abstract,references.abstract"
                
                # Заголовки запроса
                headers = {}
                if self.semantic_scholar_api_key:
                    headers["x-api-key"] = self.semantic_scholar_api_key
                
                # Выполняем запрос
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Собираем текст из разных источников
                    text_parts = []
                    
                    # Добавляем название и абстракт
                    text_parts.append(f"# {article.title}\n\n")
                    
                    # Используем TLDR (краткое изложение), если доступно
                    tldr = data.get("tldr")
                    if tldr and tldr.get("text"):
                        text_parts.append(f"## Краткое содержание (TLDR)\n{tldr.get('text')}\n\n")
                    
                    # Добавляем абстракт
                    if data.get("abstract"):
                        text_parts.append(f"## Abstract\n{data.get('abstract')}\n\n")
                    
                    # Добавляем информацию о ссылках
                    references = data.get("references", [])
                    if references:
                        text_parts.append(f"## References ({len(references)})\n\n")
                        for i, ref in enumerate(references[:20]):  # Ограничиваем количеством
                            ref_title = ref.get("title", "Unknown")
                            ref_abstract = ref.get("abstract", "")
                            text_parts.append(f"### [{i+1}] {ref_title}\n{ref_abstract}\n\n")
                    
                    # Объединяем все части
                    full_text = "\n".join(text_parts)
                    
                    # Сохраняем полный текст в статье
                    article.full_text = full_text
                    return full_text
            except Exception as e:
                return f"Ошибка при получении данных из Semantic Scholar API: {str(e)}"
        
        return "Текст статьи недоступен"
    
    def get_references(self, article: Article) -> List[Article]:
        """
        Получает список источников для статьи, если доступен.
        
        Args:
            article: Объект статьи
            
        Returns:
            Список объектов Article с источниками
        """
        # Для статей из Semantic Scholar можем получить источники через API
        if hasattr(article, 'paper_id') and article.paper_id and article.source == "Semantic Scholar":
            try:
                # URL для получения ссылок
                url = f"https://api.semanticscholar.org/graph/v1/paper/{article.paper_id}/references?fields=title,authors,year,abstract,venue"
                
                # Заголовки запроса
                headers = {}
                if self.semantic_scholar_api_key:
                    headers["x-api-key"] = self.semantic_scholar_api_key
                
                # Выполняем запрос
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    references = []
                    
                    for ref_data in data.get("data", []):
                        cited_paper = ref_data.get("citedPaper", {})
                        
                        # Извлекаем авторов
                        authors = []
                        for author in cited_paper.get("authors", []):
                            name = author.get("name", "")
                            if name:
                                authors.append(Author(name=name))
                        
                        # Если нет авторов, добавляем Unknown
                        if not authors:
                            authors.append(Author(name="Unknown"))
                        
                        # Создаем объект Article
                        reference = Article(
                            title=cited_paper.get("title", "Unknown Title"),
                            authors=authors,
                            abstract=cited_paper.get("abstract", ""),
                            year=cited_paper.get("year", 0),
                            journal=cited_paper.get("venue"),
                            source="Semantic Scholar",
                            confidence=1.0  # Максимальная уверенность, так как это прямая ссылка
                        )
                        
                        references.append(reference)
                    
                    return references
            except Exception as e:
                print(f"Ошибка при получении источников: {str(e)}")
        
        # Если не удалось получить ссылки через API, возвращаем пустой список
        return []
    
    def _extract_text_from_pdf(self, pdf_data) -> str:
        """
        Извлекает текст из PDF-файла.
        
        Args:
            pdf_data: Поток данных PDF-файла
            
        Returns:
            Строка с извлеченным текстом
        """
        try:
            reader = PyPDF2.PdfReader(pdf_data)
            text = ""
            
            # Извлекаем текст из всех страниц
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            return f"Ошибка при извлечении текста из PDF: {str(e)}"
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Извлекает текст из файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Строка с извлеченным текстом
        """
        try:
            # PDF-файл
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    return self._extract_text_from_pdf(f)
            
            # Текстовый файл
            elif file_path.lower().endswith(('.txt', '.md')):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # Неподдерживаемый формат
            else:
                return f"Неподдерживаемый формат файла: {file_path}"
                
        except Exception as e:
            return f"Ошибка при извлечении текста из файла: {str(e)}"
    
    def get_available_sources(self) -> List[dict]:
        """
        Возвращает список доступных источников данных.
        
        Returns:
            Список источников в формате словарей {id, name, description}
        """
        sources = [
            {
                "id": "google_scholar",
                "name": "Google Scholar"
            },
        ]
        
        # Проверяем, доступен ли Semantic Scholar API
        if os.getenv("SEMANTIC_SCHOLAR_API_KEY") or True:  # True для возможности использования без ключа
            sources.append({
                "id": "semantic_scholar",
                "name": "Semantic Scholar"
            })
            
        return sources 

    def get_citations(self, article: Article) -> List[Article]:
        """
        Получает список цитирований для статьи, если доступен.
        
        Args:
            article: Объект статьи
            
        Returns:
            Список объектов Article с цитированиями
        """
        # Работает только с Semantic Scholar
        if hasattr(article, 'paper_id') and article.paper_id and article.source == "semantic_scholar":
            try:
                # URL для получения цитирований
                url = f"https://api.semanticscholar.org/graph/v1/paper/{article.paper_id}/citations?fields=title,authors,year,abstract,venue,citationCount"
                
                # Заголовки запроса
                headers = {}
                if self.semantic_scholar_api_key:
                    headers["x-api-key"] = self.semantic_scholar_api_key
                
                # Выполняем запрос
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    citations = []
                    
                    for citation_data in data.get("data", []):
                        citing_paper = citation_data.get("citingPaper", {})
                        
                        # Извлекаем авторов
                        authors = []
                        for author in citing_paper.get("authors", []):
                            name = author.get("name", "")
                            if name:
                                authors.append(Author(name=name))
                        
                        # Если нет авторов, добавляем Unknown
                        if not authors:
                            authors.append(Author(name="Unknown"))
                        
                        # Создаем объект Article
                        citation = Article(
                            title=citing_paper.get("title", "Unknown Title"),
                            authors=authors,
                            abstract=citing_paper.get("abstract", ""),
                            year=citing_paper.get("year", 0),
                            journal=citing_paper.get("venue"),
                            citation_count=citing_paper.get("citationCount", 0),
                            source="semantic_scholar",
                            paper_id=citing_paper.get("paperId")
                        )
                        
                        citations.append(citation)
                    
                    return citations
            except Exception as e:
                logging.error(f"Ошибка при получении цитирований: {str(e)}")
        
        # Если не удалось получить цитирования через API, возвращаем пустой список
        return [] 