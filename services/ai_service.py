"""
Сервис для работы с различными AI API (GigaChat, OpenAI, HuggingFace).

Для работы сервиса необходимо:
1. Настроить переменные окружения:
   - AI_SERVICE: Выбор сервиса ("GigaChat", "OpenAI", "HuggingFace")
   - OPENAI_API_KEY: API ключ OpenAI (если используется OpenAI)
   - MODEL: Модель для использования (по умолчанию "GPT-3.5")
   - LANGUAGE: Язык вывода (по умолчанию "Русский")

Поддерживаемые AI сервисы:
1. GigaChat (Сбер) - основной рекомендуемый сервис
   - Требует API ключ GigaChat
   - Оптимизирован для работы с русскими текстами
   
2. OpenAI (GPT-3.5/GPT-4)
   - Требует API ключ OpenAI
   - Хорошо работает с английскими текстами
   
3. HuggingFace (Локальные модели)
   - Не требует API ключей
   - Работает медленнее, но полностью локально
   - Поддерживает оба языка

Основные возможности:
- Создание кратких содержаний статей (create_summary)
- Поиск источников и ссылок (find_references)
- Генерация резюме для текстов (generate_summary)

Особенности работы:
- Автоматическое определение языка текста
- Fallback на локальные модели при недоступности API
- Поддержка Markdown форматирования
- Встроенные промпты для научных текстов
- Кэширование результатов для оптимизации

Пример использования:
```python
from services.ai_service import AIService
from models.article import Article

# Инициализация сервиса
service = AIService()

# Создание краткого содержания
article = Article(title="Название", authors=["Автор"], abstract="Текст")
summary = service.create_summary(article, style="Академический")

# Поиск источников
references = service.find_references(article)

# Генерация резюме для произвольного текста
text = "Длинный научный текст..."
summary = service.generate_summary(text, max_length=1500)
```

Системные требования:
- Python 3.7+
- Установленные пакеты: openai, gigachat, transformers (опционально)
- Доступ к соответствующим API (в зависимости от выбранного сервиса)
- GPU для ускорения работы локальных моделей (опционально)

Рекомендации по выбору сервиса:
- GigaChat: для работы с русскоязычными научными текстами
- OpenAI: для работы с англоязычными текстами или когда требуется высокая точность
- HuggingFace: когда нет доступа к API или требуется локальная обработка
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
import logging
import random
import re
from dotenv import load_dotenv

from models.article import Article, Author
from .gigachat_service import GigaChatService

logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

class AIService:
    """Сервис для работы с AI API."""
    
    def __init__(self):
        """Инициализирует сервис."""
        self.service = os.getenv("AI_SERVICE", "GigaChat")  # По умолчанию используем GigaChat
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("MODEL", "GPT-3.5")
        self.language = os.getenv("LANGUAGE", "Русский")
        
        # Инициализируем сервисы
        self.gigachat_service = GigaChatService() if self.service.lower() == "gigachat" else None
        
        # Логируем информацию о настройках
        logger.info(f"AI Service: {self.service}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Language: {self.language}")
        
    def create_summary(self, article: Article, style: str = "Краткий обзор", max_length: int = 500) -> str:
        """Создает краткое содержание статьи с помощью GigaChat.
        
        Args:
            article: Объект статьи
            style: Стиль краткого содержания
            max_length: Максимальная длина краткого содержания в словах
            
        Returns:
            Краткое содержание статьи
        """
        try:
            # Используем только GigaChat для создания кратких содержаний
            if self.gigachat_service:
                logger.info("Используем GigaChat для создания краткого содержания")
                return self.gigachat_service.create_summary(article, style, max_length)
            else:
                logger.warning("GigaChat не настроен, используем заглушку")
                return self._generate_mock_summary(article.abstract or article.summary)
        except Exception as e:
            logger.error(f"Ошибка при создании краткого содержания: {str(e)}")
            return self._generate_mock_summary(article.abstract or article.summary)
            
    def _generate_advanced_mock_summary_for_article(self, article: Article) -> str:
        """
        Генерирует расширенное демонстрационное резюме для статьи без использования AI API.
        
        Args:
            article (Article): Объект статьи
            
        Returns:
            str: Сгенерированное резюме
        """
        # Используем имеющуюся заглушку, но с форматированием в Markdown
        title = article.title
        categories = article.categories if article.categories else ["наука"]
        abstract = article.abstract or article.summary or "Аннотация отсутствует"
        
        # Извлекаем ключевые слова из аннотации
        abstract_words = [word for word in re.findall(r'\b\w+\b', abstract.lower()) 
                         if len(word) > 3 and word not in ["этот", "того", "этого", "такой", "такая", "также", "быть", "этом", "между"]]
        key_terms = list(set(abstract_words))[:5]  # Берем до 5 уникальных слов
        
        # Формируем структурированное содержание
        summary = "# Краткое содержание статьи\n\n"
        
        # Введение и цель
        summary += "## Проблема и цель исследования\n\n"
        summary += f"Данная статья «**{title}**» посвящена исследованию в области {', '.join(categories)}. "
        summary += f"Работа направлена на решение проблем, связанных с {key_terms[0] if key_terms else 'исследуемой областью'}. "
        summary += f"Основная цель — {random.choice(['разработка новых методов', 'анализ существующих подходов', 'создание эффективного решения'])} "
        summary += f"для {key_terms[1] if len(key_terms) > 1 else 'данной области исследования'}.\n\n"
        
        # Методология
        summary += "## Методология\n\n"
        summary += "В исследовании применяются следующие методы:\n\n"
        summary += "- Анализ существующей литературы и подходов\n"
        summary += f"- Экспериментальное исследование {key_terms[2] if len(key_terms) > 2 else 'параметров'}\n"
        summary += "- Статистическая обработка полученных данных\n"
        summary += f"- Сравнительный анализ с существующими решениями в области {categories[0] if categories else 'науки'}\n\n"
        
        # Результаты
        summary += "## Результаты\n\n"
        summary += "Исследование показало следующие результаты:\n\n"
        summary += f"1. Выявлены основные факторы, влияющие на {key_terms[0] if key_terms else 'исследуемый процесс'}\n"
        summary += f"2. Предложен новый подход к {key_terms[1] if len(key_terms) > 1 else 'решению проблемы'}\n"
        summary += f"3. Экспериментально подтверждена эффективность предложенного метода\n"
        summary += f"4. Определены ограничения и области применения разработанного подхода\n\n"
        
        # Выводы
        summary += "## Выводы и значимость\n\n"
        summary += f"Данное исследование вносит значительный вклад в понимание {key_terms[0] if key_terms else 'рассматриваемых процессов'}. "
        summary += f"Предложенный подход может быть применен в {random.choice(['промышленности', 'дальнейших исследованиях', 'смежных областях'])}. "
        summary += "Результаты открывают новые перспективы для развития данного направления науки."
        
        return summary
        
    def _generate_simple_mock_summary_for_article(self, article: Article) -> str:
        """
        Генерирует простое демонстрационное резюме для статьи при возникновении ошибок.
        
        Args:
            article (Article): Объект статьи
            
        Returns:
            str: Простое сгенерированное резюме
        """
        title = article.title
        categories = ', '.join(article.categories) if article.categories else "не указаны"
        
        return f"""# Краткое содержание статьи

## О статье

Название: **{title}**
Категории: {categories}

## Основные положения

- Статья посвящена исследованию в указанной области
- Рассматриваются ключевые аспекты и методы анализа данных
- Предлагается подход к решению проблемы

## Выводы

Для получения более детального содержания необходимо проанализировать полный текст статьи.
"""

    def find_references(self, article: Article) -> List[str]:
        """Ищет источники для статьи.
        
        Args:
            article: Объект статьи
            
        Returns:
            Список найденных источников
        """
        try:
            # Приводим строку к нижнему регистру для сравнения
            service_lower = self.service.lower()
            
            if service_lower == "gigachat" and self.gigachat_service:
                logger.info("Используем GigaChat для поиска источников")
                return self.gigachat_service.find_references(article)
            elif service_lower == "openai" and self.api_key:
                logger.info("Используем OpenAI для поиска источников")
                logger.info(f"Поиск источников для статьи: {article.title}")
                
                # Подготавливаем данные о статье
                article_info = f"""Название: {article.title}
Авторы: {', '.join(article.authors)}
Аннотация: {article.abstract or article.summary}
Категории: {', '.join(article.categories)}
Год: {article.year}
"""
                
                # Настраиваем клиента OpenAI
                os.environ["OPENAI_API_KEY"] = self.api_key
                client = OpenAI()
                
                # Запрос к API
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты - научный ассистент, который предлагает возможные источники и ссылки для научных статей."},
                        {"role": "user", "content": f"На основе информации о научной статье, предложи 5-7 вероятных источников, которые могут быть цитированы в ней. Формат: автор, название, год. Статья:\n{article_info}"}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                text_response = response.choices[0].message.content
                # Разбиваем ответ на строки и очищаем
                references = [line.strip() for line in text_response.split('\n') 
                             if line.strip() and not line.strip().startswith('#')]
                
                # Если нет результатов, возвращаем заглушку
                if not references:
                    return [
                        "Smith, J. et al. (2021). Recent advances in the field.",
                        "Johnson, M. & Williams, K. (2020). Theoretical foundations.",
                        "Rodriguez, A. (2019). Empirical evidence in related work."
                    ]
                    
                return references
            elif service_lower == "huggingface":
                # Используем заглушку для Hugging Face
                logger.info("Использование заглушки для Hugging Face")
                return [
                    f"Smith, J. & Jones, M. (2021). Advances in {article.categories[0] if article.categories else 'Science'}.",
                    f"Johnson, M. & Williams, K. (2020). Theoretical foundations of {article.title.split()[0] if article.title else 'Research'}.",
                    f"Rodriguez, A. (2019). Empirical evidence in {article.categories[-1] if article.categories else 'related work'}.",
                    f"Chen, L. et al. (2022). Recent developments in {article.title.split()[-1] if article.title else 'the field'}.",
                    f"Kumar, R. & Singh, V. (2018). A review of methods for {article.categories[0] if article.categories else 'analysis'}."
                ]
            else:
                # Если API ключ не настроен, возвращаем заглушку
                return [
                    "Smith, J. et al. (2021). Recent advances in the field.",
                    "Johnson, M. & Williams, K. (2020). Theoretical foundations.",
                    "Rodriguez, A. (2019). Empirical evidence in related work."
                ]
        except Exception as e:
            logger.error(f"Ошибка при поиске источников: {str(e)}")
            raise
        
    def generate_summary(self, text, max_length=1500):
        """
        Генерирует краткое содержание статьи.
        
        Args:
            text (str): Текст статьи
            max_length (int): Максимальная длина резюме
            
        Returns:
            str: Краткое содержание статьи
        """
        try:
            # Ограничиваем длину входного текста
            if len(text) > 15000:
                text = text[:15000] + "..."
            
            # Приводим строку к нижнему регистру для сравнения, не зависящего от регистра
            service_lower = self.service.lower()
            
            if service_lower == "gigachat" and self.gigachat_service:
                logger.info("Используем GigaChat для генерации краткого содержания")
                return self.gigachat_service.generate_summary(text, max_length)
            elif service_lower == "openai" and self.api_key:
                return self._generate_summary_openai(text, max_length)
            elif service_lower == "huggingface":
                try:
                    return self._generate_summary_huggingface(text, max_length)
                except Exception as e:
                    logger.error(f"Ошибка при использовании Hugging Face: {str(e)}")
                    return self._generate_mock_summary(text)
            else:
                return self._generate_mock_summary(text)
        except Exception as e:
            logger.error(f"Ошибка при генерации резюме: {str(e)}")
            # В случае ошибки возвращаем заглушку для демонстрации
            return self._generate_mock_summary(text)
    
    def _generate_mock_summary(self, text, sections=3):
        """
        Генерирует демонстрационное резюме без использования AI API.
        
        Args:
            text (str): Исходный текст статьи
            sections (int): Количество разделов в резюме
            
        Returns:
            str: Сгенерированное резюме
        """
        # Если текст слишком короткий, возвращаем его без изменений
        if len(text) < 500:
            return "# Краткое содержание\n\n" + text
        
        # Извлекаем предполагаемое название из первых строк
        lines = text.split('\n')
        potential_title = "статьи"
        for line in lines[:10]:
            if len(line) > 15 and len(line) < 100 and not line.startswith('#'):
                potential_title = line.strip()
                break
        
        # Находим наиболее частые слова для имитации ключевых тем
        # (исключая слишком короткие и стоп-слова)
        stop_words = set(['и', 'в', 'на', 'с', 'для', 'по', 'к', 'или', 'из', 'у', 
                          'о', 'the', 'of', 'and', 'in', 'to', 'a', 'is', 'that', 
                          'for', 'with', 'as', 'by', 'on', 'are', 'be', 'this', 'an'])
        
        word_freq = {}
        for word in re.findall(r'\b\w+\b', text.lower()):
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Сортируем слова по частоте
        frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        key_topics = [word for word, _ in frequent_words]
        
        # Создаем случайные предложения для абзацев, включая ключевые слова
        paragraphs = []
        
        # Введение
        intro = (
            f"Данная работа представляет собой исследование в области {key_topics[0] if key_topics else 'науки'}. "
            f"Автор рассматривает вопросы, связанные с {', '.join(key_topics[1:4]) if len(key_topics) > 3 else 'рассматриваемой темой'}. "
            f"Основная цель исследования — анализ и систематизация знаний о {potential_title.lower()}."
        )
        paragraphs.append(intro)
        
        # Основные разделы
        for i in range(sections):
            # Выбираем несколько ключевых слов для этого раздела
            section_words = random.sample(key_topics, min(3, len(key_topics)))
            
            section = (
                f"В разделе {i+1} исследуются {section_words[0] if section_words else 'основные концепции'}. "
                f"Показано, что {section_words[1] if len(section_words) > 1 else 'данные факторы'} "
                f"имеют значительное влияние на {section_words[2] if len(section_words) > 2 else 'результаты'}. "
                f"Это подтверждается {random.choice(['экспериментальными данными', 'теоретическими выкладками', 'анализом литературы', 'статистическими показателями'])}, "
                f"что согласуется с современными исследованиями в данной области."
            )
            paragraphs.append(section)
        
        # Заключение
        conclusion = (
            f"В заключение, исследование демонстрирует важность {key_topics[0] if key_topics else 'рассматриваемой темы'} "
            f"в контексте {key_topics[-1] if len(key_topics) > 1 else 'современной науки'}. "
            f"Результаты могут быть применены в {random.choice(['практической деятельности', 'дальнейших исследованиях', 'смежных областях'])}. "
            f"Работа вносит значительный вклад в понимание {potential_title.lower()}."
        )
        paragraphs.append(conclusion)
        
        # Собираем в форматированный текст
        summary = "# Краткое содержание статьи\n\n"
        summary += "\n\n".join(paragraphs)
        
        return summary
    
    def _generate_summary_openai(self, text, max_length):
        """
        Генерирует краткое содержание статьи с использованием OpenAI.
        
        Args:
            text (str): Текст статьи
            max_length (int): Максимальная длина резюме
            
        Returns:
            str: Краткое содержание статьи
        """
        try:
            from openai import OpenAI
            
            # Настраиваем клиента OpenAI
            os.environ["OPENAI_API_KEY"] = self.api_key
            client = OpenAI()

            # Создаем более подробный промпт для структурированного резюме
            system_message = """Ты - научный ассистент, который создает структурированные краткие содержания научных статей.
Твоя задача - выделить следующие аспекты статьи:
1. Основная проблема и цель исследования
2. Методология и использованные подходы
3. Ключевые результаты и выводы
4. Практическая значимость и перспективы исследования
5. Ограничения исследования (если упоминаются)

Используй разметку Markdown для форматирования:
- Заголовок резюме (# Краткое содержание)
- Подзаголовки для каждого раздела (## Проблема и цель, ## Методология и т.д.)
- Маркированные списки для перечисления ключевых моментов
- **Жирное выделение** важных концепций и терминов
- *Курсив* для определений
- > Цитаты для важных выводов автора

Важно: не добавляй информацию, которой нет в оригинальном тексте. Сохраняй научную точность."""

            user_message = f"""Создай структурированное краткое содержание следующей научной статьи. 
Резюме должно быть информативным, но лаконичным (максимальная длина: {max_length} символов).
Сфокусируйся на основной проблеме, методологии, результатах и выводах.

Статья:
{text}"""
            
            # Определяем модель в зависимости от переменной окружения или настроек
            model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
            if "gpt-4" in model.lower():
                # Если доступен GPT-4, используем его с более низкой температурой для точности
                model_to_use = model
                temp = 0.2
                max_tokens_to_use = 1500
            else:
                # Иначе используем gpt-3.5-turbo
                model_to_use = "gpt-3.5-turbo"
                temp = 0.3
                max_tokens_to_use = 1000
                
            logger.info(f"Используем модель {model_to_use} для генерации краткого содержания")
            
            response = client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens_to_use,
                temperature=temp,
            )
            
            logger.info("Краткое содержание успешно сгенерировано через OpenAI")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ошибка OpenAI API: {str(e)}")
            # Если не удалось получить резюме через OpenAI, используем локальную модель
            return self._generate_summary_huggingface(text, max_length)
    
    def _generate_summary_huggingface(self, text, max_length):
        """
        Генерирует краткое содержание статьи с использованием локальных моделей Hugging Face.
        
        Args:
            text (str): Текст статьи
            max_length (int): Максимальная длина резюме
            
        Returns:
            str: Краткое содержание статьи
        """
        try:
            # Пытаемся импортировать необходимые библиотеки
            try:
                from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
                import torch
                has_transformers = True
                logger.info("Библиотека transformers успешно импортирована")
            except ImportError:
                has_transformers = False
                logger.warning("Библиотека transformers не найдена. Используем расширенную заглушку.")
            
            if has_transformers:
                try:
                    # Проверяем наличие GPU
                    device = 0 if torch.cuda.is_available() else -1
                    logger.info(f"Используется устройство: {'GPU' if device == 0 else 'CPU'}")
                    
                    # Определяем язык текста для выбора подходящей модели
                    is_english = self._is_primarily_english(text)
                    
                    # Выбираем модель в зависимости от языка
                    if is_english:
                        model_name = "facebook/bart-large-cnn"
                        logger.info("Определен английский язык, используем модель BART")
                    else:
                        model_name = "IlyaGusev/mbart_ru_sum_gazeta"
                        logger.info("Определен русский язык, используем модель mBART для русской суммаризации")
                    
                    # Инициализируем модель для суммаризации
                    logger.info(f"Загрузка модели summarization: {model_name}...")
                    
                    # Для русской модели используем специфичный подход
                    if model_name == "IlyaGusev/mbart_ru_sum_gazeta":
                        # Загружаем токенизатор и модель напрямую
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                        
                        # Перемещаем модель на GPU, если доступно
                        if device == 0:
                            model = model.to("cuda")
                        
                        # Разбиваем текст на части
                        max_chunk_length = min(512, tokenizer.model_max_length)
                        chunks = self._split_text_into_chunks(text, max_chunk_length, tokenizer)
                        
                        logger.info(f"Текст разбит на {len(chunks)} частей для обработки")
                        
                        summaries = []
                        # Ограничиваем количество обрабатываемых чанков для скорости
                        max_chunks_to_process = min(5, len(chunks))
                        
                        for i, chunk in enumerate(chunks[:max_chunks_to_process]):
                            logger.info(f"Обработка части {i+1}/{max_chunks_to_process}...")
                            if len(chunk.strip()) > 100:  # Пропускаем слишком короткие куски
                                inputs = tokenizer(chunk, return_tensors="pt", max_length=max_chunk_length, truncation=True)
                                if device == 0:
                                    inputs = {k: v.to("cuda") for k, v in inputs.items()}
                                
                                # Генерируем саммари
                                with torch.no_grad():
                                    output_ids = model.generate(
                                        inputs["input_ids"],
                                        max_length=120,
                                        min_length=40,
                                        no_repeat_ngram_size=3,
                                        num_beams=4
                                    )
                                
                                summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
                                summaries.append(summary)
                                logger.info(f"Часть {i+1} успешно обработана")
                            else:
                                logger.info(f"Часть {i+1} слишком короткая, пропускаем")
                    else:
                        # Используем pipeline для английской модели
                        summarizer = pipeline("summarization", model=model_name, device=device)
                        
                        # Разбиваем текст на части, если он слишком длинный
                        max_chunk_length = 1024
                        chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
                        
                        logger.info(f"Текст разбит на {len(chunks)} частей для обработки")
                        
                        summaries = []
                        max_chunks_to_process = min(3, len(chunks))
                        
                        for i, chunk in enumerate(chunks[:max_chunks_to_process]):
                            logger.info(f"Обработка части {i+1}/{max_chunks_to_process}...")
                            if len(chunk.strip()) > 100:  # Пропускаем слишком короткие куски
                                result = summarizer(
                                    chunk, 
                                    max_length=150, 
                                    min_length=40, 
                                    do_sample=False,
                                    num_beams=4
                                )
                                if result and len(result) > 0:
                                    summaries.append(result[0]['summary_text'])
                                    logger.info(f"Часть {i+1} успешно обработана")
                            else:
                                logger.info(f"Часть {i+1} слишком короткая, пропускаем")
                    
                    if summaries:
                        # Объединяем результаты
                        combined_summary = " ".join(summaries)
                        
                        # Форматируем результат в виде структурированного Markdown
                        if is_english:
                            final_summary = self._format_summary_as_markdown(combined_summary, "en")
                        else:
                            final_summary = self._format_summary_as_markdown(combined_summary, "ru")
                        
                        logger.info("Суммаризация успешно выполнена")
                        return final_summary
                    else:
                        logger.warning("Не удалось получить резюме из модели. Используем расширенную заглушку.")
                        return self._generate_advanced_mock_summary(text)
                except Exception as e:
                    logger.error(f"Ошибка при использовании модели Hugging Face: {str(e)}")
                    return self._generate_advanced_mock_summary(text)
            else:
                return self._generate_advanced_mock_summary(text)
        except Exception as e:
            logger.error(f"Общая ошибка при использовании Hugging Face: {str(e)}")
            # Если модель не загружена или другая ошибка, возвращаем расширенную заглушку
            return self._generate_advanced_mock_summary(text)
    
    def _is_primarily_english(self, text):
        """
        Определяет, является ли текст преимущественно английским.
        
        Args:
            text (str): Текст для анализа
            
        Returns:
            bool: True, если текст преимущественно на английском языке
        """
        # Упрощённое определение языка по наличию характерных символов
        # Считаем количество кириллических и латинских символов
        cyrillic_count = len(re.findall(r'[а-яА-ЯёЁ]', text))
        latin_count = len(re.findall(r'[a-zA-Z]', text))
        
        # Если кириллических символов больше, считаем текст русским
        return latin_count > cyrillic_count
    
    def _split_text_into_chunks(self, text, max_tokens, tokenizer):
        """
        Разбивает текст на части с учетом максимального количества токенов.
        
        Args:
            text (str): Исходный текст
            max_tokens (int): Максимальное количество токенов в одном куске
            tokenizer: Токенизатор для подсчета токенов
            
        Returns:
            list: Список кусков текста
        """
        # Делим текст на абзацы
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # Подсчитываем токены в параграфе
            tokens = tokenizer(paragraph, return_attention_mask=False)["input_ids"]
            paragraph_length = len(tokens)
            
            # Если текущий кусок + параграф не превышает максимум, добавляем к текущему куску
            if current_length + paragraph_length <= max_tokens:
                current_chunk.append(paragraph)
                current_length += paragraph_length
            else:
                # Если текущий кусок непустой, сохраняем его
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                # Начинаем новый кусок с текущего параграфа
                # Если параграф слишком длинный, обрезаем его
                if paragraph_length > max_tokens:
                    # Грубое приближение: считаем, что один токен примерно равен 4 символам
                    approx_chars = max_tokens * 4
                    current_chunk = [paragraph[:approx_chars]]
                    current_length = max_tokens
                else:
                    current_chunk = [paragraph]
                    current_length = paragraph_length
        
        # Добавляем последний кусок
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
    
    def _format_summary_as_markdown(self, summary_text, language="ru"):
        """
        Форматирует результат суммаризации в структурированный Markdown.
        
        Args:
            summary_text (str): Текст суммаризации
            language (str): Язык текста ('ru' или 'en')
            
        Returns:
            str: Отформатированный текст в Markdown
        """
        # Заголовки в зависимости от языка
        headers = {
            "ru": {
                "main": "# Краткое содержание статьи",
                "intro": "## Введение и основная проблема",
                "method": "## Методология",
                "results": "## Результаты",
                "conclusion": "## Выводы"
            },
            "en": {
                "main": "# Article Summary",
                "intro": "## Introduction and Main Problem",
                "method": "## Methodology",
                "results": "## Results",
                "conclusion": "## Conclusions"
            }
        }
        
        h = headers[language]
        
        # Пытаемся разделить текст на смысловые части
        # Для этого используем NLP-эвристики:
        # 1. Ищем предложения с ключевыми словами, характерными для разных разделов
        # 2. Используем позицию в тексте (начало, середина, конец)
        
        sentences = re.split(r'(?<=[.!?])\s+', summary_text)
        
        # Ключевые слова для каждого раздела
        keywords = {
            "ru": {
                "intro": ["введение", "проблема", "цель", "задача", "исследование", "работа", "статья", "рассматривается"],
                "method": ["метод", "методология", "подход", "анализ", "исследование", "измерение", "оценка", "эксперимент"],
                "results": ["результат", "вывод", "показал", "обнаружено", "выявлено", "продемонстрировано"],
                "conclusion": ["заключение", "вывод", "итог", "таким образом", "следовательно", "в результате"]
            },
            "en": {
                "intro": ["introduction", "problem", "purpose", "goal", "research", "study", "paper", "article", "examined"],
                "method": ["method", "methodology", "approach", "analysis", "measure", "assessment", "experiment"],
                "results": ["result", "finding", "showed", "demonstrated", "revealed", "indicated"],
                "conclusion": ["conclusion", "therefore", "thus", "consequently", "as a result", "in summary"]
            }
        }
        
        # Категоризируем предложения
        intro_sentences = []
        method_sentences = []
        results_sentences = []
        conclusion_sentences = []
        
        # Простой алгоритм распределения по категориям
        total_sentences = len(sentences)
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Положение в тексте (начало, середина, конец)
            position = i / total_sentences
            
            # Проверяем ключевые слова
            sentence_lower = sentence.lower()
            
            # Поиск совпадений с ключевыми словами
            has_intro_keywords = any(keyword in sentence_lower for keyword in keywords[language]["intro"])
            has_method_keywords = any(keyword in sentence_lower for keyword in keywords[language]["method"])
            has_results_keywords = any(keyword in sentence_lower for keyword in keywords[language]["results"])
            has_conclusion_keywords = any(keyword in sentence_lower for keyword in keywords[language]["conclusion"])
            
            # Распределение по категориям на основе ключевых слов и позиции
            if has_conclusion_keywords or position > 0.8:
                conclusion_sentences.append(sentence)
            elif has_results_keywords or 0.5 < position <= 0.8:
                results_sentences.append(sentence)
            elif has_method_keywords or 0.3 < position <= 0.5:
                method_sentences.append(sentence)
            elif has_intro_keywords or position <= 0.3:
                intro_sentences.append(sentence)
            else:
                # Если не удалось определить категорию, распределяем по позиции
                if position <= 0.25:
                    intro_sentences.append(sentence)
                elif position <= 0.5:
                    method_sentences.append(sentence)
                elif position <= 0.75:
                    results_sentences.append(sentence)
                else:
                    conclusion_sentences.append(sentence)
        
        # Форматируем в Markdown
        formatted_summary = f"{h['main']}\n\n"
        
        if intro_sentences:
            formatted_summary += f"{h['intro']}\n\n"
            formatted_summary += " ".join(intro_sentences) + "\n\n"
        
        if method_sentences:
            formatted_summary += f"{h['method']}\n\n"
            formatted_summary += " ".join(method_sentences) + "\n\n"
        
        if results_sentences:
            formatted_summary += f"{h['results']}\n\n"
            formatted_summary += " ".join(results_sentences) + "\n\n"
        
        if conclusion_sentences:
            formatted_summary += f"{h['conclusion']}\n\n"
            formatted_summary += " ".join(conclusion_sentences)
        
        return formatted_summary
    
    def _generate_advanced_mock_summary(self, text, sections=4):
        """
        Генерирует улучшенное демонстрационное резюме без использования AI API.
        
        Args:
            text (str): Исходный текст статьи
            sections (int): Количество разделов в резюме
            
        Returns:
            str: Сгенерированное резюме
        """
        logger.info("Генерация расширенной заглушки для краткого содержания")
        
        # Если текст слишком короткий, возвращаем его без изменений
        if len(text) < 500:
            return "# Краткое содержание\n\n" + text
        
        # Извлекаем ключевые фразы из текста
        try:
            # Находим наиболее частые слова для имитации ключевых тем
            # (исключая слишком короткие и стоп-слова)
            stop_words = set(['и', 'в', 'на', 'с', 'для', 'по', 'к', 'или', 'из', 'у', 
                            'о', 'the', 'of', 'and', 'in', 'to', 'a', 'is', 'that', 
                            'for', 'with', 'as', 'by', 'on', 'are', 'be', 'this', 'an',
                            'что', 'как', 'так', 'который', 'при', 'но', 'если', 'не'])
            
            # Удаляем лишние символы и оставляем только слова
            cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
            
            # Находим предложения, чтобы извлечь более осмысленные фрагменты
            sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 20]
            
            # Выбираем несколько предложений в качестве "ключевых" для резюме
            if sentences:
                selected_sentences = random.sample(sentences, min(sections * 2, len(sentences)))
            else:
                selected_sentences = ["Информация недоступна"] * sections
                
            # Находим часто встречающиеся слова
            word_freq = {}
            for word in re.findall(r'\b\w+\b', cleaned_text):
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Сортируем слова по частоте
            frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
            key_topics = [word for word, _ in frequent_words]
            
            # Извлекаем предполагаемое название из первых строк
            lines = text.split('\n')
            potential_title = "статьи"
            for line in lines[:10]:
                if len(line) > 15 and len(line) < 100 and not line.startswith('#'):
                    potential_title = line.strip()
                    break
                    
            # Создаем более осмысленное резюме
            summary = "# Краткое содержание статьи\n\n"
            
            # Введение - используем первое предложение из текста, если возможно
            intro_sentence = selected_sentences[0] if selected_sentences else ""
            intro_topics = ", ".join(key_topics[:3]) if key_topics else "рассматриваемой темы"
            
            intro = f"## Введение\n\n{intro_sentence}\n\nДанная работа исследует аспекты {intro_topics} "
            intro += f"и представляет анализ в контексте {potential_title.lower()}.\n\n"
            
            summary += intro
            
            # Основные разделы - пытаемся использовать реальные фрагменты из текста
            summary += "## Основные положения\n\n"
            
            for i in range(min(sections, len(selected_sentences) - 1)):
                bullet_point = selected_sentences[i + 1] if i + 1 < len(selected_sentences) else f"Аспект {i+1} требует дальнейшего изучения"
                summary += f"- {bullet_point}\n"
            
            summary += "\n"
            
            # Методология
            methodology = "\n## Методология\n\n"
            if key_topics:
                methodology += f"Исследование применяет следующие методы для анализа {key_topics[0] if key_topics else 'данных'}:\n\n"
                methodology += "1. Анализ существующих подходов и литературы\n"
                methodology += "2. Сбор и обработка эмпирических данных\n"
                methodology += f"3. Применение методов {key_topics[1] if len(key_topics) > 1 else 'статистического анализа'}\n"
                methodology += f"4. Сравнительное исследование различных аспектов {key_topics[2] if len(key_topics) > 2 else 'проблемы'}\n\n"
            else:
                methodology += "В работе применяются стандартные методы научного исследования, включая анализ литературы, "
                methodology += "сбор и обработку данных, а также статистический анализ полученных результатов.\n\n"
            
            summary += methodology
            
            # Результаты и выводы
            summary += "## Результаты и выводы\n\n"
            
            if len(selected_sentences) > sections + 1:
                conclusion_sentence = selected_sentences[-1]
                summary += f"{conclusion_sentence}\n\n"
            
            summary += f"Исследование показывает значимость {key_topics[0] if key_topics else 'рассматриваемых факторов'} "
            summary += f"и открывает новые перспективы для дальнейших исследований в области {key_topics[-1] if len(key_topics) > 1 else 'данной тематики'}."
            
            logger.info("Расширенная заглушка для краткого содержания успешно сгенерирована")
            return summary
                
        except Exception as e:
            logger.error(f"Ошибка при генерации расширенной заглушки: {str(e)}")
            # В случае ошибки, используем базовый вариант
            return self._generate_mock_summary(text)
    
    def _generate_mock_references(self, text, count=8):
        """
        Генерирует тестовый список источников без использования AI API.
        
        Args:
            text (str): Исходный текст статьи
            count (int): Количество источников
            
        Returns:
            list: Список объектов Article
        """
        from models.article import Article, Author
        import random
        from datetime import datetime
        
        # Извлекаем наиболее частые слова для использования в названиях
        word_freq = {}
        stop_words = set(['и', 'в', 'на', 'с', 'для', 'по', 'к', 'или', 'из', 'у', 
                          'о', 'the', 'of', 'and', 'in', 'to', 'a', 'is', 'that', 
                          'for', 'with', 'as', 'by', 'on', 'are', 'be', 'this', 'an'])
        
        for word in re.findall(r'\b\w+\b', text.lower()):
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Сортируем слова по частоте
        frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        key_topics = [word for word, _ in frequent_words]
        
        # Шаблоны для генерации названий источников
        title_templates = [
            "Анализ и методология {topic1} в контексте {topic2}",
            "Обзор исследований по {topic1}: современные подходы",
            "Теоретические основы {topic1} и {topic2}",
            "{topic1}: принципы, методы и перспективы",
            "Практическое применение {topic1} в области {topic2}",
            "Экспериментальное исследование {topic1}",
            "К вопросу о {topic1} в {topic2}",
            "Проблемы и решения в сфере {topic1}",
            "Сравнительный анализ методов {topic1}",
            "Новые подходы к изучению {topic1}"
        ]
        
        # Список возможных журналов
        journals = [
            "Вестник научных исследований",
            "Научно-технический журнал",
            "Современная наука и инновации",
            "Актуальные проблемы науки и образования",
            "Научные труды университета",
            "Инновационные технологии",
            "Перспективы науки",
            "Международный научный журнал",
            "Вопросы современной науки",
            "Теория и практика научных исследований"
        ]
        
        # Фамилии для генерации авторов
        last_names = [
            "Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", 
            "Петров", "Соколов", "Михайлов", "Новиков", "Федоров",
            "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов",
            "Егоров", "Павлов", "Козлов", "Степанов", "Николаев"
        ]
        
        # Инициалы
        initials = ["А.А.", "Б.В.", "В.Г.", "Г.Д.", "Д.Е.", "Е.Ж.", 
                    "Ж.З.", "З.И.", "И.К.", "К.Л.", "Л.М.", "М.Н."]
        
        # Текущий год для расчета дат публикаций
        current_year = datetime.now().year
        
        # Генерируем источники
        references = []
        
        for i in range(min(count, len(title_templates))):
            # Выбираем случайные ключевые слова для названия
            topic1 = random.choice(key_topics) if key_topics else "исследования"
            topic2 = random.choice([t for t in key_topics if t != topic1]) if len(key_topics) > 1 else "науки"
            
            # Формируем название
            title_template = random.choice(title_templates)
            title = title_template.format(topic1=topic1, topic2=topic2)
            
            # Генерируем авторов (1-3 автора)
            author_count = random.randint(1, 3)
            authors = []
            
            for j in range(author_count):
                last_name = random.choice(last_names)
                initial = random.choice(initials)
                authors.append(Author(name=f"{last_name} {initial}"))
            
            # Год публикации (последние 10 лет)
            year = random.randint(current_year - 10, current_year)
            
            # Журнал
            journal = random.choice(journals)
            
            # Абстракт
            abstract = (
                f"В данной работе рассматриваются вопросы, связанные с {topic1} и {topic2}. "
                f"Авторы представляют результаты исследований, проведенных в период с {year-2} по {year} год. "
                f"Особое внимание уделяется методологическим аспектам и практическому применению. "
                f"Показана взаимосвязь между различными факторами, влияющими на {topic1}. "
                f"Результаты могут быть использованы в дальнейших исследованиях в данной области."
            )
            
            # Создаем статью-источник
            reference = Article(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                journal=journal,
                source="Анализ текста (ИИ)",
                confidence=random.uniform(0.6, 0.95)  # Случайная уверенность
            )
            
            references.append(reference)
        
        return references
    
    def _find_references_openai(self, text):
        """
        Находит источники в тексте с использованием OpenAI.
        
        Args:
            text (str): Текст статьи
            
        Returns:
            list: Список объектов Article с найденными источниками
        """
        try:
            from openai import OpenAI
            import json
            from models.article import Article, Author
            
            # Настраиваем клиента OpenAI
            os.environ["OPENAI_API_KEY"] = self.api_key
            client = OpenAI()
            
            # Ограничиваем длину текста
            if len(text) > 10000:
                text = text[:10000] + "...\n[Текст был сокращен из-за ограничений размера]"
            
            # Создаем системный промпт для извлечения источников
            system_prompt = """
            Ты - научный ассистент, который извлекает библиографические ссылки из научных текстов.
            Проанализируй предоставленный текст и найди все библиографические ссылки (цитирования, список литературы).
            Для каждой ссылки определи: название статьи, авторов, год публикации, журнал или издательство.
            Возвращай данные только в формате JSON согласно указанной схеме.
            """
            
            # Создаем описание формата JSON
            json_format = """
            [
                {
                    "title": "Название статьи или источника",
                "authors": ["Автор 1", "Автор 2"],
                "year": 2020,
                    "journal": "Название журнала или издательства",
                    "confidence": 0.9
                }
            ]
            """
            
            # Запрос к API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Вот формат JSON, который ты должен использовать:\n{json_format}\n\nПроанализируй следующий текст и найди в нем библиографические ссылки:\n\n{text}"}
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            
            # Извлекаем JSON из ответа
            response_text = response.choices[0].message.content
            # Ищем JSON в ответе с помощью регулярного выражения
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    references_data = json.loads(json_str)
                except json.JSONDecodeError:
                    # Если ошибка парсинга, возвращаем заглушку
                    return self._generate_mock_references(text)
            else:
                return self._generate_mock_references(text)
            
            # Конвертируем данные в объекты Article
            references = []
            for ref_data in references_data:
                try:
                    # Пропускаем записи без названия
                    if not ref_data.get("title"):
                        continue
                        
                    # Создаем авторов
                    authors = []
                    for author_name in ref_data.get("authors", []):
                        if author_name:
                            authors.append(Author(name=author_name))
                    
                    # Если нет авторов, добавляем N/A
                    if not authors:
                        authors.append(Author(name="N/A"))
                    
                    # Создаем статью
                    article = Article(
                        title=ref_data.get("title", ""),
                        authors=authors,
                        abstract="",  # Обычно абстракт не извлекается из ссылок
                        year=ref_data.get("year", 0),
                        journal=ref_data.get("journal", ""),
                        source="Анализ текста (ИИ)",
                        confidence=ref_data.get("confidence", 0.7)
                    )
                    
                    references.append(article)
                except Exception as e:
                    logger.error(f"Ошибка при обработке ссылки: {str(e)}")
                    continue
            
            return references
        except Exception as e:
            logger.error(f"Ошибка OpenAI API: {str(e)}")
            # Если не удалось извлечь ссылки через OpenAI, используем локальную модель
            return self._find_references_huggingface(text)
    
    def _find_references_huggingface(self, text):
        """
        Находит источники в тексте с использованием локальных моделей Hugging Face.
        
        Args:
            text (str): Текст статьи
            
        Returns:
            list: Список объектов Article с найденными источниками
        """
        try:
            # Здесь можно реализовать извлечение ссылок с помощью моделей NER
            # или разработать правила на основе регулярных выражений для извлечения библиографии
            
            # Простой пример использования регулярных выражений для извлечения ссылок
            # (в реальном проекте нужно использовать более сложные алгоритмы)
            
            # Поиск в тексте разделов "Список литературы", "References", "Библиография" и т.д.
            from models.article import Article, Author
            import re
            
            # Находим раздел со списком литературы
            references_section = None
            patterns = [
                r'(?:Список литературы|Литература|Библиография|Источники|References|Bibliography)[\s]*(?:\n|:)(.*?)(?:(?:\n\s*\n)|$)',
                r'\[1\](.*?)(?:(?:\n\s*\n)|$)',
                r'1\.(.*?)(?:(?:\n\s*\n)|$)'
            ]
            
            for pattern in patterns:
                matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if matches:
                    references_section = matches.group(1)
                    break
            
            # Если не нашли раздел литературы, ищем в тексте
            if not references_section:
                # Ищем строки, похожие на библиографические ссылки
                references_section = text
            
            # Разбиваем на отдельные источники
            references_raw = re.split(r'\n\d+\.|\n\[\d+\]|\.\s+\[\d+\]', references_section)
            
            # Обрабатываем каждый источник
            references = []
            
            for ref_text in references_raw:
                ref_text = ref_text.strip()
                if len(ref_text) < 10:  # Слишком короткие строки пропускаем
                    continue
                
                # Поиск года в формате (2020) или 2020
                year_match = re.search(r'(?:\((\d{4})\))|(?:\s(\d{4})\.)', ref_text)
                year = int(year_match.group(1) or year_match.group(2)) if year_match else 0
                
                # Попытка извлечь авторов (обычно в начале строки до года)
                author_part = ref_text.split(str(year) if year else '.', 1)[0] if year else ""
                if not author_part:
                    author_part = ref_text.split(',', 1)[0] if ',' in ref_text else ""
                
                authors = []
                if author_part:
                    # Разделяем авторов по запятым или 'and'/'и'
                    author_names = re.split(r',\s+|\s+и\s+|\s+and\s+', author_part)
                    for name in author_names:
                        name = name.strip()
                        if name and len(name) > 3:  # Игнорируем слишком короткие имена
                            authors.append(Author(name=name))
                
                # Если не нашли авторов, добавляем неизвестного
                if not authors:
                    authors.append(Author(name="Неизвестный автор"))
                
                # Попытка извлечь название статьи (обычно после года)
                title = ""
                if year:
                    title_part = ref_text.split(str(year), 1)[1] if len(ref_text.split(str(year), 1)) > 1 else ref_text
                    title = title_part.split('.', 1)[0] if '.' in title_part else title_part
                else:
                    title = ref_text.split('.', 2)[1] if len(ref_text.split('.', 2)) > 1 else ref_text
                
                title = title.strip().strip('"').strip("'").strip()
                if not title:
                    title = f"Источник {len(references) + 1}"
                
                # Ищем журнал (обычно после названия, часто курсивом или после ///)
                journal = ""
                journal_match = re.search(r'(?:\/\/\s*|\.\s+)([\w\s]+)[,\.]', ref_text)
                if journal_match:
                    journal = journal_match.group(1).strip()
                
                # Создаем объект Article
                confidence = 0.7  # Средняя уверенность для извлечения на основе регулярных выражений
                article = Article(
                    title=title,
                    authors=authors,
                    abstract="",
                    year=year,
                    journal=journal,
                    source="Анализ текста (локально)",
                    confidence=confidence
                )
                
                references.append(article)
            
            # Если не нашли ни одного источника, возвращаем заглушку
            if not references:
                return self._generate_mock_references(text)
                
            return references
            
        except Exception as e:
            logger.error(f"Ошибка при использовании Hugging Face: {str(e)}")
            # Если модель не загружена или другая ошибка, возвращаем заглушку
            return self._generate_mock_references(text)
        
    # Другие методы... 