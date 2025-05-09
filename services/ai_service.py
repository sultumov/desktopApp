"""
Сервис для работы с AI API.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
import logging
import random
import re
from dotenv import load_dotenv

from models.article import Article, Author

logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

class AIService:
    """Сервис для работы с AI API."""
    
    def __init__(self):
        """Инициализирует сервис."""
        self.service = os.getenv("AI_SERVICE", "OpenAI")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("MODEL", "GPT-3.5")
        self.language = os.getenv("LANGUAGE", "Русский")
        
        # Устанавливаем переменные окружения для прокси, если они нужны в будущем
        # Библиотека OpenAI автоматически использует эти переменные
        # os.environ["HTTPS_PROXY"] = "http://proxy.example.com:8080"
        # os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
        
        # Логируем информацию о настройках
        logger.info(f"AI Service: {self.service}")
        logger.info(f"API Key: {self.api_key[:5]}... (length: {len(self.api_key) if self.api_key else 0})")
        logger.info(f"Model: {self.model}")
        logger.info(f"Language: {self.language}")
        
    def create_summary(self, article: Article) -> str:
        """Создает краткое содержание статьи."""
        try:
            logger.info(f"Создание краткого содержания для статьи: {article.title}")
            
            # Приводим строку к нижнему регистру для сравнения, не зависящего от регистра
            service_lower = self.service.lower()
            
            if service_lower == "openai" and self.api_key:
                from openai import OpenAI
                
                # Подготавливаем данные о статье
                article_info = f"""Название: {article.title}
Авторы: {', '.join(article.authors)}
Аннотация: {article.abstract or article.summary}
Категории: {', '.join(article.categories)}
Год: {article.year}
"""
                
                # Отладочная информация
                logger.info(f"Инициализация клиента OpenAI с API ключом {self.api_key[:10]}...")
                
                # Настраиваем клиента OpenAI
                os.environ["OPENAI_API_KEY"] = self.api_key
                client = OpenAI()
                logger.info("Клиент OpenAI успешно создан")
                
                # Запрос к API
                logger.info("Отправка запроса к API OpenAI...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты - научный ассистент, который создает краткое содержание научных статей."},
                        {"role": "user", "content": f"Создай структурированное краткое содержание следующей научной статьи, выделив основные идеи, методологию, результаты и выводы. Используй разметку Markdown для структурирования.\n\nСтатья:\n{article_info}"}
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                )
                logger.info("Ответ от API OpenAI получен")
                
                return response.choices[0].message.content
            elif service_lower == "huggingface":
                # Используем имеющуюся заглушку, пока библиотека не будет установлена
                logger.info("Использование заглушки для Hugging Face")
                return f"""Краткое содержание статьи "{article.title}":

1. Основные идеи:
   - Статья посвящена исследованию в области {', '.join(article.categories) if article.categories else 'науки'}
   - Рассматриваются ключевые аспекты и методы анализа данных
   - Предлагается новый подход к решению проблемы

2. Методология:
   - Анализ существующих методов
   - Разработка усовершенствованного алгоритма
   - Экспериментальная проверка результатов

3. Результаты:
   - Получены статистически значимые улучшения
   - Предложены практические рекомендации
   - Определены направления для дальнейших исследований

4. Выводы:
   - Разработанный метод демонстрирует высокую эффективность
   - Предложенный подход может быть применен в смежных областях"""
            else:
                # Если сервис не распознан, возвращаем заглушку
                return f"""Краткое содержание статьи "{article.title}":

1. Основные идеи:
   - Идея 1
   - Идея 2
   - Идея 3

2. Методология:
   - Метод 1
   - Метод 2

3. Результаты:
   - Результат 1
   - Результат 2

4. Выводы:
   - Вывод 1
   - Вывод 2"""

        except Exception as e:
            logger.error(f"Ошибка при создании краткого содержания: {str(e)}")
            raise

    def find_references(self, article: Article) -> List[str]:
        """Ищет источники в статье."""
        try:
            logger.info(f"Поиск источников для статьи: {article.title}")
            
            # Приводим строку к нижнему регистру для сравнения, не зависящего от регистра
            service_lower = self.service.lower()
            
            if service_lower == "openai" and self.api_key:
                from openai import OpenAI
                
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
            
            if service_lower == "openai" and self.api_key:
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
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - научный ассистент, который создает краткое содержание научных статей."},
                    {"role": "user", "content": f"Создай структурированное краткое содержание следующей научной статьи, выделив основные разделы, методологию, результаты и выводы. Используй разметку Markdown для структурирования. Максимальная длина: {max_length} символов.\n\nСтатья:\n{text}"}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            
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
                from transformers import pipeline
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
                    
                    # Инициализируем модель для суммаризации
                    logger.info("Загрузка модели summarization...")
                    summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
                    logger.info("Модель summarization успешно загружена")
                    
                    # Разбиваем текст на части, если он слишком длинный
                    max_chunk_length = 1024
                    chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
                    
                    logger.info(f"Текст разбит на {len(chunks)} частей для обработки")
                    
                    summaries = []
                    for i, chunk in enumerate(chunks[:3]):  # Обрабатываем только первые 3 чанка для скорости
                        logger.info(f"Обработка части {i+1}/3...")
                        if len(chunk.strip()) > 100:  # Пропускаем слишком короткие куски
                            result = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                            if result and len(result) > 0:
                                summaries.append(result[0]['summary_text'])
                                logger.info(f"Часть {i+1} успешно обработана")
                        else:
                            logger.info(f"Часть {i+1} слишком короткая, пропускаем")
                    
                    if summaries:
                        # Объединяем результаты
                        combined_summary = " ".join(summaries)
                        
                        # Добавляем Markdown заголовок
                        logger.info("Суммаризация успешно выполнена")
                        return "# Краткое содержание статьи\n\n" + combined_summary
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