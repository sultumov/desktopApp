import os
import json
import pickle
from typing import List, Optional, Dict, Any
from datetime import datetime
import shutil

from models.article import Article, Author

class StorageService:
    """Сервис для хранения и управления библиотекой статей."""
    
    def __init__(self):
        """Инициализирует сервис хранения."""
        # Пути для хранения файлов
        self.data_dir = os.path.join(os.path.expanduser("~"), ".research_assistant")
        self.library_file = os.path.join(self.data_dir, "library.pickle")
        
        # Создаем директории, если они не существуют
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Загружаем библиотеку
        self.library = self._load_library()
    
    def _load_library(self) -> List[Article]:
        """
        Загружает библиотеку статей из файла.
        
        Returns:
            Список объектов Article
        """
        if os.path.exists(self.library_file):
            try:
                with open(self.library_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Ошибка при загрузке библиотеки: {str(e)}")
                return []
        return []
    
    def _save_library(self):
        """Сохраняет библиотеку статей в файл."""
        try:
            with open(self.library_file, 'wb') as f:
                pickle.dump(self.library, f)
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