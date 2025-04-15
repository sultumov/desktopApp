import os
import json
from typing import List, Dict, Any, Optional, Union

from models.article import Article, Author

class AIService:
    """Сервис для работы с искусственным интеллектом."""
    
    def __init__(self):
        """Инициализирует сервис AI."""
        # Определяем, какой бэкенд использовать
        self.ai_backend = os.getenv("AI_BACKEND", "huggingface").lower()
        
        if self.ai_backend == "huggingface":
            try:
                import torch
                from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
                
                # Определяем, есть ли доступная CUDA GPU
                self.device = 0 if torch.cuda.is_available() else -1
                device_name = "GPU" if self.device == 0 else "CPU"
                
                # Инициализируем модели для разных задач
                print(f"Загрузка моделей Hugging Face на {device_name}...")
                
                # Модель для суммаризации - можно использовать разные варианты
                # BART лучше для длинных текстов, T5 - для коротких
                # Если памяти недостаточно, можно использовать меньшие модели
                summary_model = os.getenv("HF_SUMMARY_MODEL", "facebook/bart-large-cnn")
                print(f"Загрузка модели суммаризации: {summary_model}")
                self.summarizer = pipeline(
                    "summarization", 
                    model=summary_model,
                    device=self.device
                )
                
                # Модель для извлечения ключевых фраз 
                # Альтернативы: "ml6team/keyphrase-extraction-kbir-inspec", "nbroad/KeyBART-t5-base"
                keyword_model = os.getenv("HF_KEYWORD_MODEL", "yanekyuk/bert-uncased-keyword-extractor")
                print(f"Загрузка модели извлечения ключевых слов: {keyword_model}")
                self.keyword_extractor = pipeline(
                    "token-classification", 
                    model=keyword_model,
                    aggregation_strategy="simple",
                    device=self.device
                )
                
                # Модель для ответов на вопросы (для поиска источников)
                # Альтернативы: "distilbert-base-cased-distilled-squad", "deepset/roberta-large-squad2"
                qa_model = os.getenv("HF_QA_MODEL", "deepset/roberta-base-squad2")
                print(f"Загрузка модели вопросов-ответов: {qa_model}")
                self.qa_model = pipeline(
                    "question-answering",
                    model=qa_model,
                    device=self.device
                )
                
                # Модель для классификации текста (для определения тематик)
                # Полезно для категоризации статей
                classification_model = os.getenv("HF_CLASSIFICATION_MODEL", "facebook/bart-large-mnli")
                print(f"Загрузка модели классификации: {classification_model}")
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model=classification_model,
                    device=self.device
                )
                
                print("Модели Hugging Face успешно загружены")
                
            except ImportError as e:
                print(f"Ошибка при инициализации Hugging Face: {str(e)}")
                print("Установите необходимые библиотеки: pip install transformers torch")
                self.ai_backend = "none"
        else:
            print(f"Неизвестный AI бэкенд: {self.ai_backend}")
            self.ai_backend = "none"
    
    def generate_summary(self, text: str) -> str:
        """
        Генерирует краткое содержание для текста статьи.
        
        Args:
            text: Полный текст статьи
            
        Returns:
            Строка с кратким содержанием и ключевыми словами
        """
        if self.ai_backend == "huggingface":
            return self._generate_summary_huggingface(text)
        else:
            return "AI бэкенд не настроен. Установите AI_BACKEND=huggingface."
    
    def _generate_summary_huggingface(self, text: str) -> str:
        """Генерирует краткое содержание с помощью моделей Hugging Face."""
        try:
            # Разбиваем текст на части, если он слишком длинный
            max_chunk_length = 1000
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            
            # Получаем категории текста для выявления тематики
            categories = ["научное исследование", "обзор литературы", "технический отчет", 
                         "экспериментальное исследование", "теоретическая работа", "анализ данных"]
            
            category_results = self.zero_shot_classifier(
                text[:2000],  # Берем начало текста для определения категории
                categories,
                multi_label=True
            )
            
            # Суммаризируем каждый кусок
            summaries = []
            for chunk in chunks[:5]:  # Берем не более 5 кусков для разумного времени обработки
                summary = self.summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                if summary and len(summary) > 0:
                    summaries.append(summary[0]['summary_text'])
            
            # Объединяем суммаризации
            combined_summary = " ".join(summaries)
            
            # Извлекаем ключевые слова из всего текста
            keywords_results = self.keyword_extractor(text[:5000])  # Ограничиваем размер для ключевых слов
            
            # Фильтруем и сортируем ключевые слова по релевантности
            keywords = []
            keyword_scores = {}
            
            for item in keywords_results:
                word = item['word']
                if len(word) > 3 and word.lower() not in keywords:
                    if word.lower() not in keyword_scores or item['score'] > keyword_scores[word.lower()]:
                        keyword_scores[word.lower()] = item['score']
                        keywords.append(word)
            
            # Оставляем только 10 лучших ключевых слов
            keywords = keywords[:10]
            
            # Формируем итоговое резюме
            formatted_summary = f"## Ключевые слова\n{', '.join(keywords)}\n\n"
            
            # Добавляем информацию о категории текста
            top_categories = ", ".join([
                f"{cat} ({score:.1%})" 
                for cat, score in zip(category_results['labels'][:2], category_results['scores'][:2])
                if score > 0.3
            ])
            if top_categories:
                formatted_summary += f"## Тип работы\n{top_categories}\n\n"
            
            formatted_summary += f"## Краткое описание\n{combined_summary}\n\n"
            
            # Для основных выводов используем суммаризатор на последней части текста
            if len(text) > 2000:
                conclusions_text = text[-2000:]
                conclusions = self.summarizer(conclusions_text, max_length=150, min_length=50, do_sample=False)
                if conclusions and len(conclusions) > 0:
                    formatted_summary += "## Основные выводы\n"
                    for point in conclusions[0]['summary_text'].split('. '):
                        if point and len(point) > 10:  # Фильтруем короткие фрагменты
                            formatted_summary += f"- {point}\n"
            
            return formatted_summary
            
        except Exception as e:
            return f"Ошибка при генерации резюме с Hugging Face: {str(e)}"
    
    def find_references(self, text: str) -> List[Article]:
        """
        Анализирует текст статьи и находит потенциальные источники.
        
        Args:
            text: Полный текст статьи
            
        Returns:
            Список объектов Article, представляющих потенциальные источники
        """
        if self.ai_backend == "huggingface":
            return self._find_references_huggingface(text)
        else:
            return []
    
    def _find_references_huggingface(self, text: str) -> List[Article]:
        """Находит источники с помощью моделей Hugging Face."""
        try:
            # Расширенный список потенциальных цитат и упоминаний
            citation_patterns = [
                "согласно исследованию", "по мнению", "как показано в работе",
                "в исследовании", "как указано в", "как показали", "по данным",
                "цитируя", "в своей работе", "в статье", "в книге", 
                "авторы предлагают", "в работе автора", "согласно теории",
                "исследователи утверждают", "было продемонстрировано", 
                "исследование показало", "анализ", "предыдущие исследования",
                "в предыдущей работе", "согласно"
            ]
            
            # Ищем потенциальные цитаты с помощью модели вопросов-ответов
            references = []
            
            # Разбиваем текст на части для обработки
            max_chunk_length = 2000
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            
            # Дополнительные вопросы для более глубокого поиска
            general_questions = [
                "Какие источники цитируются в тексте?",
                "Какие авторы упоминаются в тексте?",
                "Какие научные работы упоминаются в тексте?",
                "На какие исследования ссылается автор?",
                "Какие годы публикаций упоминаются в тексте?"
            ]
            
            # Сначала обрабатываем общие вопросы
            for chunk in chunks[:10]:  # Обрабатываем не более 10 кусков
                for question in general_questions:
                    try:
                        result = self.qa_model(question=question, context=chunk)
                        
                        # Если нашли потенциальную ссылку с высокой уверенностью
                        if result['score'] > 0.4 and len(result['answer']) > 5:
                            # Добавляем найденный источник
                            self._process_reference_candidate(result['answer'], result['score'], references)
                    except Exception as e:
                        print(f"Ошибка при обработке общего вопроса: {str(e)}")
            
            # Затем ищем по конкретным паттернам цитирования
            for chunk in chunks[:10]:
                for pattern in citation_patterns:
                    question = f"Какие работы или авторы упоминаются после '{pattern}'?"
                    try:
                        result = self.qa_model(question=question, context=chunk)
                        
                        # Если нашли потенциальную ссылку
                        if result['score'] > 0.3 and len(result['answer']) > 5:
                            # Добавляем найденный источник
                            self._process_reference_candidate(result['answer'], result['score'], references)
                    except Exception as e:
                        print(f"Ошибка при обработке паттерна: {str(e)}")
            
            # Дополнительно ищем квадратные скобки с числами - типичный формат цитирования [1], [2], ...
            import re
            citations = re.findall(r'\[\d+\]', text)
            if citations:
                # Выбираем уникальные значения и сортируем
                unique_citations = sorted(set(citations))
                
                # Для каждой цитаты в формате [номер] ищем контекст
                for citation in unique_citations[:20]:  # Ограничиваем количество для производительности
                    # Ищем предложения с этой цитатой
                    pattern = rf'[^.!?]*{re.escape(citation)}[^.!?]*[.!?]'
                    citation_contexts = re.findall(pattern, text)
                    
                    if citation_contexts:
                        # Используем первое предложение как контекст
                        context = citation_contexts[0]
                        
                        # Задаем вопрос о том, что это за источник
                        question = f"Какой источник соответствует цитате {citation}?"
                        try:
                            result = self.qa_model(question=question, context=context)
                            if result['score'] > 0.2:
                                # Добавляем найденный источник
                                self._process_reference_candidate(
                                    f"{result['answer']} (цитата {citation})", 
                                    result['score'] + 0.2,  # Повышаем уверенность для цитат в скобках
                                    references
                                )
                        except Exception as e:
                            print(f"Ошибка при обработке нумерованной цитаты: {str(e)}")
            
            # Сортируем по уровню уверенности и удаляем дубликаты
            references = self._deduplicate_references(references)
            
            # Сортируем по уровню уверенности
            references.sort(key=lambda r: getattr(r, "confidence", 0.0), reverse=True)
            
            return references[:20]  # Ограничиваем количество результатов
            
        except Exception as e:
            print(f"Ошибка при поиске источников с Hugging Face: {str(e)}")
            return []
    
    def _process_reference_candidate(self, answer: str, score: float, references: List[Article]):
        """
        Обрабатывает кандидата на источник и добавляет его в список, если подходит.
        
        Args:
            answer: Текст ответа от модели
            score: Оценка уверенности
            references: Список для пополнения
        """
        # Пытаемся извлечь информацию о авторе и годе
        year = 0
        for word in answer.split():
            # Ищем год публикации (4 цифры между 1900 и 2023)
            if word.isdigit() and 1900 <= int(word) <= 2023:
                year = int(word)
                break
            
            # Также ищем годы в круглых скобках (2010) или с точками (2010.)
            import re
            year_match = re.search(r'\((\d{4})\)|\b(\d{4})[.,)]', word)
            if year_match:
                year_str = year_match.group(1) if year_match.group(1) else year_match.group(2)
                if 1900 <= int(year_str) <= 2023:
                    year = int(year_str)
                    break
        
        # Предполагаем, что фамилии авторов начинаются с заглавной буквы
        author_name = "Unknown"
        for name_part in answer.split()[:5]:  # Проверяем первые 5 слов
            # Типичный паттерн имени автора - слово с заглавной буквы длиной > 2 символов, 
            # не являющееся общим словом
            common_words = ["согласно", "как", "этим", "этот", "были", "было", "этой", "эти", "авторы"]
            if (name_part[0].isupper() and len(name_part) > 2 and 
                name_part.lower().rstrip(',.();:') not in common_words):
                author_name = name_part.rstrip(',.();:')
                break
        
        # Создаем объект статьи
        reference = Article(
            title=answer,
            authors=[Author(name=author_name)],
            abstract="",  # Абстракт неизвестен
            year=year,
            confidence=score
        )
        
        # Проверяем на дубликаты
        if not any(r.title.lower() == reference.title.lower() for r in references):
            references.append(reference)
    
    def _deduplicate_references(self, references: List[Article]) -> List[Article]:
        """
        Удаляет дубликаты источников на основе похожести текста.
        
        Args:
            references: Список источников с возможными дубликатами
            
        Returns:
            Список уникальных источников
        """
        if not references:
            return []
            
        unique_refs = []
        titles_lower = []
        
        for ref in references:
            # Нормализуем текст для сравнения
            normalized_title = ' '.join(ref.title.lower().split())
            
            # Проверяем, нет ли уже похожего источника
            is_duplicate = False
            for idx, existing_title in enumerate(titles_lower):
                # Если более 50% слов совпадают, считаем дубликатом
                common_words = set(normalized_title.split()) & set(existing_title.split())
                if common_words and len(common_words) / len(normalized_title.split()) > 0.5:
                    # Выбираем источник с большей уверенностью
                    if getattr(ref, "confidence", 0.0) > getattr(unique_refs[idx], "confidence", 0.0):
                        unique_refs[idx] = ref
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                titles_lower.append(normalized_title)
                unique_refs.append(ref)
        
        return unique_refs
        
    def classify_text(self, text: str, categories: List[str]) -> Dict[str, float]:
        """
        Классифицирует текст по заданным категориям.
        
        Args:
            text: Текст для классификации
            categories: Список категорий
            
        Returns:
            Словарь {категория: оценка}
        """
        if self.ai_backend != "huggingface":
            return {}
            
        try:
            # Ограничиваем размер текста
            if len(text) > 5000:
                text = text[:5000]
                
            # Выполняем zero-shot классификацию
            result = self.zero_shot_classifier(text, categories, multi_label=True)
            
            # Формируем результат
            return {label: score for label, score in zip(result['labels'], result['scores'])}
        except Exception as e:
            print(f"Ошибка при классификации текста: {str(e)}")
            return {} 