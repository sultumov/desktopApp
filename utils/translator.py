"""Модуль для перевода текста."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from googletrans import Translator

# Настройка логгера
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация переводчика
translator = Translator()

def translate_text(text: str, source_lang: str = 'auto', target_lang: str = 'ru') -> str:
    """Переводит текст на указанный язык.
    
    Args:
        text: Текст для перевода
        source_lang: Исходный язык (auto для автоопределения)
        target_lang: Целевой язык
        
    Returns:
        Переведенный текст
    """
    try:
        # Если текст пустой, возвращаем его как есть
        if not text or not text.strip():
            return text
            
        # Пытаемся перевести текст
        result = translator.translate(text, src=source_lang, dest=target_lang)
        
        # Если перевод успешен, возвращаем результат
        if result and result.text:
            logger.debug(f"Текст успешно переведен с {result.src} на {result.dest}")
            return result.text
            
        # Если что-то пошло не так, возвращаем исходный текст
        logger.warning("Не удалось получить перевод, возвращаем исходный текст")
        return text
        
    except Exception as e:
        logger.error(f"Ошибка при переводе текста: {str(e)}")
        return text  # В случае ошибки возвращаем исходный текст 