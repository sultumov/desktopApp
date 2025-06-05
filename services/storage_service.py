"""
Сервис для работы с локальным хранилищем статей.
"""
import logging
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from models.article import Article
from utils import get_user_data_dir, log_exception

logger = logging.getLogger(__name__)

class StorageService:
    """Сервис для работы с локальным хранилищем статей."""
    
    def __init__(self):
        """Инициализирует сервис."""
        # Создаем директории для хранения данных
        self.data_dir = get_user_data_dir()
        self.articles_dir = os.path.join(self.data_dir, 'articles')
        self.pdf_dir = os.path.join(self.data_dir, 'pdf')
        
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # Инициализируем кэш статей
        self._articles_cache = None
        
    def save_article(self, article):
        """Сохраняет статью в локальное хранилище.
        
        Args:
            article: Объект статьи для сохранения
        """
        try:
            # Создаем директории если их нет
            os.makedirs(self.articles_dir, exist_ok=True)
            
            # Получаем чистый ID статьи (убираем версию и домен)
            article_id = article.id
            if '/' in article_id:
                article_id = article_id.split('/')[-1]  # Берем последнюю часть после /
            if 'v' in article_id:
                article_id = article_id.split('v')[0]  # Убираем версию
                
            # Формируем путь для сохранения
            json_path = os.path.join(self.articles_dir, f"{article_id}.json")
            
            # Сохраняем метаданные в JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)
                
            logger.info(f"Статья сохранена: {json_path}")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении статьи: {str(e)}", exc_info=True)
            raise
            
    def add_article(self, article: Article) -> bool:
        """Добавляет статью в хранилище.
        
        Args:
            article: Объект статьи для добавления
            
        Returns:
            bool: True если статья успешно добавлена
        """
        try:
            # Создаем директории если их нет
            os.makedirs(self.articles_dir, exist_ok=True)
            os.makedirs(self.pdf_dir, exist_ok=True)
            
            # Получаем чистый ID статьи (убираем версию и домен)
            article_id = article.id
            if '/' in article_id:
                article_id = article_id.split('/')[-1]  # Берем последнюю часть после /
            if 'v' in article_id:
                article_id = article_id.split('v')[0]  # Убираем версию
                
            # Формируем пути для сохранения
            json_path = os.path.join(self.articles_dir, f"{article_id}.json")
            pdf_path = os.path.join(self.pdf_dir, f"{article_id}.pdf")
            
            # Если есть PDF, копируем его в хранилище
            if hasattr(article, 'local_pdf_path') and article.local_pdf_path:
                if os.path.exists(article.local_pdf_path):
                    shutil.copy2(article.local_pdf_path, pdf_path)
                    article.local_pdf_path = pdf_path
            
            # Сохраняем метаданные в JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)
                
            # Сбрасываем кэш
            self._articles_cache = None
            
            logger.info(f"Статья добавлена в хранилище: {json_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении статьи: {str(e)}", exc_info=True)
            return False
        
    def get_articles(self) -> List[Article]:
        """Возвращает список всех сохраненных статей."""
        try:
            # Используем кэш если есть
            if self._articles_cache is not None:
                return self._articles_cache
                
            articles = []
            
            # Получаем список файлов метаданных
            metadata_files = [f for f in os.listdir(self.articles_dir) if f.endswith('.json')]
            
            for metadata_file in metadata_files:
                try:
                    # Читаем метаданные
                    with open(os.path.join(self.articles_dir, metadata_file), 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        
                    # Создаем объект статьи
                    article = Article(
                        id=metadata.get('id'),
                        title=metadata.get('title'),
                        year=datetime.fromisoformat(metadata['published']).year if metadata.get('published') else None,
                        authors=metadata.get('authors', []),
                        abstract=metadata.get('abstract'),
                        published=datetime.fromisoformat(metadata['published']) if metadata.get('published') else None,
                        doi=metadata.get('doi'),
                        url=metadata.get('url'),
                        categories=metadata.get('categories', []),
                        source=metadata.get('source')
                    )
                    
                    # Добавляем путь к PDF если есть
                    if metadata.get('local_pdf_path'):
                        if os.path.exists(metadata['local_pdf_path']):
                            article.local_pdf_path = metadata['local_pdf_path']
                            
                    articles.append(article)
                    
                except Exception as e:
                    log_exception(f"Ошибка при чтении метаданных статьи {metadata_file}: {str(e)}")
                    continue
            
            # Сохраняем в кэш
            self._articles_cache = articles
                    
            return articles
            
        except Exception as e:
            log_exception(f"Ошибка при получении списка статей: {str(e)}")
            return []
            
    def delete_article(self, article_id: str) -> bool:
        """Удаляет статью из хранилища."""
        try:
            # Путь к файлу метаданных
            metadata_path = os.path.join(self.articles_dir, f"{article_id}.json")
            
            # Проверяем существование файла
            if not os.path.exists(metadata_path):
                return False
                
            # Читаем метаданные чтобы получить путь к PDF
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Удаляем PDF если есть
            if metadata.get('local_pdf_path'):
                if os.path.exists(metadata['local_pdf_path']):
                    os.remove(metadata['local_pdf_path'])
                    
            # Удаляем метаданные
            os.remove(metadata_path)
            
            # Сбрасываем кэш
            self._articles_cache = None
            
            return True
            
        except Exception as e:
            log_exception(f"Ошибка при удалении статьи: {str(e)}")
            return False
            
    def get_article(self, article_id: str) -> Optional[Article]:
        """Возвращает статью по идентификатору."""
        try:
            # Путь к файлу метаданных
            metadata_path = os.path.join(self.articles_dir, f"{article_id}.json")
            
            # Проверяем существование файла
            if not os.path.exists(metadata_path):
                return None
                
            # Читаем метаданные
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Создаем объект статьи
            article = Article(
                id=metadata.get('id'),
                title=metadata.get('title'),
                year=datetime.fromisoformat(metadata['published']).year if metadata.get('published') else None,
                authors=metadata.get('authors', []),
                abstract=metadata.get('abstract'),
                published=datetime.fromisoformat(metadata['published']) if metadata.get('published') else None,
                doi=metadata.get('doi'),
                url=metadata.get('url'),
                categories=metadata.get('categories', []),
                source=metadata.get('source')
            )
            
            # Добавляем путь к PDF если есть
            if metadata.get('local_pdf_path'):
                if os.path.exists(metadata['local_pdf_path']):
                    article.local_pdf_path = metadata['local_pdf_path']
                    
            return article
            
        except Exception as e:
            log_exception(f"Ошибка при получении статьи: {str(e)}")
            return None
            
    def update_article(self, article: Article) -> bool:
        """Обновляет статью в хранилище."""
        try:
            if not article.id:
                return False
                
            # Удаляем старую версию
            self.delete_article(article.id)
            
            # Сохраняем новую версию
            return self.save_article(article)
            
        except Exception as e:
            log_exception(f"Ошибка при обновлении статьи: {str(e)}")
            return False 