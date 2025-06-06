"""
Сервис для работы с ArXiv API.
"""

import logging
import arxiv
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models.article import Article
import os
from functools import lru_cache
import re

logger = logging.getLogger(__name__)

class ArxivService:
    """Сервис для работы с ArXiv API."""

    def __init__(self):
        """Инициализирует сервис."""
        self.client = arxiv.Client()
        self.search_results = []
        self.page_size = 10  # Размер страницы по умолчанию
        self.current_page = 0
        self.current_query = ""
        self.has_more = True
        self._cache = {}  # Кэш для результатов поиска
        self._cache_timeout = timedelta(minutes=5)  # Время жизни кэша

    def _get_from_cache(self, query: str) -> Optional[List[Article]]:
        """Получает результаты из кэша."""
        if query in self._cache:
            timestamp, results = self._cache[query]
            if datetime.now() - timestamp < self._cache_timeout:
                return results
            else:
                del self._cache[query]
        return None

    def _add_to_cache(self, query: str, results: List[Article]):
        """Добавляет результаты в кэш."""
        self._cache[query] = (datetime.now(), results)

    def _convert_result_to_article(self, result) -> Article:
        """Конвертирует результат arxiv в объект Article."""
        return Article(
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

    def search_articles(self, query: str, limit: int = 10, page: int = 1,
                       year_from: Optional[int] = None, year_to: Optional[int] = None,
                       categories: Optional[List[str]] = None) -> List[Article]:
        """Выполняет поиск статей по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество статей
            page: Номер страницы
            year_from: Начальный год
            year_to: Конечный год
            categories: Список категорий для фильтрации
            
        Returns:
            Список найденных статей
        """
        try:
            if not query or not query.strip():
                logger.warning("Пустой поисковый запрос")
                return []
                
            # Проверяем кэш при новом поиске
            cached_results = self._get_from_cache(query)
            if cached_results:
                logger.info("Возвращены результаты из кэша")
                self.search_results = cached_results
                self.has_more = len(cached_results) >= limit
                return self.search_results[:limit]

            self.current_page = page - 1  # Страницы в arxiv начинаются с 0
            self.current_query = query
            self.search_results = []
            self.has_more = True
            self.page_size = limit
            
            logger.info(f"Поиск статей (страница {self.current_page}): {query}")
            
            # Модифицируем запрос с учетом года
            modified_query = query
            if year_from or year_to:
                date_range = []
                if year_from:
                    date_range.append(f"submittedDate:[{year_from} TO")
                if year_to:
                    date_range.append(f"{year_to}]")
                elif year_from:
                    date_range.append("*]")
                if date_range:
                    modified_query = f"{query} AND {' '.join(date_range)}"
            
            # Добавляем фильтрацию по категориям
            if categories:
                category_filter = " OR ".join([f"cat:{cat}" for cat in categories])
                modified_query = f"{modified_query} AND ({category_filter})"
            
            try:
                # Создаем объект поиска
                search = arxiv.Search(
                    query=modified_query,
                    max_results=limit,
                    sort_by=arxiv.SortCriterion.Relevance
                )

                # Получаем результаты
                new_results = []
                for result in self.client.results(search):
                    try:
                        article = self._convert_result_to_article(result)
                        new_results.append(article)
                        if len(new_results) >= limit:
                            break
                    except Exception as e:
                        logger.error(f"Ошибка при обработке результата: {str(e)}")
                        continue
                        
            except StopIteration:
                self.has_more = False
                logger.info("Достигнут конец результатов")
            except Exception as e:
                logger.error(f"Ошибка при выполнении поискового запроса: {str(e)}")
                raise

            # Если получили меньше результатов, чем размер страницы
            if len(new_results) < limit:
                self.has_more = False

            self.search_results = new_results
            # Сохраняем в кэш только если есть результаты
            if new_results:
                self._add_to_cache(query, new_results)

            self.current_page += 1
            
            logger.info(f"Получено статей: {len(new_results)}")
            return new_results

        except Exception as e:
            logger.error(f"Ошибка при поиске статей: {str(e)}")
            raise

    def load_more(self) -> List[Article]:
        """Загружает следующую страницу результатов."""
        if not self.has_more:
            return []
        return self.search_articles(
            query=self.current_query,
            limit=self.page_size,
            page=self.current_page + 1
        )

    def has_more_results(self) -> bool:
        """Проверяет, есть ли еще результаты для загрузки."""
        return self.has_more

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
            logger.info(f"Получение текста статьи: {article.title}")
            
            # Проверяем, существует ли уже скачанный PDF
            article_id = article.id.split('/')[-1]
            if article_id.endswith('v1'):
                article_id = article_id[:-2]  # Убираем 'v1' из конца
                
            # Путь к возможному PDF файлу
            safe_filename = f"{article_id}.pdf"
            storage_dir = os.path.join('storage', 'articles')
            pdf_path = os.path.join(storage_dir, safe_filename)
            
            # Если файл не существует, скачиваем его
            if not os.path.exists(pdf_path):
                logger.info(f"PDF файл не найден, скачиваем: {pdf_path}")
                os.makedirs(storage_dir, exist_ok=True)
                
                try:
                    # Создаем объект Result для скачивания
                    paper = next(self.client.results(arxiv.Search(id_list=[article_id])))
                    paper.download_pdf(filename=pdf_path)
                    logger.info(f"PDF успешно скачан: {pdf_path}")
                except Exception as e:
                    logger.error(f"Ошибка при скачивании PDF: {str(e)}")
                    return "Не удалось скачать PDF статьи"
            
            # Извлекаем текст из PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Обновляем статью с полным текстом
            article.full_text = text
            
            return text
        except Exception as e:
            logger.error(f"Ошибка при получении текста статьи: {str(e)}")
            return "Ошибка при извлечении текста из PDF"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Извлекает текст из PDF файла.
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Извлеченный текст
        """
        try:
            logger.info(f"Извлечение текста из PDF: {pdf_path}")
            
            # Пробуем с PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                
                text_parts = []
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text_parts.append(page.extract_text())
                
                text = "\n".join(text_parts)
                
                # Если удалось получить текст, возвращаем его
                if text and len(text.strip()) > 100:  # Проверяем, что текст не пустой
                    logger.info(f"Текст успешно извлечен с помощью PyPDF2: {len(text)} символов")
                    return text
            except Exception as e:
                logger.warning(f"Не удалось извлечь текст с помощью PyPDF2: {str(e)}")
            
            # Если PyPDF2 не сработал, пробуем pdfminer.six
            try:
                from pdfminer.high_level import extract_text as extract_text_pdfminer
                
                text = extract_text_pdfminer(pdf_path)
                
                # Если удалось получить текст, возвращаем его
                if text and len(text.strip()) > 100:
                    logger.info(f"Текст успешно извлечен с помощью pdfminer.six: {len(text)} символов")
                    return text
            except Exception as e:
                logger.warning(f"Не удалось извлечь текст с помощью pdfminer.six: {str(e)}")
            
            # Если обе попытки не удались, возвращаем сообщение об ошибке
            logger.error("Не удалось извлечь текст из PDF любым методом")
            return "Не удалось извлечь текст из PDF. Возможно, PDF защищен или содержит только сканированные изображения."
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из PDF: {str(e)}")
            return "Ошибка при обработке PDF файла"

    def download_pdf(self, article: Article, file_path: str) -> None:
        """Скачивает PDF версию статьи.
        
        Args:
            article: Статья для скачивания
            file_path: Путь для сохранения PDF файла
        """
        try:
            logger.info(f"Скачивание PDF для статьи: {article.title}")
            
            # Получаем ID статьи из entry_id (например, из http://arxiv.org/abs/1234.5678 получаем 1234.5678)
            article_id = article.id.split('/')[-1]
            if article_id.endswith('v1'):
                article_id = article_id[:-2]  # Убираем 'v1' из конца

            # Создаем безопасное имя файла
            safe_filename = f"{article_id}.pdf"
            
            # Создаем путь к файлу в директории storage/articles
            storage_dir = os.path.join('storage', 'articles')
            os.makedirs(storage_dir, exist_ok=True)
            
            full_path = os.path.join(storage_dir, safe_filename)
                
            # Создаем объект Result для скачивания
            paper = next(self.client.results(arxiv.Search(id_list=[article_id])))
            paper.download_pdf(filename=full_path)
            
            logger.info(f"PDF успешно скачан: {full_path}")

        except Exception as e:
            logger.error(f"Ошибка при скачивании PDF: {str(e)}")
            raise 

    def find_references(self, article: Article) -> List[str]:
        """Ищет источники для статьи.
        
        Args:
            article: Объект статьи
            
        Returns:
            Список найденных источников
        """
        try:
            logger.info(f"Поиск источников для статьи: {article.title}")
            
            # Получаем текст статьи
            text = self.get_article_text(article)
            
            # Ищем все упоминания источников в тексте
            references = []
            
            # Паттерны для поиска источников
            patterns = [
                r'\[(\d+)\][\s\n]*([^[]+)',  # [1] Author et al.
                r'(?<!\d)(\d{4})[\s\n]*([A-Z][^.]+\.)(?=\s|$)',  # Year Author et al.
                r'([A-Z][a-z]+(?:\s+(?:et\.?\s+al\.?|and|&)\s+[A-Z][a-z]+)?)\s+\((\d{4})\)',  # Author (Year)
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    ref = match.group(0).strip()
                    if ref and ref not in references:
                        references.append(ref)
            
            # Если не нашли источники, возвращаем заглушку
            if not references:
                return [
                    "Не удалось найти источники в тексте статьи.",
                    "Возможные причины:",
                    "1. Статья не содержит списка литературы",
                    "2. Формат источников не распознан",
                    "3. Ошибка при извлечении текста из PDF"
                ]
            
            return references

        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}")
            return [
                "Произошла ошибка при поиске источников.",
                f"Причина: {str(e)}",
                "Попробуйте скачать PDF статьи и проверить источники вручную."
            ] 