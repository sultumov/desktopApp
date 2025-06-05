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
        
    def save_article(self, article: Article) -> bool:
        """Сохраняет статью в хранилище."""
        try:
            # Создаем уникальный идентификатор для статьи
            article_id = article.id or str(datetime.now().timestamp())
            
            # Сохраняем метаданные
            metadata = {
                'id': article_id,
                'title': article.title,
                'authors': article.authors,
                'abstract': article.abstract,
                'published': article.published.isoformat() if article.published else None,
                'doi': article.doi,
                'url': article.url,
                'categories': article.categories,
                'source': article.source,
                'local_pdf_path': article.local_pdf_path if hasattr(article, 'local_pdf_path') else None
            }
            
            # Путь к файлу метаданных
            metadata_path = os.path.join(self.articles_dir, f"{article_id}.json")
            
            # Сохраняем метаданные
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            # Если есть PDF, копируем его в хранилище
            if hasattr(article, 'local_pdf_path') and article.local_pdf_path:
                if os.path.exists(article.local_pdf_path):
                    pdf_filename = os.path.basename(article.local_pdf_path)
                    new_pdf_path = os.path.join(self.pdf_dir, f"{article_id}_{pdf_filename}")
                    shutil.copy2(article.local_pdf_path, new_pdf_path)
                    
                    # Обновляем путь к PDF в метаданных
                    metadata['local_pdf_path'] = new_pdf_path
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Сбрасываем кэш
            self._articles_cache = None
                        
            return True
            
        except Exception as e:
            log_exception(f"Ошибка при сохранении статьи: {str(e)}")
            return False
            
    def add_article(self, article: Article) -> bool:
        """Алиас для метода save_article."""
        return self.save_article(article)
        
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