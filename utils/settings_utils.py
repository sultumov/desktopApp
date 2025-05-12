"""Утилиты для работы с настройками приложения."""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_json_settings(file_path, default=None):
    """Загружает настройки из JSON файла.

    Args:
        file_path: Путь к файлу настроек
        default: Значение по умолчанию, если файл не существует или поврежден

    Returns:
        Словарь с настройками или значение по умолчанию
    """
    if default is None:
        default = {}
        
    try:
        if not os.path.exists(file_path):
            logger.info(f"Файл настроек {file_path} не найден, используем значения по умолчанию")
            return default
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON в файле {file_path}: {str(e)}")
        return default
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек из {file_path}: {str(e)}")
        return default

def save_json_settings(file_path, settings):
    """Сохраняет настройки в JSON файл.

    Args:
        file_path: Путь к файлу настроек
        settings: Словарь с настройками

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    try:
        # Убедимся, что директория существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
            
        return True, f"Настройки сохранены в {file_path}"
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек в {file_path}: {str(e)}")
        return False, f"Ошибка сохранения настроек: {str(e)}"

def load_env_settings(file_path='.env', default=None):
    """Загружает настройки из .env файла.

    Args:
        file_path: Путь к файлу настроек
        default: Значение по умолчанию, если файл не существует

    Returns:
        Словарь с настройками или значение по умолчанию
    """
    if default is None:
        default = {}
        
    try:
        if not os.path.exists(file_path):
            logger.info(f"Файл настроек {file_path} не найден, используем значения по умолчанию")
            return default
            
        settings = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' in line:
                    key, value = line.split('=', 1)
                    settings[key.strip()] = value.strip()
                    
        return settings
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек из {file_path}: {str(e)}")
        return default

def save_env_settings(file_path, settings):
    """Сохраняет настройки в .env файл.

    Args:
        file_path: Путь к файлу настроек
        settings: Словарь с настройками

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for key, value in settings.items():
                f.write(f"{key}={value}\n")
                
        return True, f"Настройки сохранены в {file_path}"
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек в {file_path}: {str(e)}")
        return False, f"Ошибка сохранения настроек: {str(e)}"

def get_config_dir():
    """Возвращает путь к директории с конфигурационными файлами.

    Returns:
        Путь к директории с конфигурационными файлами
    """
    # Определяем базовую директорию приложения
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(app_dir, 'config')
    
    # Создаем директорию, если она не существует
    os.makedirs(config_dir, exist_ok=True)
    
    return config_dir

def get_user_data_dir(app_name="ArxivAssistant"):
    """Возвращает путь к директории с пользовательскими данными.

    Args:
        app_name: Имя приложения

    Returns:
        Путь к директории с пользовательскими данными
    """
    home = Path.home()
    
    if os.name == 'nt':  # Windows
        data_dir = home / "AppData" / "Local" / app_name
    elif os.name == 'posix':  # Linux, macOS
        data_dir = home / ".local" / "share" / app_name.lower()
    else:
        data_dir = home / ".config" / app_name.lower()
    
    # Создаем директорию, если она не существует
    os.makedirs(data_dir, exist_ok=True)
    
    return str(data_dir) 