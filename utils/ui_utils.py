"""Утилиты для работы с пользовательским интерфейсом."""

import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# Настройка логгера
logger = logging.getLogger(__name__)

def copy_to_clipboard(text):
    """Копирует текст в буфер обмена.

    Args:
        text: Текст для копирования

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    if not text:
        return False, "Нет текста для копирования"

    try:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        return True, "Текст скопирован в буфер обмена"
    except Exception as e:
        logger.error(f"Ошибка при копировании в буфер обмена: {str(e)}")
        return False, f"Ошибка при копировании: {str(e)}"

def show_info_message(parent, title, message):
    """Показывает информационное сообщение.

    Args:
        parent: Родительский виджет для диалога
        title: Заголовок сообщения
        message: Текст сообщения
    """
    QMessageBox.information(parent, title, message)

def show_error_message(parent, title, message):
    """Показывает сообщение об ошибке.

    Args:
        parent: Родительский виджет для диалога
        title: Заголовок сообщения
        message: Текст сообщения
    """
    QMessageBox.critical(parent, title, message)

def show_warning_message(parent, title, message):
    """Показывает предупреждающее сообщение.

    Args:
        parent: Родительский виджет для диалога
        title: Заголовок сообщения
        message: Текст сообщения
    """
    QMessageBox.warning(parent, title, message)

def set_status_message(status_bar, message, timeout=0):
    """Устанавливает сообщение в строке состояния.

    Args:
        status_bar: Объект строки состояния
        message: Текст сообщения
        timeout: Время в мс, через которое сообщение исчезнет (0 - не исчезает)
    """
    if status_bar:
        status_bar.showMessage(message, timeout)
        
def delay_call(func, msec=100):
    """Вызывает функцию с задержкой.
    
    Args:
        func: Функция для вызова
        msec: Задержка в миллисекундах
    """
    QTimer.singleShot(msec, func)
    
def confirm_action(parent, title, message, default_yes=False):
    """Запрашивает подтверждение действия.

    Args:
        parent: Родительский виджет для диалога
        title: Заголовок диалога
        message: Текст сообщения
        default_yes: True, если кнопка "Да" должна быть по умолчанию

    Returns:
        True, если пользователь подтвердил действие
    """
    default_button = QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No
    
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button
    )
    
    return reply == QMessageBox.StandardButton.Yes 