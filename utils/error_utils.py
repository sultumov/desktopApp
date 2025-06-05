"""Утилиты для обработки ошибок и исключений."""

import sys
import logging
import traceback
from functools import wraps
from typing import Optional, Tuple, Type
from PyQt6.QtWidgets import QMessageBox
from PyPDF2 import PdfReader

# Настройка логгера
logger = logging.getLogger(__name__)

def log_exception(exc, message=None):
    """Логирует исключение с подробной информацией.

    Args:
        exc: Объект исключения
        message: Дополнительное сообщение (необязательно)
    """
    exc_info = sys.exc_info()
    if message:
        logger.error(f"{message}: {str(exc)}")
    else:
        logger.error(str(exc))
    logger.debug("".join(traceback.format_exception(*exc_info)))

def safe_execute(func, error_message="Произошла ошибка", *args, **kwargs):
    """Безопасно выполняет функцию, перехватывая все исключения.

    Args:
        func: Функция для выполнения
        error_message: Сообщение об ошибке
        *args, **kwargs: Аргументы для передачи в функцию

    Returns:
        Кортеж (успех: bool, результат или сообщение об ошибке)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        log_exception(e, error_message)
        return False, f"{error_message}: {str(e)}"

def exception_handler(message=None):
    """Декоратор для перехвата исключений в методах.

    Args:
        message: Сообщение, которое будет залогировано при исключении

    Returns:
        Обёрнутая функция
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = message or f"Ошибка в функции {func.__name__}"
                log_exception(e, error_msg)
                raise
        return wrapper
    return decorator

def gui_exception_handler(show_error_func=None):
    """Декоратор для перехвата исключений в методах GUI.
    
    Args:
        show_error_func: Функция для отображения ошибки (необязательно)
        
    Returns:
        Обёрнутая функция
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = f"Ошибка в функции {func.__name__}: {str(e)}"
                log_exception(e, error_msg)
                
                # Если есть функция для отображения ошибки - используем её
                if show_error_func:
                    show_error_func(self, "Ошибка", error_msg)
                # Иначе, если у объекта есть statusBar - используем его
                elif hasattr(self, 'statusBar') and callable(self.statusBar):
                    self.statusBar().showMessage(error_msg)
                
                # Возвращаем None, чтобы вызывающий код мог проверить на ошибку
                return None
                
        return wrapper
    return decorator 