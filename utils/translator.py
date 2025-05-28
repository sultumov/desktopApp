"""Модуль для перевода текста."""

import requests
import logging
from typing import Optional, Dict
import re
import json
import os
import hashlib
from datetime import datetime, timedelta

# Настройка логгера
logger = logging.getLogger(__name__)

# Кэш переводов
TRANSLATIONS_CACHE: Dict[str, Dict] = {}
CACHE_FILE = "cache/translations.json"
CACHE_DURATION = timedelta(days=7)  # Кэш хранится 7 дней

def _load_cache():
    """Загружает кэш переводов из файла."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Очищаем устаревшие записи
            current_time = datetime.now()
            TRANSLATIONS_CACHE.clear()
            
            for key, data in cache_data.items():
                cache_time = datetime.fromisoformat(data['timestamp'])
                if current_time - cache_time <= CACHE_DURATION:
                    TRANSLATIONS_CACHE[key] = data
                    
            logger.debug(f"Загружено {len(TRANSLATIONS_CACHE)} переводов из кэша")
                    
    except Exception as e:
        logger.error(f"Ошибка при загрузке кэша переводов: {str(e)}")

def _save_cache():
    """Сохраняет кэш переводов в файл."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(TRANSLATIONS_CACHE, f, ensure_ascii=False, indent=2)
        logger.debug("Кэш переводов сохранен")
    except Exception as e:
        logger.error(f"Ошибка при сохранении кэша переводов: {str(e)}")

def _get_cache_key(text: str, target_lang: str) -> str:
    """Генерирует ключ для кэша.
    
    Args:
        text: Исходный текст
        target_lang: Целевой язык
        
    Returns:
        Ключ для кэша
    """
    return hashlib.md5(f"{text}:{target_lang}".encode()).hexdigest()

def translate_text(text: str, target_lang: str = 'en') -> str:
    """Переводит текст на указанный язык.
    
    Args:
        text: Текст для перевода
        target_lang: Целевой язык (по умолчанию английский)
        
    Returns:
        Переведенный текст или исходный текст в случае ошибки
    """
    try:
        # Если текст пустой, возвращаем его как есть
        if not text or not text.strip():
            return text
            
        # Если текст уже на целевом языке, возвращаем его как есть
        if target_lang == 'en' and not any(c.isalpha() and ord(c) > 127 for c in text):
            return text
        if target_lang == 'ru' and bool(re.search('[а-яА-Я]', text)):
            return text
            
        # Проверяем кэш
        cache_key = _get_cache_key(text, target_lang)
        if cache_key in TRANSLATIONS_CACHE:
            cache_data = TRANSLATIONS_CACHE[cache_key]
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time <= CACHE_DURATION:
                logger.debug("Перевод найден в кэше")
                return cache_data['translation']
            
        # Используем бесплатный API перевода
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Извлекаем переведенный текст из ответа
        result = response.json()
        translated_text = ''.join(part[0] for part in result[0] if part[0])
        
        # Сохраняем в кэш
        TRANSLATIONS_CACHE[cache_key] = {
            'translation': translated_text,
            'timestamp': datetime.now().isoformat()
        }
        _save_cache()
        
        logger.debug(f"Текст переведен: {text} -> {translated_text}")
        return translated_text
        
    except Exception as e:
        logger.error(f"Ошибка при переводе текста: {str(e)}")
        return text  # Возвращаем исходный текст в случае ошибки

# Загружаем кэш при импорте модуля
_load_cache() 