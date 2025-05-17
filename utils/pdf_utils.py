"""Утилиты для работы с PDF файлами."""

import os
import logging
import requests
from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader
from urllib.parse import urlparse

# Настройка логгера
logger = logging.getLogger(__name__)

def download_pdf(url, destination_path, chunk_size=8192):
    """Скачивает PDF по указанному URL.

    Args:
        url: URL для скачивания
        destination_path: Путь для сохранения файла
        chunk_size: Размер куска данных при скачивании

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    # Проверяем, существует ли каталог для сохранения
    directory = os.path.dirname(destination_path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            logger.error(f"Ошибка при создании директории {directory}: {str(e)}")
            return False, f"Ошибка при создании директории: {str(e)}"

    # Получаем имя файла из URL, если не указано явно
    if not os.path.basename(destination_path):
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = 'document.pdf'
        destination_path = os.path.join(directory, filename)

    try:
        # Скачиваем файл по частям
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(destination_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    f.write(chunk)

        return True, f"PDF успешно скачан: {destination_path}"
    except requests.exceptions.HTTPError as e:
        logger.error(f"Ошибка HTTP при скачивании PDF: {str(e)}")
        return False, f"Ошибка HTTP при скачивании: {str(e)}"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Ошибка соединения при скачивании PDF: {str(e)}")
        return False, f"Ошибка соединения: {str(e)}"
    except requests.exceptions.Timeout as e:
        logger.error(f"Тайм-аут при скачивании PDF: {str(e)}")
        return False, f"Тайм-аут при скачивании: {str(e)}"
    except Exception as e:
        logger.error(f"Ошибка при скачивании PDF: {str(e)}")
        return False, f"Ошибка при скачивании: {str(e)}"

def is_valid_pdf(file_path):
    """Проверяет, является ли файл действительным PDF.

    Args:
        file_path: Путь к файлу

    Returns:
        True, если файл является действительным PDF
    """
    if not os.path.exists(file_path):
        logger.warning(f"Файл не найден: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            # Проверяем сигнатуру PDF файла
            return header == b'%PDF'
    except Exception as e:
        logger.error(f"Ошибка при проверке PDF файла {file_path}: {str(e)}")
        return False

def get_pdf_info(file_path):
    """Возвращает базовую информацию о PDF файле.

    Args:
        file_path: Путь к файлу

    Returns:
        Словарь с информацией о файле или None в случае ошибки
    """
    if not is_valid_pdf(file_path):
        return None

    try:
        file_stats = os.stat(file_path)
        return {
            'path': file_path,
            'size': file_stats.st_size,
            'modified': file_stats.st_mtime,
            'created': file_stats.st_ctime
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о PDF файле {file_path}: {str(e)}")
        return None 