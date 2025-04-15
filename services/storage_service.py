import os
import json
import pickle
from typing import List, Optional, Dict, Any
from datetime import datetime
import shutil
import logging
import random
import re
from pathlib import Path

from models.article import Article, Author

class StorageService:
    """Сервис для хранения и управления библиотекой статей."""
    
    def __init__(self):
        """Инициализирует сервис для работы с библиотекой."""
        # Каталог для хранения библиотеки (создаем, если не существует)
        self.library_dir = os.path.join(os.getcwd(), "library")
        
        # Путь к файлу с данными библиотеки
        self.library_file = os.path.join(self.library_dir, "library.json")
        
        # Создаем каталог, если он не существует
        if not os.path.exists(self.library_dir):
            os.makedirs(self.library_dir)
            
        # Проверяем существование файла библиотеки
        if not os.path.exists(self.library_file):
            # Инициализируем пустую библиотеку
            self._save_library([])
    
    def load_library(self) -> List[Article]:
        """
        Загружает библиотеку статей.
        
        Returns:
            Список объектов Article
        """
        try:
            # Если файл библиотеки не существует, возвращаем пустой список
            if not os.path.exists(self.library_file):
                return []
            
            # Загружаем данные из JSON
            with open(self.library_file, 'r', encoding='utf-8') as f:
                library_data = json.load(f)
            
            # Преобразуем данные в объекты Article
            articles = []
            
            for article_data in library_data:
                try:
                    # Создаем объекты Author
                    authors = []
                    for author_data in article_data.get("authors", []):
                        if isinstance(author_data, str):
                            authors.append(Author(name=author_data))
                        else:
                            authors.append(Author(
                                name=author_data.get("name", "Unknown"),
                                affiliation=author_data.get("affiliation"),
                                email=author_data.get("email")
                            ))
                    
                    # Если авторы не указаны, добавляем Unknown
                    if not authors:
                        authors.append(Author(name="Unknown"))
                    
                    # Преобразуем строку даты в объект datetime
                    added_date = datetime.fromisoformat(article_data.get("added_date", datetime.now().isoformat()))
                    
                    # Создаем объект Article
                    article = Article(
                        title=article_data.get("title", "Untitled"),
                        authors=authors,
                        abstract=article_data.get("abstract", ""),
                        year=article_data.get("year", 0),
                        doi=article_data.get("doi"),
                        url=article_data.get("url"),
                        journal=article_data.get("journal"),
                        volume=article_data.get("volume"),
                        issue=article_data.get("issue"),
                        pages=article_data.get("pages"),
                        keywords=article_data.get("keywords", []),
                        full_text=article_data.get("full_text"),
                        file_path=article_data.get("file_path"),
                        categories=article_data.get("categories", []),
                        added_date=added_date,
                        source=article_data.get("source", "Unknown"),
                        citation_count=article_data.get("citation_count", 0),
                        reference_count=article_data.get("reference_count", 0),
                        paper_id=article_data.get("paper_id")
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logging.error(f"Ошибка при преобразовании статьи: {str(e)}")
                    continue
            
            # Если библиотека пуста, генерируем тестовые статьи
            if not articles:
                articles = self.mock_library()
                self._save_library(articles)
                
            return articles
            
        except Exception as e:
            logging.error(f"Ошибка при загрузке библиотеки: {str(e)}")
            
            # Генерируем тестовые статьи при ошибке
            mock_articles = self.mock_library()
            self._save_library(mock_articles)
            
            return mock_articles
    
    def mock_library(self, count=15) -> List[Article]:
        """
        Генерирует тестовую библиотеку статей для демонстрации.
        
        Args:
            count (int): Количество статей для генерации
            
        Returns:
            Список объектов Article
        """
        articles = []
        current_year = datetime.now().year
        
        # Темы для научных статей
        topics = [
            "Искусственный интеллект и машинное обучение",
            "Нейросетевые модели для обработки естественного языка",
            "Квантовые вычисления: теория и практика",
            "Методы оптимизации в машинном обучении",
            "Компьютерное зрение и распознавание образов",
            "Глубокое обучение в анализе данных",
            "Методы обработки больших данных",
            "Алгоритмы интеллектуального анализа текста",
            "Робототехника и автоматизация",
            "Информационная безопасность и шифрование",
            "Моделирование сложных систем",
            "Генеративные нейронные сети",
            "Алгоритмы компьютерной графики",
            "Системы рекомендаций и коллаборативная фильтрация",
            "Методы классификации и кластеризации данных",
            "Обработка изображений и сигналов",
            "Системы поддержки принятия решений",
            "Многоагентные системы и распределенный искусственный интеллект",
            "Нейросимволические вычисления",
            "Интерпретируемость моделей машинного обучения"
        ]
        
        # Журналы
        journals = [
            "Journal of Artificial Intelligence Research",
            "IEEE Transactions on Pattern Analysis and Machine Intelligence",
            "Neural Networks",
            "Journal of Machine Learning Research",
            "Pattern Recognition",
            "Computer Vision and Image Understanding",
            "Data Mining and Knowledge Discovery",
            "International Journal of Computer Vision",
            "Artificial Intelligence",
            "IEEE Transactions on Neural Networks and Learning Systems"
        ]
        
        # Источники
        sources = ["Google Scholar", "Semantic Scholar", "Импорт вручную", "Файловая система"]
        
        # Категории
        all_categories = ["ИИ", "Машинное обучение", "Компьютерное зрение", "Обработка языка", 
                       "Робототехника", "Теория информации", "Алгоритмы", "Данные"]
        
        # Генерация статей
        for i in range(count):
            # Выбираем случайную тему
            title = random.choice(topics)
            
            # Генерируем авторов (2-4 автора)
            author_count = random.randint(2, 4)
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                          "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson"]
            first_names = ["John", "Robert", "Michael", "David", "James", "Mary", "Patricia", 
                           "Jennifer", "Linda", "Elizabeth", "Sarah", "Anna", "Emily", "Jessica"]
            
            authors = []
            for j in range(author_count):
                last_name = random.choice(last_names)
                first_name = random.choice(first_names)
                authors.append(Author(name=f"{last_name}, {first_name[0]}."))
            
            # Год публикации (последние 5 лет)
            year = random.randint(current_year - 5, current_year)
            
            # Формируем абстракт
            abstract = (
                f"Abstract: This paper presents research on {title.lower()}. "
                f"We propose a novel approach to address the key challenges in this field. "
                f"Our methods demonstrate significant improvements over existing techniques, "
                f"achieving state-of-the-art results on several benchmark datasets. "
                f"We provide extensive experimental validation and discuss the implications "
                f"for future research in this rapidly evolving domain."
            )
            
            # Журнал и выходные данные
            journal = random.choice(journals)
            volume = str(random.randint(1, 40))
            issue = str(random.randint(1, 12))
            pages = f"{random.randint(1, 500)}-{random.randint(501, 1000)}"
            
            # Генерируем DOI
            doi = f"10.{random.randint(1000, 9999)}/{random.choice(['acm', 'ieee', 'jmlr', 'springer'])}.{year}.{random.randint(10000, 99999)}"
            
            # Выбираем случайные категории (1-3)
            category_count = random.randint(1, 3)
            categories = random.sample(all_categories, category_count)
            
            # Дата добавления (последние 6 месяцев)
            days_ago = random.randint(0, 180)
            added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            added_date = added_date.replace(day=added_date.day - days_ago % 30, month=added_date.month - days_ago // 30)
            
            # Создаем статью
            article = Article(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                doi=doi,
                url=f"https://doi.org/{doi}",
                journal=journal,
                volume=volume,
                issue=issue,
                pages=pages,
                keywords=title.lower().split()[:5],
                categories=categories,
                added_date=added_date,
                source=random.choice(sources),
                citation_count=random.randint(0, 100),
                reference_count=random.randint(5, 50)
            )
            
            articles.append(article)
        
        return articles
    
    def _save_library(self, library: List[Article]):
        """Сохраняет библиотеку статей в файл."""
        try:
            # Преобразуем объекты Article в данные для сохранения
            library_data = []
            for article in library:
                article_data = {
                    'title': article.title,
                    'authors': [{'name': author.name} for author in article.authors],
                    'year': article.year,
                    'abstract': article.abstract,
                    'journal': article.journal,
                    'url': article.url,
                    'added_date': article.added_date.isoformat(),
                    'categories': article.categories,
                    'source': article.source,
                    'citation_count': article.citation_count,
                    'reference_count': article.reference_count,
                    'paper_id': article.paper_id
                }
                library_data.append(article_data)
            
            # Сохраняем данные в файл
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении библиотеки: {str(e)}")
    
    def add_article(self, article: Article) -> bool:
        """
        Добавляет статью в библиотеку.
        
        Args:
            article: Объект Article для добавления
            
        Returns:
            True, если статья успешно добавлена
        """
        # Проверяем, нет ли уже такой статьи
        for existing in self.library:
            if existing.title == article.title and existing.year == article.year:
                # Обновляем существующую статью
                existing.authors = article.authors
                existing.abstract = article.abstract
                existing.journal = article.journal
                existing.url = article.url or existing.url
                existing.full_text = article.full_text or existing.full_text
                self._save_library()
                return True
        
        # Добавляем новую статью
        article.added_date = datetime.now()
        self.library.append(article)
        self._save_library()
        return True
    
    def get_library_articles(self, category: str = "Все") -> List[Article]:
        """
        Возвращает статьи из библиотеки, отфильтрованные по категории.
        
        Args:
            category: Категория для фильтрации (по умолчанию "Все")
            
        Returns:
            Список объектов Article
        """
        if category == "Все":
            return self.library
        
        # Фильтруем по категории
        return [article for article in self.library if category in article.categories]
    
    def delete_articles(self, indices: List[int]) -> bool:
        """
        Удаляет статьи из библиотеки по индексам.
        
        Args:
            indices: Список индексов статей для удаления
            
        Returns:
            True, если статьи успешно удалены
        """
        # Сортируем индексы в обратном порядке, чтобы не нарушать индексы при удалении
        indices = sorted(indices, reverse=True)
        
        for index in indices:
            if 0 <= index < len(self.library):
                del self.library[index]
        
        self._save_library()
        return True
    
    def export_articles(self, indices: List[int], output_path: str) -> bool:
        """
        Экспортирует выбранные статьи в файл.
        
        Args:
            indices: Список индексов статей для экспорта
            output_path: Путь для сохранения экспорта
            
        Returns:
            True, если экспорт успешен
        """
        try:
            # Получаем статьи для экспорта
            articles = [self.library[i] for i in indices if 0 <= i < len(self.library)]
            
            # Определяем формат на основе расширения файла
            _, ext = os.path.splitext(output_path)
            ext = ext.lower()
            
            if ext == '.bib':
                # Экспорт в формате BibTeX
                with open(output_path, 'w', encoding='utf-8') as f:
                    for article in articles:
                        f.write(article.to_bibtex() + "\n\n")
            
            elif ext == '.pdf':
                # Экспорт в PDF
                # Для этого нужна библиотека вроде reportlab
                return False
            
            elif ext == '.docx':
                # Экспорт в Word
                # Для этого нужна библиотека вроде python-docx
                return False
            
            elif ext == '.txt':
                # Простой текстовый экспорт
                with open(output_path, 'w', encoding='utf-8') as f:
                    for article in articles:
                        f.write(article.citation + "\n\n")
            
            elif ext == '.json':
                # Экспорт в JSON
                data = []
                for article in articles:
                    # Создаем словарь с данными статьи
                    article_data = {
                        'title': article.title,
                        'authors': [{'name': author.name} for author in article.authors],
                        'year': article.year,
                        'abstract': article.abstract,
                        'journal': article.journal,
                        'url': article.url
                    }
                    data.append(article_data)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            else:
                # Неизвестный формат
                return False
            
            return True
            
        except Exception as e:
            print(f"Ошибка при экспорте: {str(e)}")
            return False
    
    def load_file(self, file_path: str) -> str:
        """
        Загружает текст из файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Строка с содержимым файла
        """
        try:
            # PDF-файл
            if file_path.lower().endswith('.pdf'):
                from PyPDF2 import PdfReader
                
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    text = ""
                    
                    # Извлекаем текст из всех страниц
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    
                    return text
            
            # Текстовый файл
            elif file_path.lower().endswith(('.txt', '.md')):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # Неподдерживаемый формат
            else:
                return f"Неподдерживаемый формат файла: {file_path}"
                
        except Exception as e:
            return f"Ошибка при чтении файла: {str(e)}"
    
    def save_file(self, content: str, file_path: str) -> bool:
        """
        Сохраняет текст в файл.
        
        Args:
            content: Содержимое для сохранения
            file_path: Путь для сохранения
            
        Returns:
            True, если файл успешно сохранен
        """
        try:
            # Создаем директории, если они не существуют
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Ошибка при сохранении файла: {str(e)}")
            return False 