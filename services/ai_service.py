import os
import json
from typing import List, Dict, Any, Optional, Union
import logging
import random
import re

from models.article import Article, Author

class AIService:
    """Сервис для работы с ИИ моделями."""
    
    def __init__(self):
        """Инициализирует сервис для работы с ИИ."""
        # Определяем модель из env или используем OpenAI по умолчанию
        self.backend = os.getenv("AI_BACKEND", "openai")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        
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
            
            if self.backend == "openai" and self.api_key:
                return self._generate_summary_openai(text, max_length)
            else:
                return self._generate_summary_huggingface(text, max_length)
        except Exception as e:
            logging.error(f"Ошибка при генерации резюме: {str(e)}")
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
            import openai
            
            # Настраиваем клиента OpenAI
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
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
            logging.error(f"Ошибка OpenAI API: {str(e)}")
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
            from transformers import pipeline
            
            # Инициализируем модель для суммаризации
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            
            # Разбиваем текст на части, если он слишком длинный
            max_chunk_length = 1024
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            
            summaries = []
            for chunk in chunks[:3]:  # Обрабатываем только первые 3 чанка для скорости
                result = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                if result and len(result) > 0:
                    summaries.append(result[0]['summary_text'])
            
            # Объединяем результаты
            combined_summary = " ".join(summaries)
            
            # Добавляем Markdown заголовок
            return "# Краткое содержание статьи\n\n" + combined_summary
        except Exception as e:
            logging.error(f"Ошибка при использовании Hugging Face: {str(e)}")
            # Если модель не загружена или другая ошибка, возвращаем заглушку
            return self._generate_mock_summary(text)
    
    def find_references(self, text):
        """
        Находит источники в тексте научной статьи.
        
        Args:
            text (str): Текст статьи
            
        Returns:
            list: Список объектов Article с найденными источниками
        """
        try:
            if self.backend == "openai" and self.api_key:
                return self._find_references_openai(text)
            else:
                return self._find_references_huggingface(text)
        except Exception as e:
            logging.error(f"Ошибка при поиске источников: {str(e)}")
            # В случае ошибки возвращаем заглушку
            return self._generate_mock_references(text)
    
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
            import openai
            import json
            from models.article import Article, Author
            
            # Настраиваем клиента OpenAI
            openai.api_key = self.api_key
            
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
            
            user_prompt = f"""
            Проанализируй текст и извлеки все библиографические ссылки. Верни их в формате JSON массива:
            [
              {{
                "title": "Название статьи",
                "authors": ["Автор 1", "Автор 2"],
                "year": 2020,
                "journal": "Название журнала",
                "confidence": 0.95
              }},
              ...
            ]
            
            Если ты не уверен в каком-то значении, укажи null. Значение "confidence" должно отражать твою уверенность в правильности извлеченной ссылки (от 0 до 1).
            
            Текст:
            {text}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.2,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Извлекаем JSON из ответа
            # Иногда модель может вернуть текст до или после JSON
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
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
                    logging.error(f"Ошибка при обработке ссылки: {str(e)}")
                    continue
            
            return references
        except Exception as e:
            logging.error(f"Ошибка OpenAI API: {str(e)}")
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
            logging.error(f"Ошибка при использовании Hugging Face: {str(e)}")
            # Если модель не загружена или другая ошибка, возвращаем заглушку
            return self._generate_mock_references(text)
        
    # Другие методы... 