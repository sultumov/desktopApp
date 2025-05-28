"""Сервис для работы с КиберЛенинкой."""

import requests
from datetime import datetime
from models.article import Article
import logging
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
import os
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import random
from requests.exceptions import RequestException
from urllib3.exceptions import HTTPError
from socket import timeout

# Настройка логгера
logger = logging.getLogger(__name__)

class CyberleninkaService:
    """Сервис для работы с КиберЛенинкой."""
    
    BASE_URL = "https://cyberleninka.ru"
    CACHE_DIR = "cache/cyberleninka"
    CACHE_TIME = 24 * 60 * 60  # 24 часа в секундах
    MAX_RETRIES = 3  # Максимальное количество попыток
    RETRY_DELAY = 2  # Базовая задержка между попытками (в секундах)
    
    # Список User-Agent для ротации
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    def __init__(self):
        """Инициализация сервиса."""
        try:
            logger.info("Инициализация CyberleninkaService")
            self.session = requests.Session()
            self._update_headers()
            
            # Создаем директорию для кэша
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            
            # Проверяем доступность сервиса при инициализации
            if not self.check_availability():
                logger.warning("Сервис КиберЛенинки недоступен")
                
        except Exception as e:
            logger.error(f"Ошибка при инициализации сервиса: {str(e)}", exc_info=True)
            # Не выбрасываем исключение, чтобы сервис мог продолжить работу
        
    def _update_headers(self):
        """Обновление заголовков запроса с новым User-Agent."""
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://cyberleninka.ru/'
        }
        self.session.headers.update(headers)
        logger.debug(f"Обновлены заголовки запросов с User-Agent: {headers['User-Agent']}")
        
    def _make_request(self, url: str, method: str = 'get', **kwargs) -> requests.Response:
        """Выполнение HTTP запроса с обработкой ошибок и повторными попытками.
        
        Args:
            url: URL для запроса
            method: HTTP метод (get/post)
            **kwargs: Дополнительные параметры для requests
            
        Returns:
            Response объект
            
        Raises:
            RequestException: При ошибке запроса после всех попыток
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Увеличиваем задержку с каждой попыткой
                delay = self.RETRY_DELAY * (attempt + 1)
                time.sleep(random.uniform(delay, delay + 1))
                
                # Обновляем User-Agent перед запросом
                self._update_headers()
                
                # Выполняем запрос
                response = getattr(self.session, method)(url, timeout=10, **kwargs)
                response.raise_for_status()
                
                # Проверяем наличие капчи
                if 'captcha' in response.text.lower():
                    logger.warning(f"Обнаружена капча (попытка {attempt + 1}/{self.MAX_RETRIES})")
                    raise RequestException("Требуется ввод капчи")
                    
                # Проверяем, что получили HTML-ответ
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type and len(response.text.strip()) < 100:
                    logger.warning(f"Получен пустой или слишком короткий ответ (попытка {attempt + 1}/{self.MAX_RETRIES})")
                    raise RequestException("Получен некорректный ответ")
                    
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Ошибка при выполнении запроса (попытка {attempt + 1}/{self.MAX_RETRIES}): {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    continue
                    
        logger.error(f"Все попытки выполнить запрос к {url} завершились неудачно")
        raise RequestException(f"Не удалось выполнить запрос после {self.MAX_RETRIES} попыток: {str(last_error)}")
        
    def _get_cache_path(self, key: str) -> Path:
        """Получение пути к файлу кэша.
        
        Args:
            key: Ключ кэша
            
        Returns:
            Путь к файлу кэша
        """
        # Создаем хеш ключа для безопасного имени файла
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return Path(self.CACHE_DIR) / f"{hash_key}.json"
        
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Получение данных из кэша.
        
        Args:
            key: Ключ кэша
            
        Returns:
            Данные из кэша или None, если кэш устарел или отсутствует
        """
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
            
        try:
            data = json.loads(cache_path.read_text(encoding='utf-8'))
            # Проверяем время кэша
            if time.time() - data['timestamp'] > self.CACHE_TIME:
                logger.debug(f"Кэш устарел для ключа: {key}")
                return None
            return data['data']
        except Exception as e:
            logger.error(f"Ошибка при чтении кэша: {str(e)}")
            return None
            
    def _save_to_cache(self, key: str, data: Any):
        """Сохранение данных в кэш.
        
        Args:
            key: Ключ кэша
            data: Данные для сохранения
        """
        try:
            cache_path = self._get_cache_path(key)
            cache_data = {
                'timestamp': time.time(),
                'data': data
            }
            cache_path.write_text(json.dumps(cache_data, ensure_ascii=False), encoding='utf-8')
            logger.debug(f"Данные сохранены в кэш: {key}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {str(e)}")
            
    def _find_results_block(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Поиск блока с результатами с расширенной проверкой.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            Блок с результатами или None
        """
        # Проверяем наличие капчи
        if 'captcha' in soup.text.lower():
            logger.error("Обнаружена капча на странице")
            return None
            
        # Основные селекторы для поиска результатов
        results_selectors = [
            '.search-results',
            '#search-results',
            '.articles-list',
            '.articles',
            'main .items',
            '.search-results-list',
            '[data-target="search-results"]',
            '.publications-list',
            '#publications',
            'main article',
            '.content article',
            '[itemtype="http://schema.org/ScholarlyArticle"]'
        ]
        
        # Пробуем найти блок по селекторам
        for selector in results_selectors:
            results_block = soup.select_one(selector)
            if results_block:
                logger.debug(f"Найден блок результатов по селектору: {selector}")
                return results_block
                
        # Если не нашли по селекторам, ищем по содержимому
        potential_blocks = [
            # Ищем блоки, которые могут содержать статьи
            div for div in soup.find_all('div') 
            if div.find_all('article') or 
               div.find_all(class_=lambda x: x and ('article' in x.lower() or 'publication' in x.lower()))
        ]
        
        if potential_blocks:
            logger.debug("Найден блок результатов по содержимому")
            return potential_blocks[0]
            
        # Проверяем, есть ли сообщение об отсутствии результатов
        no_results_texts = [
            'ничего не найдено',
            'нет результатов',
            'no results',
            'not found'
        ]
        
        page_text = soup.text.lower()
        if any(text in page_text for text in no_results_texts):
            logger.info("Поиск не дал результатов")
            return None
            
        logger.error("Блок с результатами поиска не найден")
        logger.debug("Структура страницы:")
        logger.debug(f"Title: {soup.title.string if soup.title else 'No title'}")
        logger.debug(f"Body classes: {soup.body.get('class', []) if soup.body else 'No body'}")
        logger.debug(f"Main content areas: {[tag.name for tag in soup.find_all(['main', 'article', 'div'], class_=True)]}")
        
        return None
        
    def _find_articles(self, container: BeautifulSoup) -> List[BeautifulSoup]:
        """Поиск статей в контейнере с расширенной проверкой.
        
        Args:
            container: BeautifulSoup объект с контейнером
            
        Returns:
            Список найденных статей
        """
        # Основные селекторы для поиска статей
        article_selectors = [
            'article',
            '.article',
            '.publication',
            '.search-result',
            '.search-item',
            '.item',
            '[itemtype="http://schema.org/ScholarlyArticle"]',
            '.article-info',
            '.article-block',
            '.article-preview'
        ]
        
        # Пробуем найти статьи по селекторам
        for selector in article_selectors:
            articles = container.select(selector)
            if articles:
                logger.debug(f"Найдены статьи по селектору: {selector}")
                return articles
                
        # Если не нашли по селекторам, ищем по структуре
        articles = []
        
        # Ищем элементы, похожие на статьи
        for element in container.find_all(['div', 'article', 'section']):
            # Проверяем наличие характерных признаков статьи
            has_title = bool(element.find(['h1', 'h2', 'h3', 'h4', '.title', '.heading']))
            has_authors = bool(element.find(string=re.compile(r'автор|author', re.I)))
            has_year = bool(re.search(r'\b20\d{2}\b', element.text))
            
            if has_title and (has_authors or has_year):
                articles.append(element)
                
        if articles:
            logger.debug("Найдены статьи по структуре")
            return articles
            
        logger.warning("Статьи не найдены в блоке результатов")
        return []
        
    def search_articles(self, query: str, limit: int = 10, page: int = 1,
                       year_from: Optional[int] = None, year_to: Optional[int] = None,
                       categories: Optional[List[str]] = None) -> List[Article]:
        """Поиск статей.
        
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
            logger.info(f"Поиск статей по запросу: {query} (страница {page}, лимит {limit})")
        
            # Проверяем доступность сервиса перед поиском
            if not self.check_availability():
                logger.error("Сервис КиберЛенинки недоступен")
                return []
            
            # Проверяем кэш
            cache_key = f"search_{query}_{limit}_{page}_{year_from}_{year_to}_{categories}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                logger.info("Возвращены результаты из кэша")
                return [Article(**article_data) for article_data in cached_data]

                # Формируем URL для поиска
                search_url = f"{self.BASE_URL}/search"
                params = {
                    'q': query,
                    'page': page
                }

                # Добавляем параметры года если указаны
                if year_from:
                    params['year_from'] = year_from
                if year_to:
                    params['year_to'] = year_to

                # Выполняем запрос
                response = self._make_request(search_url, params=params)

                # Парсим результаты
                soup = BeautifulSoup(response.text, 'html.parser')

                # Ищем блок с результатами
                results_block = self._find_results_block(soup)
                if not results_block:
                    logger.warning("Блок с результатами не найден")
                    return []

                    # Парсим статьи
                articles = self._parse_articles(results_block, limit, categories)

                # Сохраняем в кэш только если нашли результаты
                if articles:
                    self._save_to_cache(cache_key, [article.to_dict() for article in articles])

                    return articles
                
        except Exception as e:
            logger.error(f"Ошибка при поиске статей: {str(e)}", exc_info=True)
            return []
            
    def _parse_articles(self, container: BeautifulSoup, limit: int, categories: Optional[List[str]] = None) -> List[Article]:
        """Парсинг статей из HTML.
        
        Args:
            container: BeautifulSoup объект с контейнером
            limit: Максимальное количество статей
            categories: Список категорий для фильтрации
            
        Returns:
            Список статей
        """
        articles = []
        article_elements = self._find_articles(container)
        
        for article_elem in article_elements[:limit]:
            try:
                # Извлекаем основную информацию
                title_elem = article_elem.find(['h2', 'h3', 'h4', '.title', '[itemprop="name"]'])
                title = title_elem.get_text(strip=True) if title_elem else None
                
                if not title:
                    continue
                    
                # Извлекаем авторов
                authors = []
                authors_elem = article_elem.find(['[itemprop="author"]', '.authors', '.author'])
                if authors_elem:
                    author_names = authors_elem.get_text(strip=True).split(',')
                    authors = [name.strip() for name in author_names if name.strip()]
                    
                # Извлекаем год
                year = None
                year_match = re.search(r'\b(19|20)\d{2}\b', article_elem.get_text())
                if year_match:
                    year = int(year_match.group())
                    
                # Извлекаем URL
                url = None
                link_elem = article_elem.find('a', href=True)
                if link_elem:
                    url = urllib.parse.urljoin(self.BASE_URL, link_elem['href'])
                            
                # Извлекаем аннотацию
                abstract = None
                abstract_elem = article_elem.find(['[itemprop="description"]', '.abstract', '.summary'])
                if abstract_elem:
                    abstract = abstract_elem.get_text(strip=True)
                    
                # Извлекаем категории
                article_categories = []
                categories_elem = article_elem.find(['[itemprop="about"]', '.categories', '.tags'])
                if categories_elem:
                    article_categories = [cat.strip() for cat in categories_elem.get_text(strip=True).split(',')]
                        
                # Создаем объект статьи
                article = Article(
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=abstract,
                    url=url,
                    categories=article_categories,
                    source="cyberleninka"
                )
                
                # Проверяем соответствие фильтрам
                if self._matches_filters(article, categories):
                    articles.append(article)
                    
            except Exception as e:
                logger.error(f"Ошибка при парсинге статьи: {str(e)}")
                continue
                
            if len(articles) >= limit:
                break
                
        return articles
        
    def _matches_filters(self, article: Article, categories: Optional[List[str]] = None) -> bool:
        """Проверка соответствия статьи фильтрам.
        
        Args:
            article: Объект статьи
            categories: Список категорий для фильтрации
            
        Returns:
            True если статья соответствует фильтрам, False иначе
        """
        if not categories:
            return True
            
        article_categories = set(cat.lower() for cat in article.categories)
        filter_categories = set(cat.lower() for cat in categories)
        
        return bool(article_categories & filter_categories)  # Проверяем пересечение множеств
        
    def get_article_pdf(self, article_id: str) -> Optional[bytes]:
        """Скачивание PDF статьи.
        
        Args:
            article_id: Идентификатор статьи
            
        Returns:
            Содержимое PDF файла или None в случае ошибки
        """
        logger.info(f"Начало скачивания PDF для статьи: {article_id}")
        try:
            # Получаем страницу статьи для поиска ссылки на PDF
            article_url = f"{self.BASE_URL}/article/{article_id.replace('cyberleninka_', '')}"
            
            response = self._make_request(article_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем ссылку на PDF
            pdf_selectors = [
                'a[href$=".pdf"]',
                '.download-pdf',
                '.article-download a'
            ]
            
            pdf_link = None
            for selector in pdf_selectors:
                pdf_elem = soup.select_one(selector)
                if pdf_elem and 'href' in pdf_elem.attrs:
                    pdf_link = pdf_elem['href']
                    break
                    
            if not pdf_link:
                logger.error("Ссылка на PDF не найдена")
                return None
                
            # Добавляем базовый URL если ссылка относительная
            if not pdf_link.startswith('http'):
                pdf_link = self.BASE_URL + pdf_link
                
            logger.debug(f"Скачивание PDF по ссылке: {pdf_link}")
            
            # Скачиваем PDF
            pdf_response = self._make_request(pdf_link)
            pdf_response.raise_for_status()
            
            return pdf_response.content
            
        except Exception as e:
            logger.error(f"Ошибка при скачивании PDF: {str(e)}", exc_info=True)
            return None
            
    def get_total_pages(self, query: str) -> int:
        """Получение общего количества страниц результатов.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Общее количество страниц
        """
        try:
            search_url = f"{self.BASE_URL}/search"
            params = {'q': query}
            
            response = self._make_request(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем элемент с информацией о пагинации
            pagination_selectors = [
                '.pagination',
                '.pages',
                '.page-numbers'
            ]
            
            for selector in pagination_selectors:
                pagination = soup.select_one(selector)
                if pagination:
                    # Ищем последний номер страницы
                    page_numbers = []
                    for page_elem in pagination.select('a'):
                        try:
                            page_numbers.append(int(page_elem.text.strip()))
                        except ValueError:
                            continue
                    
                    if page_numbers:
                        return max(page_numbers)
                        
            return 1
            
        except Exception as e:
            logger.error(f"Ошибка при получении количества страниц: {str(e)}", exc_info=True)
            return 1
            
    def get_categories(self) -> List[str]:
        """Получение списка доступных категорий.
        
        Returns:
            Список категорий
        """
        try:
            response = self._make_request(self.BASE_URL)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем элементы с категориями
            categories = set()
            category_selectors = [
                '.categories a',
                '.subjects a',
                '.topics a'
            ]
            
            for selector in category_selectors:
                for category_elem in soup.select(selector):
                    category = category_elem.text.strip()
                    if category:
                        categories.add(category)
                        
            return sorted(list(categories))
            
        except Exception as e:
            logger.error(f"Ошибка при получении категорий: {str(e)}", exc_info=True)
            return []

    def get_full_text(self, article_id: str) -> str:
        """Получение полного текста статьи.
        
        Args:
            article_id: Идентификатор статьи
            
        Returns:
            Полный текст статьи
        """
        logger.info(f"Начало получения текста статьи: {article_id}")
        
        # Проверяем кэш
        cache_key = f"full_text_{article_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info("Возвращен текст из кэша")
            return cached_data
        
        try:
            # Извлекаем URL из ID
            article_url = f"{self.BASE_URL}/article/{article_id.replace('cyberleninka_', '')}"
            logger.info(f"Получаем текст статьи: {article_url}")
            
            # Выполняем запрос
            response = self._make_request(article_url)
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Получаем текст статьи
            text_blocks = []
            
            # Пробуем разные селекторы для поиска текста
            content_selectors = [
                'div[itemprop="articleBody"]',
                '.ocr',
                '.article-text',
                '#article-text',
                '.paper-text',
                '[role="main"] article',
                '.content article'
            ]
            
            # Ищем текст по селекторам
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    # Удаляем ненужные элементы
                    for elem in content.select('script, style, .advertisement, .banner, .share-buttons'):
                        elem.decompose()
                    
                    # Получаем текст, сохраняя структуру
                    paragraphs = []
                    for p in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:  # Игнорируем короткие фрагменты
                            paragraphs.append(text)
                    
                    if paragraphs:
                        text_blocks.extend(paragraphs)
                        break
            
            if not text_blocks:
                # Если не нашли текст по селекторам, пробуем найти любой текстовый контент
                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                if main_content:
                    # Удаляем ненужные элементы
                    for elem in main_content.select('script, style, .advertisement, .banner, .share-buttons, header, footer, nav'):
                        elem.decompose()
                    
                    # Получаем параграфы текста
                    paragraphs = []
                    for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:
                            paragraphs.append(text)
                    
                    if paragraphs:
                        text_blocks.extend(paragraphs)
                    
            if not text_blocks:
                logger.warning("Текст статьи не найден")
                return ""
                
            # Объединяем текст
            full_text = "\n\n".join(text_blocks)
            
            # Сохраняем в кэш
            self._save_to_cache(cache_key, full_text)
            
            return full_text
            
        except Exception as e:
            logger.error(f"Ошибка при получении текста статьи: {str(e)}", exc_info=True)
            return ""

    def check_availability(self) -> bool:
        """Проверяет доступность сервиса.
        
        Returns:
            True если сервис доступен, False в противном случае
        """
        try:
            response = self._make_request(self.BASE_URL)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Сервис недоступен: {str(e)}")
            return False 