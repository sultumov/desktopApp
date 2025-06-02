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
                       categories: Optional[List[str]] = None, load_full_text: bool = False) -> List[Article]:
        """Выполняет поиск статей по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество статей
            page: Номер страницы
            year_from: Начальный год
            year_to: Конечный год
            categories: Список категорий для фильтрации
            load_full_text: Загружать ли полный текст статей
            
        Returns:
            Список найденных статей
        """
        try:
            if not query or not query.strip():
                logger.warning("Пустой поисковый запрос")
                return []
                
            # Проверяем кэш при новом поиске
            cache_key = f"{query}_{limit}_{page}_{year_from}_{year_to}_{categories}"
            cached_results = self._get_from_cache(cache_key)
            if cached_results:
                logger.info("Возвращены результаты из кэша")
                self.search_results = cached_results
                self.has_more = len(cached_results) >= limit
                return self.search_results[:limit]

            self.current_page = page - 1
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
                        
                        # Если запрошена загрузка полного текста
                        if load_full_text:
                            try:
                                # Скачиваем PDF во временную директорию
                                article_id = article.id.split('/')[-1]
                                if article_id.endswith('v1'):
                                    article_id = article_id[:-2]
                                
                                storage_dir = os.path.join('storage', 'articles')
                                os.makedirs(storage_dir, exist_ok=True)
                                pdf_path = os.path.join(storage_dir, f"{article_id}.pdf")
                                
                                # Скачиваем только если файл еще не существует
                                if not os.path.exists(pdf_path):
                                    self.download_pdf(article, pdf_path)
                                
                                # Извлекаем текст
                                article.full_text = self.extract_text_from_pdf(pdf_path)
                                logger.info(f"Загружен полный текст для статьи: {article.title}")
                            except Exception as e:
                                logger.error(f"Ошибка при загрузке полного текста: {str(e)}")
                                article.full_text = None
                        
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
                self._add_to_cache(cache_key, new_results)

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
        """Получает текст статьи.
        
        Args:
            article: Объект статьи
            
        Returns:
            Текст статьи или сообщение об ошибке
        """
        try:
            logger.info(f"Получение текста статьи: {article.title}")
            
            # Проверяем наличие локального файла
            if not hasattr(article, 'local_pdf_path') or not article.local_pdf_path:
                return "PDF файл не найден"
            
            pdf_path = article.local_pdf_path
            
            # Проверяем существование и доступность файла
            if not os.path.exists(pdf_path):
                return "PDF файл не существует"
                
            if not os.access(pdf_path, os.R_OK):
                return "Нет доступа к PDF файлу"
            
            # Извлекаем текст
            text = self.extract_text_from_pdf(pdf_path)
            
            # Сохраняем текст в статье
            article.full_text = text
            
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при получении текста статьи: {str(e)}")
            return f"Ошибка при получении текста статьи: {str(e)}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Извлекает текст из PDF файла.
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Извлеченный текст
        """
        try:
            logger.info(f"Извлечение текста из PDF: {pdf_path}")
            
            text = ""
            
            # Пробуем с pdfplumber (лучше работает с форматированием)
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        try:
                            text_parts.append(page.extract_text())
                        except Exception as e:
                            logger.warning(f"Ошибка при извлечении текста из страницы: {str(e)}")
                            continue
                    
                    text = "\n".join(filter(None, text_parts))
                    
                    if text and len(text.strip()) > 100:
                        logger.info(f"Текст успешно извлечен с помощью pdfplumber: {len(text)} символов")
                        return self._clean_extracted_text(text)
            except Exception as e:
                logger.warning(f"Не удалось извлечь текст с помощью pdfplumber: {str(e)}")
            
            # Пробуем с PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                
                text_parts = []
                for page_num in range(len(reader.pages)):
                    try:
                        page = reader.pages[page_num]
                        text_parts.append(page.extract_text())
                    except Exception as e:
                        logger.warning(f"Ошибка при извлечении текста из страницы {page_num}: {str(e)}")
                        continue
                
                text = "\n".join(filter(None, text_parts))
                
                if text and len(text.strip()) > 100:
                    logger.info(f"Текст успешно извлечен с помощью PyPDF2: {len(text)} символов")
                    return self._clean_extracted_text(text)
            except Exception as e:
                logger.warning(f"Не удалось извлечь текст с помощью PyPDF2: {str(e)}")
            
            # Пробуем с pdfminer.six как последний вариант
            try:
                from pdfminer.high_level import extract_text as extract_text_pdfminer
                
                text = extract_text_pdfminer(pdf_path)
                
                if text and len(text.strip()) > 100:
                    logger.info(f"Текст успешно извлечен с помощью pdfminer.six: {len(text)} символов")
                    return self._clean_extracted_text(text)
            except Exception as e:
                logger.warning(f"Не удалось извлечь текст с помощью pdfminer.six: {str(e)}")
            
            if not text or len(text.strip()) < 100:
                logger.error("Не удалось извлечь текст из PDF любым методом")
            return "Не удалось извлечь текст из PDF. Возможно, PDF защищен или содержит только сканированные изображения."
            
            return self._clean_extracted_text(text)
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из PDF: {str(e)}")
            return "Ошибка при обработке PDF файла"

    def _clean_extracted_text(self, text: str) -> str:
        """Очищает и форматирует извлеченный текст.
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        try:
            # Удаляем множественные пробелы и переносы строк
            text = re.sub(r'\s+', ' ', text)
            
            # Восстанавливаем переносы строк после точек
            text = re.sub(r'(\. )', r'.\n', text)
            
            # Восстанавливаем параграфы
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            # Удаляем лишние пробелы в начале и конце строк
            text = '\n'.join(line.strip() for line in text.split('\n'))
            
            return text.strip()
        except Exception as e:
            logger.warning(f"Ошибка при очистке текста: {str(e)}")
            return text

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
            
            # Проверяем, есть ли уже полный текст в статье
            text = article.full_text if hasattr(article, 'full_text') else None
            
            # Если текста нет, пробуем получить его
            if not text:
                try:
                    text = self.get_article_text(article)
                except Exception as e:
                    logger.error(f"Не удалось получить текст статьи: {str(e)}")
                    return [
                        "Не удалось получить текст статьи.",
                        "Пожалуйста, загрузите PDF файл статьи вручную."
                    ]
            
            if not text or len(text.strip()) < 100:
                return [
                    "Текст статьи пустой или слишком короткий.",
                    "Пожалуйста, загрузите PDF файл статьи вручную."
                ]
            
            # Ищем все упоминания источников в тексте
            references = []
            
            # Паттерны для поиска источников
            patterns = [
                r'\[(\d+)\][\s\n]*([^[]+)',  # [1] Author et al.
                r'(?<!\d)(\d{4})[\s\n]*([A-Z][^.]+\.)(?=\s|$)',  # Year Author et al.
                r'([A-Z][a-z]+(?:\s+(?:et\.?\s+al\.?|and|&)\s+[A-Z][a-z]+)?)\s+\((\d{4})\)',  # Author (Year)
                r'References?:|Список литературы:|Библиография:|Bibliography:',  # Заголовки разделов с источниками
                r'\d+\.\s+[A-Z][^.]+\.',  # Нумерованные источники
            ]
            
            # Ищем секцию с источниками
            references_section = None
            for pattern in [r'References?:|Список литературы:|Библиография:|Bibliography:']:
                match = re.search(pattern, text)
                if match:
                    references_section = text[match.start():]
                    break
            
            # Если нашли секцию с источниками, используем её
            search_text = references_section if references_section else text
            
            for pattern in patterns:
                matches = re.finditer(pattern, search_text)
                for match in matches:
                    ref = match.group(0).strip()
                    if ref and ref not in references and len(ref) > 10:  # Проверяем минимальную длину
                        references.append(ref)
            
            # Фильтруем заголовки разделов из списка источников
            references = [ref for ref in references if not re.match(r'References?:|Список литературы:|Библиография:|Bibliography:', ref)]
            
            # Если не нашли источники, возвращаем заглушку
            if not references:
                return [
                    "Не удалось найти источники в тексте статьи.",
                    "Возможные причины:",
                    "1. Статья не содержит списка литературы",
                    "2. Формат источников не распознан",
                    "3. Ошибка при извлечении текста из PDF",
                    "Попробуйте загрузить PDF файл статьи вручную."
                ]
            
            return references

        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}")
            return [
                "Произошла ошибка при поиске источников.",
                f"Причина: {str(e)}",
                "Попробуйте загрузить PDF файл статьи вручную."
            ] 

    def get_local_articles(self) -> List[Article]:
        """Получает список статей из локального хранилища.
        
        Returns:
            Список статей с метаданными
        """
        try:
            storage_dir = os.path.join('storage', 'articles')
            if not os.path.exists(storage_dir):
                logger.warning("Директория storage/articles не существует")
                os.makedirs(storage_dir, exist_ok=True)
                return []
            
            articles = []
            for filename in os.listdir(storage_dir):
                if not filename.endswith('.pdf'):
                    continue
                
                try:
                    article_id = filename[:-4]  # Убираем .pdf
                    pdf_path = os.path.join(storage_dir, filename)
                    
                    # Проверяем существование и доступность файла
                    if not os.path.exists(pdf_path):
                        logger.warning(f"Файл не существует: {pdf_path}")
                        continue
                        
                    if not os.access(pdf_path, os.R_OK):
                        logger.warning(f"Нет доступа к файлу: {pdf_path}")
                        continue
                    
                    # Создаем базовую статью сначала
                    article = Article(
                        id=article_id,
                        title=f"PDF файл: {filename}",
                        authors=[],
                        abstract="",
                        year=None,
                        published=None,
                        summary="",
                        doi=None,
                        categories=[],
                        url=None
                    )
                    
                    # Добавляем путь к локальному файлу
                    article.local_pdf_path = pdf_path
                    
                    # Пробуем получить метаданные из arxiv
                    try:
                        search = arxiv.Search(id_list=[article_id])
                        result = next(self.client.results(search))
                        arxiv_article = self._convert_result_to_article(result)
                        
                        # Обновляем метаданные, сохраняя путь к файлу
                        article = arxiv_article
                        article.local_pdf_path = pdf_path
                        
                    except Exception as e:
                        logger.warning(f"Не удалось получить метаданные из arxiv для {filename}: {str(e)}")
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {filename}: {str(e)}")
                    continue
            
            return sorted(articles, key=lambda x: x.title)
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка локальных статей: {str(e)}")
            return []

    def get_article_summary(self, article: Article) -> str:
        """Генерирует краткое содержание статьи.
        
        Args:
            article: Статья для обработки
            
        Returns:
            Краткое содержание
        """
        try:
            if not article:
                return "Статья не найдена"
            
            # Проверяем наличие локального файла
            if not hasattr(article, 'local_pdf_path') or not article.local_pdf_path:
                return "PDF файл не найден"
            
            # Если нет полного текста, пробуем получить его
            if not hasattr(article, 'full_text') or not article.full_text:
                article.full_text = self.get_article_text(article)
            
            if not article.full_text or isinstance(article.full_text, str) and "ошибка" in article.full_text.lower():
                return "Не удалось получить текст статьи"
            
            # Формируем краткое содержание
            summary_parts = []
            
            # Добавляем метаданные
            if article.title:
                summary_parts.append(f"Название: {article.title}")
            if article.authors:
                summary_parts.append(f"Авторы: {', '.join(article.authors)}")
            if article.published:
                summary_parts.append(f"Дата публикации: {article.published.strftime('%d.%m.%Y')}")
            if article.categories:
                summary_parts.append(f"Категории: {', '.join(article.categories)}")
            
            # Добавляем аннотацию
            if article.abstract:
                summary_parts.append("\nАннотация:")
                summary_parts.append(article.abstract)
            
            # Разбиваем текст на секции и добавляем их
            try:
                sections = self._split_text_to_sections(article.full_text)
                if sections:
                    summary_parts.append("\nОсновные разделы:")
                    for section_name, section_text in sections.items():
                        sentences = re.split(r'(?<=[.!?])\s+', section_text)
                        summary = ' '.join(sentences[:3])
                        summary_parts.append(f"\n{section_name}:")
                        summary_parts.append(summary)
            except Exception as e:
                logger.warning(f"Ошибка при разбиении на секции: {str(e)}")
                # Добавляем первые несколько предложений текста
                sentences = re.split(r'(?<=[.!?])\s+', article.full_text)
                summary_parts.append("\nНачало текста:")
                summary_parts.append(' '.join(sentences[:5]))
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            logger.error(f"Ошибка при генерации краткого содержания: {str(e)}")
            return f"Ошибка при создании краткого содержания: {str(e)}"

    def _split_text_to_sections(self, text: str) -> Dict[str, str]:
        """Разбивает текст на секции.
        
        Args:
            text: Текст для разбиения
            
        Returns:
            Словарь с секциями
        """
        try:
            # Паттерны для поиска заголовков секций
            section_patterns = [
                r'^(?:I{1,3}|IV|V|VI{1,3}|IX|X)\.\s+([A-Z][^.]+)',  # I. INTRODUCTION
                r'^\d+\.\s+([A-Z][^.]+)',  # 1. INTRODUCTION
                r'^([A-Z][A-Z\s]{3,}(?:\s+AND\s+[A-Z\s]+)?)',  # INTRODUCTION AND METHODS
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Introduction
            ]
            
            sections = {}
            current_section = "Введение"
            current_text = []
            
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем, является ли строка заголовком секции
                is_header = False
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        # Сохраняем предыдущую секцию
                        if current_text:
                            sections[current_section] = ' '.join(current_text)
                        
                        # Начинаем новую секцию
                        current_section = match.group(1)
                        current_text = []
                        is_header = True
                        break
                
                if not is_header:
                    current_text.append(line)
            
            # Сохраняем последнюю секцию
            if current_text:
                sections[current_section] = ' '.join(current_text)
            
            return sections
            
        except Exception as e:
            logger.error(f"Ошибка при разбиении текста на секции: {str(e)}")
            return {"Текст": text} 

    def get_article_references(self, article: Article) -> List[Dict[str, str]]:
        """Извлекает список источников из статьи.
        
        Args:
            article: Статья для обработки
            
        Returns:
            Список источников с метаданными
        """
        try:
            # Если нет полного текста, пробуем получить его
            if not hasattr(article, 'full_text') or not article.full_text:
                if hasattr(article, 'local_pdf_path') and article.local_pdf_path:
                    article.full_text = self.extract_text_from_pdf(article.local_pdf_path)
                else:
                    return [{"error": "Текст статьи недоступен"}]
            
            if not article.full_text:
                return [{"error": "Не удалось извлечь текст из PDF"}]
            
            # Ищем секцию с источниками
            text = article.full_text
            references_section = None
            
            # Паттерны для поиска секции с источниками
            ref_section_patterns = [
                r'(?:References|Bibliography|Список литературы|Библиография)[\s\n]*:?[\s\n]*((?:[^\n]+\n?)+)',
                r'(?:\[\d+\]|\d+\.)[\s\n]+[A-Z][^\n]+(?:\n(?!\[\d+\]|\d+\.)[^\n]+)*',
            ]
            
            # Ищем секцию с источниками
            for pattern in ref_section_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                if matches:
                    if len(matches) > 1:  # Если нашли несколько совпадений, берем самое длинное
                        matches.sort(key=lambda x: len(x.group(0)), reverse=True)
                    references_section = matches[0].group(0)
                    break
            
            if not references_section:
                return [{"error": "Секция с источниками не найдена"}]
            
            # Разбиваем на отдельные источники
            references = []
            ref_patterns = [
                # [1] Author et al. Title. Journal, Year
                r'\[(\d+)\]\s+([^[]+?)(?=\[\d+\]|\Z)',
                # 1. Author et al. Title. Journal, Year
                r'(\d+)\.\s+([^.]+(?:\.[^.]+)*?)(?=\d+\.|$)',
                # Author et al. (Year) Title. Journal
                r'([A-Z][^()]+)\s*\((\d{4})\)[^.]+\.',
            ]
            
            found_refs = set()
            for pattern in ref_patterns:
                matches = re.finditer(pattern, references_section, re.MULTILINE)
                for match in matches:
                    ref_text = match.group(0).strip()
                    if ref_text and ref_text not in found_refs and len(ref_text) > 10:
                        # Пытаемся извлечь метаданные
                        ref_data = self._parse_reference(ref_text)
                        references.append(ref_data)
                        found_refs.add(ref_text)
            
            # Если не нашли источники стандартными паттернами,
            # просто разбиваем по строкам и фильтруем
            if not references:
                lines = references_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10 and line not in found_refs:
                        ref_data = self._parse_reference(line)
                        references.append(ref_data)
                        found_refs.add(line)
            
            return references if references else [{"error": "Источники не найдены"}]
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении источников: {str(e)}")
            return [{"error": f"Ошибка при извлечении источников: {str(e)}"}]

    def _parse_reference(self, ref_text: str) -> Dict[str, str]:
        """Парсит текст источника и извлекает метаданные.
        
        Args:
            ref_text: Текст источника
            
        Returns:
            Словарь с метаданными
        """
        try:
            ref_data = {
                "text": ref_text,
                "authors": [],
                "year": None,
                "title": None,
                "journal": None,
            }
            
            # Извлекаем год
            year_match = re.search(r'\(?(\d{4})\)?', ref_text)
            if year_match:
                ref_data["year"] = year_match.group(1)
            
            # Извлекаем авторов (ищем в начале до года или точки)
            author_part = ref_text.split('(')[0] if '(' in ref_text else ref_text.split('.')[0]
            authors = re.findall(r'[A-Z][a-z]+(?:,?\s+(?:and|&)?\s*[A-Z][a-z]+)*', author_part)
            if authors:
                ref_data["authors"] = [a.strip() for a in authors]
            
            # Извлекаем название (текст между первой и второй точкой после авторов)
            parts = ref_text.split('.')
            if len(parts) > 1:
                ref_data["title"] = parts[1].strip()
            
            # Извлекаем журнал (текст после названия)
            if len(parts) > 2:
                ref_data["journal"] = parts[2].strip()
            
            return ref_data
            
        except Exception as e:
            logger.warning(f"Ошибка при парсинге источника: {str(e)}")
            return {"text": ref_text} 