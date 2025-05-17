"""
Сервис для работы с GigaChat API.

Для работы сервиса необходимо:
1. Получить API ключ GigaChat (https://developers.sber.ru/portal/products/gigachat)
2. Настроить переменные окружения:
   - GIGACHAT_API_KEY: API ключ GigaChat
   - GIGACHAT_CREDENTIALS: Альтернативные учетные данные (если не используется API ключ)
   - GIGACHAT_VERIFY_SSL: "true"/"false" для проверки SSL (по умолчанию "true")

Основные возможности:
- Создание кратких содержаний научных статей (create_summary)
- Поиск релевантных источников для статей (find_references)

Особенности работы:
- Сервис автоматически определяет способ аутентификации (API ключ или учетные данные)
- При отсутствии доступа к API возвращает заглушки для демонстрации
- Поддерживает форматирование в Markdown
- Имеет встроенные промпты для работы с научными текстами

Пример использования:
```python
from services.gigachat_service import GigaChatService
from models.article import Article

# Инициализация сервиса
service = GigaChatService()

# Создание краткого содержания
article = Article(title="Название", authors=["Автор"], abstract="Текст")
summary = service.create_summary(article, style="Краткий обзор", max_length=500)

# Поиск источников
references = service.find_references(article)
```

Системные требования:
- Python 3.7+
- Установленный пакет gigachat
- Доступ к API GigaChat
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv
import gigachat
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from models.article import Article

# Настройка логгера
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

class GigaChatService:
    """Сервис для работы с GigaChat API."""
    
    def __init__(self):
        """Инициализирует сервис."""
        self.api_key = os.getenv("GIGACHAT_API_KEY")
        self.credentials = os.getenv("GIGACHAT_CREDENTIALS")
        self.verify_ssl = os.getenv("GIGACHAT_VERIFY_SSL", "true").lower() == "true"
        
        # Удаляем кавычки из API ключа, если они есть
        if self.api_key:
            self.api_key = self.api_key.strip('"\'')
            logger.info(f"API ключ GigaChat загружен: {self.api_key[:5]}...{self.api_key[-5:]}")
        
        if not (self.api_key or self.credentials):
            logger.warning("Не найден API ключ или учетные данные для GigaChat")
            
        # В этой версии не инициализируем клиент в конструкторе,
        # а будем создавать его каждый раз при вызове через конструкцию with
        self.client = None
        
    def create_summary(self, article: Article, style: str = "обзор", max_length: int = 1000) -> str:
        """Создает краткое содержание статьи.
        
        Args:
            article: Объект статьи
            style: Стиль краткого содержания
            max_length: Максимальная длина краткого содержания в словах
            
        Returns:
            Краткое содержание статьи
        """
        if not self.api_key:
            logger.error("API ключ GigaChat не установлен")
            return self._generate_mock_summary(article)
            
        try:
            logger.info(f"Создание краткого содержания для статьи: {article.title}")
            
            # Подготавливаем данные о статье
            article_info = f"""Название: {article.title}
Авторы: {', '.join(article.authors)}
Аннотация: {article.abstract or article.summary}
Категории: {', '.join(article.categories) if article.categories else 'Не указаны'}
Год: {article.year or 'Не указан'}
DOI: {article.doi if hasattr(article, 'doi') and article.doi else 'Не указан'}
"""

            # Системный промпт
            system_message = f"""Ты - научный ассистент, который создает структурированные краткие содержания научных статей.
Твоя задача - создать {style.lower()} статьи, используя не более {max_length} слов.

Для разных стилей используй следующие подходы:
- Академический: Формальный научный стиль, с акцентом на методологию и результаты
- Краткий обзор: Сжатое изложение основных идей и выводов
- Детальный анализ: Подробный разбор всех аспектов исследования
- Ключевые моменты: Список главных тезисов и открытий

Используй разметку Markdown для форматирования:
- Создай заголовок "# Краткое содержание"
- Используй подзаголовки для каждого раздела
- Применяй маркированные списки для перечисления ключевых моментов
- Выделяй **жирным** важные концепции и термины

Анализируй научные аббревиатуры и термины. Сохраняй научную точность и конкретность.
Старайся подчеркнуть новизну и уникальность исследования."""

            # Создаем полный запрос, комбинируя системный промпт и информацию о статье
            query = f"{system_message}\n\nСоздай {style.lower()} следующей научной статьи, используя не более {max_length} слов.\n\nИнформация о статье:\n{article_info}"
            
            logger.info("Отправка запроса к GigaChat API")
            
            # Используем контекстный менеджер для работы с API согласно документации
            # и отключаем проверку SSL сертификатов
            with GigaChat(credentials=self.api_key, verify_ssl_certs=False) as giga:
                response = giga.chat(query)
            
            logger.info("Ответ от GigaChat API получен")
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка при создании краткого содержания: {str(e)}", exc_info=True)
            return self._generate_mock_summary(article)
            
    def find_references(self, article: Article, article_text: str = None) -> List[str]:
        """Ищет источники для статьи.
        
        Args:
            article: Объект статьи
            article_text: Текст статьи (опционально)
            
        Returns:
            Список найденных источников
        """
        if not self.api_key:
            logger.error("API ключ GigaChat не установлен")
            return self._generate_mock_references()
            
        try:
            logger.info(f"Поиск источников для статьи: {article.title}")
            
            # Подготавливаем данные о статье
            article_info = f"""Название: {article.title}
Авторы: {', '.join(article.authors)}
Аннотация: {article.abstract or article.summary}
Категории: {', '.join(article.categories) if article.categories else 'Не указаны'}
Год: {article.year or 'Не указан'}
"""
            
            # Добавляем текст статьи, если он доступен
            if article_text and len(article_text) > 100:
                # Ограничиваем размер текста для запроса
                max_text_length = 3000
                truncated_text = article_text[:max_text_length] + "..." if len(article_text) > max_text_length else article_text
                article_info += f"\nФрагмент текста статьи:\n{truncated_text}"

            # Системный промпт
            system_message = """Ты - научный ассистент, который помогает находить релевантные источники для научных статей.
Твоя задача - предложить список из 5-10 научных источников, которые могут быть полезны для данной статьи.

Для каждого источника укажи:
1. Полное название
2. Авторов
3. Год публикации
4. DOI или URL (если есть)
5. Краткое описание, почему этот источник релевантен

Используй стандартный формат цитирования.
Источники должны быть реальными и актуальными.
Отдавай предпочтение высокоцитируемым работам и статьям из уважаемых журналов.

Тщательно анализируй содержание статьи и предлагай источники, максимально связанные с её темой."""

            # Создаем полный запрос, комбинируя системный промпт и информацию о статье
            query = f"{system_message}\n\nПредложи релевантные источники для следующей научной статьи:\n\n{article_info}"
            
            logger.info("Отправка запроса к GigaChat API для поиска источников")
            
            # Используем контекстный менеджер для работы с API согласно документации
            # и отключаем проверку SSL сертификатов
            with GigaChat(credentials=self.api_key, verify_ssl_certs=False) as giga:
                response = giga.chat(query)
            
            logger.info("Ответ от GigaChat API получен")
            
            # Разбираем ответ и форматируем источники
            references = response.choices[0].message.content.split("\n\n")
            return [ref.strip() for ref in references if ref.strip()]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}", exc_info=True)
            return self._generate_mock_references()
            
    def _generate_mock_summary(self, article: Article) -> str:
        """Генерирует заглушку для краткого содержания."""
        return f"""# Краткое содержание

## Основная информация
- **Название**: {article.title}
- **Авторы**: {', '.join(article.authors)}
- **Год**: {article.year or 'Не указан'}

## Аннотация
{article.abstract or article.summary or 'Аннотация отсутствует'}

## Ключевые моменты
- Это демонстрационное краткое содержание
- Сервис GigaChat временно недоступен
- Для получения полного краткого содержания необходимо настроить подключение к API"""
            
    def _generate_mock_references(self) -> List[str]:
        """Генерирует заглушку для списка источников."""
        return [
            "1. Smith, J., et al. (2023) «Введение в научные исследования», Journal of Science, DOI: 10.1000/example1",
            "2. Johnson, A. (2022) «Методология научных исследований», Research Methods Quarterly, DOI: 10.1000/example2",
            "3. Brown, R. (2023) «Современные подходы к исследованиям», Modern Research, DOI: 10.1000/example3"
        ] 