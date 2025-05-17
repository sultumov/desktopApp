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

# Настройка логгера
logger = logging.getLogger(__name__)

class CyberleninkaService:
    """Сервис для работы с КиберЛенинкой."""
    
    BASE_URL = "https://cyberleninka.ru"
    CACHE_DIR = "cache/cyberleninka"
    CACHE_TIME = 24 * 60 * 60  # 24 часа в секундах
    
    def __init__(self):
        """Инициализация сервиса."""
        logger.info("Инициализация CyberleninkaService")
        self.session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        logger.debug(f"Установлены заголовки запросов: {headers}")
        
        # Создаем директорию для кэша
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        
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
                       categories: Optional[List[str]] = None) -> list[Article]:
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
        logger.info(f"Поиск статей по запросу: {query} (страница {page}, лимит {limit})")
        
        # Проверяем кэш
        cache_key = f"search_{query}_{limit}_{page}_{year_from}_{year_to}_{categories}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info("Найдены результаты в кэше")
            return [Article(**article_data) for article_data in cached_data]
            
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Формируем URL
                encoded_query = urllib.parse.quote(query)
                url = f"{self.BASE_URL}/search?q={encoded_query}&page={page}"
                
                if year_from:
                    url += f"&year_from={year_from}"
                if year_to:
                    url += f"&year_to={year_to}"
                    
                logger.debug(f"URL запроса: {url}")
                
                # Делаем запрос
                response = self.session.get(url)
                response.raise_for_status()
                
                # Проверяем на наличие капчи
                if 'captcha' in response.text.lower():
                    logger.error("Обнаружена капча")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                    
                # Парсим HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем блок с результатами
                results_block = self._find_results_block(soup)
                if not results_block:
                    logger.warning("Блок с результатами не найден")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    return []
                    
                # Парсим статьи
                articles = self._parse_articles(soup, limit, categories)
                
                # Сохраняем в кэш
                articles_data = [article.to_dict() for article in articles]
                self._save_to_cache(cache_key, articles_data)
                
                logger.info(f"Найдено {len(articles)} статей")
                return articles
                
            except requests.RequestException as e:
                logger.error(f"Ошибка запроса: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise
                
            except Exception as e:
                logger.error(f"Ошибка при поиске: {str(e)}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise
                
        logger.error("Все попытки поиска завершились неудачно")
        return []
            
    def _parse_articles(self, soup: BeautifulSoup, limit: int, categories: Optional[List[str]] = None) -> List[Article]:
        """Парсинг статей из HTML.
        
        Args:
            soup: BeautifulSoup объект
            limit: Максимальное количество статей
            categories: Список категорий для фильтрации
            
        Returns:
            Список статей
        """
        articles = []
        results_block = self._find_results_block(soup)
        if not results_block:
            return articles
            
        # Ищем статьи
        articles_html = self._find_articles(results_block)
        logger.info(f"Найдено {len(articles_html)} статей на странице")
        
        for article_html in articles_html[:limit]:
            try:
                # Ищем основные элементы статьи
                title_elem = article_html.find(['h2', 'h3', 'h4', 'a'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                if not title_elem:
                    title_elem = article_html.find(['h2', 'h3', 'h4', 'a'])
                
                if not title_elem:
                    logger.warning("Не найден заголовок статьи")
                    continue
                    
                # Получаем ссылку и ID
                link = None
                if title_elem.name == 'a':
                    link = title_elem.get('href', '')
                else:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        link = link_elem.get('href', '')
                    else:
                        link_elem = article_html.find('a', href=True)
                        if link_elem:
                            link = link_elem.get('href', '')
                            
                if not link:
                    logger.warning("Не найдена ссылка на статью")
                    continue
                    
                if not link.startswith('http'):
                    link = f"{self.BASE_URL}{link}"
                    
                article_id = link.split('/')[-1]
                
                # Получаем название
                title = title_elem.get_text(strip=True)
                
                # Ищем авторов
                authors = []
                authors_container = article_html.find(['div', 'span'], class_=lambda x: x and 'author' in x.lower())
                if authors_container:
                    author_elements = authors_container.find_all(['a', 'span'])
                    for author_elem in author_elements:
                        author_name = author_elem.get_text(strip=True)
                        if author_name and ',' not in author_name and len(author_name.split()) <= 4:
                            authors.append(author_name)
                            
                # Ищем аннотацию
                abstract = ""
                abstract_elem = article_html.find(['div', 'p'], class_=lambda x: x and ('abstract' in x.lower() or 'description' in x.lower()))
                if abstract_elem:
                    abstract = abstract_elem.get_text(strip=True)
                    
                # Ищем год публикации
                year = None
                year_elem = article_html.find(['span', 'div'], class_=lambda x: x and ('year' in x.lower() or 'date' in x.lower()))
                if year_elem:
                    year_text = year_elem.get_text(strip=True)
                    year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                    if year_match:
                        year = int(year_match.group())
                        
                # Создаем объект статьи
                article = Article(
                    id=article_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=link,
                    year=year,
                    source="cyberleninka"
                )
                
                # Проверяем фильтры
                if self._matches_filters(article, categories):
                    articles.append(article)
                    
            except Exception as e:
                logger.error(f"Ошибка при парсинге статьи: {str(e)}", exc_info=True)
                continue
                
        return articles
        
    def _matches_filters(self, article: Article, categories: Optional[List[str]] = None) -> bool:
        """Проверка соответствия статьи фильтрам.
        
        Args:
            article: Статья
            categories: Список категорий
            
        Returns:
            True если статья соответствует фильтрам
        """
        if not categories:
            return True
            
        return any(category.lower() in [c.lower() for c in article.categories] for category in categories)
        
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
            
            response = self.session.get(article_url)
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
            pdf_response = self.session.get(pdf_link)
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
            
            response = self.session.get(search_url, params=params)
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
            response = self.session.get(self.BASE_URL)
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
        try:
            # Извлекаем URL из ID
            article_url = f"{self.BASE_URL}/article/{article_id.replace('cyberleninka_', '')}"
            logger.info(f"Получаем текст статьи: {article_url}")
            
            # Добавляем задержку перед запросом
            logger.debug("Ожидание 1 секунда перед запросом...")
            time.sleep(1)
            
            logger.debug("Отправка HTTP GET запроса...")
            response = self.session.get(article_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            logger.debug(f"Получен ответ, статус: {response.status_code}, длина: {len(response.text)} байт")
            
            # Парсим HTML
            logger.debug("Начало парсинга HTML...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Получаем текст статьи
            text_blocks = []
            
            # Пробуем разные селекторы для поиска текста
            content_selectors = [
                'div[itemprop="articleBody"]',
                '.ocr',
                '.article-text',
                '#article-text',
                '.paper-text'
            ]
            
            logger.debug(f"Поиск текста статьи по селекторам: {content_selectors}")
            for selector in content_selectors:
                blocks = soup.select(selector)
                if blocks:
                    logger.debug(f"Найден текст по селектору: {selector}")
                    text_blocks.extend([block.text.strip() for block in blocks])
                    
            if not text_blocks:
                logger.error("Текст статьи не найден")
                logger.debug(f"Первые 1000 символов HTML: {response.text[:1000]}")
                return ""
                
            text = "\n\n".join(text_blocks)
            logger.info(f"Получен текст статьи длиной {len(text)} символов")
            
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при получении текста статьи: {str(e)}", exc_info=True)
            return ""

    def check_availability(self) -> bool:
        """Проверяет доступность сервиса.
        
        Returns:
            True если сервис доступен, False в противном случае
        """
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            
            # Проверяем на наличие капчи
            if 'captcha' in response.text.lower():
                logger.error("Сервис требует капчу")
                return False
                
            return True
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при проверке доступности сервиса: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка при проверке сервиса: {str(e)}", exc_info=True)
            return False 