"""Сервис для работы с КиберЛенинкой."""

import os
import re
import time
import json
import random
import hashlib
import logging
from pathlib import Path

import requests
import urllib.parse
from typing import List, Optional, Dict, Union, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from models.article import Article
from utils.error_utils import log_exception

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования DEBUG

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
                
                # Если есть параметры запроса, кодируем их правильно
                if 'params' in kwargs:
                    encoded_params = {}
                    for key, value in kwargs['params'].items():
                        if isinstance(value, str):
                            encoded_params[key] = urllib.parse.quote(value)
                        else:
                            encoded_params[key] = value
                    kwargs['params'] = encoded_params
                
                # Добавляем дополнительные заголовки для поискового запроса
                if '/search' in url:
                    self.session.headers.update({
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': 'https://cyberleninka.ru/',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1'
                    })
                
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
            
        # Логируем структуру страницы для отладки
        logger.debug("Анализ структуры страницы:")
        logger.debug(f"Title: {soup.title.string if soup.title else 'No title'}")
        logger.debug(f"Meta description: {soup.find('meta', {'name': 'description'})}")
        logger.debug("Основные блоки:")
        for tag in soup.find_all(['main', 'div', 'ul'], class_=True):
            logger.debug(f"- {tag.name}: class='{tag.get('class')}' id='{tag.get('id', '')}'")
            
        # Основные селекторы для поиска результатов
        results_selectors = [
            '.articles > .list',  # Новая структура
            '.articles .list > li',
            '.search-results > ul > li',
            '#search-results .list',
            '.articles-list > .list',
            '.articles > ul',
            'main .items',
            '.search-results-list',
            '[data-target="search-results"]',
            '.publications-list',
            '#publications',
            'main article',
            '.content article',
            '[itemtype="http://schema.org/ScholarlyArticle"]',
            '.article-list',
            '.search-list'
        ]
        
        # Пробуем найти блок по селекторам
        for selector in results_selectors:
            logger.debug(f"Проверка селектора: {selector}")
            results = soup.select(selector)
            if results:
                logger.debug(f"Найден блок результатов по селектору: {selector}")
                logger.debug(f"Количество найденных элементов: {len(results)}")
                return results
                
        # Если не нашли по селекторам, ищем по содержимому
        logger.debug("Поиск по содержимому...")
        potential_blocks = []
        
        # Ищем блоки с характерными признаками статей
        for container in soup.find_all(['div', 'ul']):
            # Проверяем наличие статей или элементов списка
            articles = container.find_all(['article', 'li'])
            if articles:
                # Проверяем, содержат ли эти элементы характерные признаки статей
                for article in articles[:3]:  # Проверяем первые 3 элемента
                    has_title = bool(article.find(['h1', 'h2', 'h3', 'h4', '.title', '[itemprop="name"]']))
                    has_link = bool(article.find('a', href=True))
                    has_author = bool(article.find(['[itemprop="author"]', '.author', '.authors']))
                    
                    if has_title and (has_link or has_author):
                        logger.debug(f"Найден потенциальный блок результатов: {container.name} {container.get('class', '')}")
                        potential_blocks.append(articles)
                        break
        
        if potential_blocks:
            logger.debug(f"Найдено {len(potential_blocks)} потенциальных блоков с результатами")
            return potential_blocks[0]
            
        # Проверяем, есть ли сообщение об отсутствии результатов
        no_results_texts = [
            'ничего не найдено',
            'нет результатов',
            'no results',
            'not found',
            'по вашему запросу'
        ]
        
        page_text = soup.text.lower()
        if any(text in page_text for text in no_results_texts):
            logger.info("Поиск не дал результатов")
            return None
            
        logger.error("Блок с результатами поиска не найден")
        logger.debug("Полная структура страницы:")
        logger.debug(soup.prettify()[:2000])  # Первые 2000 символов для анализа
        
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

            # Логируем URL и параметры запроса
            logger.info(f"Поисковый URL: {search_url}")
            logger.info(f"Параметры запроса: {params}")

            # Выполняем запрос
            response = self._make_request(search_url, params=params)
            
            # Логируем ответ сервера
            logger.info(f"Код ответа: {response.status_code}")
            logger.info(f"Заголовки ответа: {response.headers}")
            logger.debug(f"Текст ответа: {response.text[:500]}...")  # Первые 500 символов

            # Парсим результаты
            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем блок с результатами
            results_block = self._find_results_block(soup)
            if not results_block:
                logger.warning("Блок с результатами не найден")
                logger.debug(f"HTML страницы: {soup.prettify()[:1000]}...")  # Первые 1000 символов
                return []

            # Парсим статьи
            articles = self._parse_articles(results_block, limit, categories)

            # Логируем количество найденных статей
            logger.info(f"Найдено статей: {len(articles)}")

            # Сохраняем в кэш только если нашли результаты
            if articles:
                self._save_to_cache(cache_key, [article.to_dict() for article in articles])

            return articles
                
        except Exception as e:
            logger.error(f"Ошибка при поиске статей: {str(e)}", exc_info=True)
            return []
            
    def _parse_articles(self, container: List[BeautifulSoup], limit: int, categories: Optional[List[str]] = None) -> List[Article]:
        """Парсинг статей из HTML.
        
        Args:
            container: Список элементов BeautifulSoup с контейнерами статей
            limit: Максимальное количество статей
            categories: Список категорий для фильтрации
            
        Returns:
            Список статей
        """
        articles = []
        
        # Если container - это список элементов li, используем их напрямую
        article_elements = container
        if len(container) == 1 and container[0].name in ['div', 'ul']:
            # Если получили один контейнер, ищем в нем элементы статей
            article_elements = container[0].find_all(['li', 'article'])
        
        logger.debug(f"Найдено элементов для парсинга: {len(article_elements)}")
        
        for article_elem in article_elements[:limit]:
            try:
                logger.debug(f"Парсинг элемента: {article_elem.name} {article_elem.get('class', '')}")
                
                # Извлекаем основную информацию
                title = None
                url = None
                
                # Ищем ссылку, которая обычно содержит заголовок
                link_elem = article_elem.find('a', href=True)
                if link_elem:
                    url = urllib.parse.urljoin(self.BASE_URL, link_elem['href'])
                    # Пробуем найти заголовок в ссылке
                    title_elem = link_elem.find(['h2', 'h3', 'h4', '.title', '[itemprop="name"]'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        # Если в ссылке нет специального элемента с заголовком, используем текст ссылки
                        title = link_elem.get_text(strip=True)
                
                if not title:
                    # Если не нашли в ссылке, ищем заголовок в самом элементе статьи
                    title_elem = article_elem.find(['h2', 'h3', 'h4', '.title', '[itemprop="name"]'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                if not title or not url:
                    logger.debug("Пропуск элемента: не найден заголовок или URL")
                    continue
                
                # Извлекаем ID из URL
                article_id = url.split('/')[-1] if url else None
                
                # Извлекаем авторов
                authors = []
                authors_container = article_elem.find(['[itemprop="author"]', '.authors', '.author', '.authors-list'])
                if authors_container:
                    # Сначала ищем отдельные элементы авторов
                    author_elements = authors_container.find_all(['a', 'span'])
                    if author_elements:
                        for author_elem in author_elements:
                            author_name = author_elem.get_text(strip=True)
                            if author_name and not any(x in author_name.lower() for x in ['автор', 'authors']):
                                authors.append(author_name)
                    
                    if not authors:
                        # Если не нашли отдельные элементы, берем весь текст
                        author_text = authors_container.get_text(strip=True)
                        # Очищаем от лишних слов
                        author_text = re.sub(r'^(автор[ы]?|author[s]?)[:]\s*', '', author_text, flags=re.I)
                        # Разделяем по запятой и очищаем
                        authors = [name.strip() for name in author_text.split(',') if name.strip()]
                
                # Извлекаем год
                year = None
                year_container = article_elem.find(class_=lambda x: x and 'year' in x.lower())
                if year_container:
                    year_match = re.search(r'\b(19|20)\d{2}\b', year_container.get_text())
                    if year_match:
                        year = int(year_match.group())
                if not year:
                    # Если не нашли в специальном контейнере, ищем в любом тексте
                    year_match = re.search(r'\b(19|20)\d{2}\b', article_elem.get_text())
                    if year_match:
                        year = int(year_match.group())
                
                # Извлекаем аннотацию
                abstract = None
                abstract_elem = article_elem.find(['[itemprop="description"]', '.abstract', '.summary', '.description'])
                if abstract_elem:
                    abstract = abstract_elem.get_text(strip=True)
                
                # Извлекаем категории
                article_categories = []
                categories_container = article_elem.find(['[itemprop="about"]', '.categories', '.tags', '.subjects'])
                if categories_container:
                    # Сначала ищем отдельные элементы категорий
                    category_elements = categories_container.find_all(['a', 'span'])
                    if category_elements:
                        for cat_elem in category_elements:
                            cat_name = cat_elem.get_text(strip=True)
                            if cat_name:
                                article_categories.append(cat_name)
                    
                    if not article_categories:
                        # Если не нашли отдельные элементы, берем весь текст
                        category_text = categories_container.get_text(strip=True)
                        # Очищаем от лишних слов
                        category_text = re.sub(r'^(категори[и]?|categor(y|ies))[:]\s*', '', category_text, flags=re.I)
                        # Разделяем по запятой и очищаем
                        article_categories = [cat.strip() for cat in category_text.split(',') if cat.strip()]
                
                # Создаем объект статьи
                article = Article(
                    id=f"cyberleninka_{article_id}" if article_id else None,
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=abstract,
                    url=url,
                    categories=article_categories,
                    source="cyberleninka"
                )
                
                logger.debug(f"Создана статья: {article.title}")
                
                # Проверяем соответствие фильтрам
                if self._matches_filters(article, categories):
                    articles.append(article)
                    
            except Exception as e:
                logger.error(f"Ошибка при парсинге статьи: {str(e)}")
                continue
                
            if len(articles) >= limit:
                break
                
        logger.info(f"Успешно обработано статей: {len(articles)}")
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

    def extract_keywords(self, article_id: str) -> List[str]:
        """Извлекает ключевые слова из статьи.
        
        Args:
            article_id: Идентификатор статьи
            
        Returns:
            Список ключевых слов
        """
        logger.info(f"Извлечение ключевых слов для статьи: {article_id}")
        
        try:
            # Получаем страницу статьи
            article_url = f"{self.BASE_URL}/article/{article_id.replace('cyberleninka_', '')}"
            response = self._make_request(article_url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем блок с ключевыми словами
            keywords = []
            
            # Пробуем разные селекторы для поиска ключевых слов
            keyword_selectors = [
                '[itemprop="keywords"]',
                '.keywords',
                '.article-tags',
                '.tags'
            ]
            
            for selector in keyword_selectors:
                keyword_block = soup.select_one(selector)
                if keyword_block:
                    # Извлекаем ключевые слова
                    for keyword in keyword_block.stripped_strings:
                        # Очищаем и нормализуем ключевое слово
                        keyword = keyword.strip().strip(',').strip()
                        if keyword and keyword.lower() not in ['ключевые слова:', 'keywords:', 'tags:']:
                            keywords.append(keyword)
                    break
            
            if not keywords:
                # Если не нашли по селекторам, ищем в тексте
                text_patterns = [
                    r'Ключевые слова:?\s*([^\.]+)',
                    r'Keywords:?\s*([^\.]+)',
                    r'Теги:?\s*([^\.]+)'
                ]
                
                text = soup.get_text()
                for pattern in text_patterns:
                    match = re.search(pattern, text, re.I)
                    if match:
                        # Разбиваем на отдельные слова
                        words = match.group(1).split(',')
                        keywords.extend([w.strip() for w in words if w.strip()])
                        break
            
            # Удаляем дубликаты и сортируем
            keywords = sorted(set(keywords))
            
            logger.info(f"Найдено ключевых слов: {len(keywords)}")
            return keywords
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых слов: {str(e)}", exc_info=True)
            return []

    def find_references(self, article_id: str) -> List[str]:
        """Извлекает список источников из статьи.
        
        Args:
            article_id: Идентификатор статьи
            
        Returns:
            Список найденных источников
        """
        logger.info(f"Поиск источников для статьи: {article_id}")
        
        try:
            # Получаем полный текст статьи
            text = self.get_full_text(article_id)
            
            if not text:
                logger.warning("Не удалось получить текст статьи")
                return []
                
            # Ищем секцию с источниками
            references = []
            
            # Паттерны для поиска заголовка списка литературы
            header_patterns = [
                r'Список литературы:?',
                r'Литература:?',
                r'Библиографический список:?',
                r'Библиография:?',
                r'References:?',
                r'Bibliography:?'
            ]
            
            # Ищем начало списка литературы
            start_pos = -1
            for pattern in header_patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    start_pos = match.end()
                    break
                    
            if start_pos == -1:
                logger.warning("Не найден список литературы")
                return []
                
            # Получаем текст после заголовка
            references_text = text[start_pos:].strip()
            
            # Паттерны для поиска отдельных источников
            ref_patterns = [
                r'\d+\.\s+[А-Я][^.]+\.',  # Нумерованные источники
                r'[А-Я][а-я]+\s+[А-Я]\.\s*[А-Я]\.',  # Автор И.О.
                r'\[(\d+)\][\s\n]*([^[]+)',  # [1] Источник
                r'(?<!\d)(\d{4})[\s\n]*([A-ZА-Я][^.]+\.)',  # Год Источник
                r'([A-ZА-Я][a-zа-я]+(?:\s+(?:et\.?\s+al\.?|and|&)\s+[A-ZА-Я][a-zа-я]+)?)\s+\((\d{4})\)'  # Автор (Год)
            ]
            
            # Ищем источники по паттернам
            for pattern in ref_patterns:
                matches = re.finditer(pattern, references_text)
                for match in matches:
                    ref = match.group(0).strip()
                    if ref and ref not in references and len(ref) > 10:  # Проверяем минимальную длину
                        references.append(ref)
                        
            # Если не нашли по паттернам, пробуем разбить по переносам строк
            if not references:
                lines = references_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10 and not line.lower().startswith(('список', 'литература', 'references')):
                        references.append(line)
                        
            logger.info(f"Найдено источников: {len(references)}")
            return references
            
        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}", exc_info=True)
            return []

    def get_article(self, article_id: str) -> Optional[Article]:
        """Получает информацию о статье по её ID.
        
        Args:
            article_id: Идентификатор статьи
            
        Returns:
            Объект статьи или None в случае ошибки
        """
        logger.info(f"Получение информации о статье: {article_id}")
        
        try:
            # Получаем страницу статьи
            article_url = f"{self.BASE_URL}/article/{article_id.replace('cyberleninka_', '')}"
            response = self._make_request(article_url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем основную информацию
            title = None
            title_elem = soup.find(['h1', '[itemprop="name"]'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                
            if not title:
                logger.warning("Не найдено название статьи")
                return None
                
            # Извлекаем авторов
            authors = []
            authors_elem = soup.find(['[itemprop="author"]', '.authors', '.author'])
            if authors_elem:
                author_names = authors_elem.get_text(strip=True).split(',')
                authors = [name.strip() for name in author_names if name.strip()]
                
            # Извлекаем год
            year = None
            year_match = re.search(r'\b(19|20)\d{2}\b', soup.get_text())
            if year_match:
                year = int(year_match.group())
                
            # Извлекаем аннотацию
            abstract = None
            abstract_elem = soup.find(['[itemprop="description"]', '.abstract', '.summary'])
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
                
            # Извлекаем категории
            categories = []
            categories_elem = soup.find(['[itemprop="about"]', '.categories', '.tags'])
            if categories_elem:
                categories = [cat.strip() for cat in categories_elem.get_text(strip=True).split(',')]
                
            # Создаем объект статьи
            article = Article(
                id=article_id,
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                url=article_url,
                categories=categories,
                source="cyberleninka"
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о статье: {str(e)}", exc_info=True)
            return None 