"""Утилиты для работы с файлами."""

import os
import logging
from PyQt6.QtWidgets import QFileDialog, QMessageBox

logger = logging.getLogger(__name__)

def save_text_to_file(parent, text, title="Сохранить файл", default_path="", file_filter="Текстовые файлы (*.txt);;Все файлы (*.*)"):
    """Сохраняет текст в файл с диалогом выбора имени файла.

    Args:
        parent: Родительский виджет для диалога
        text: Текст для сохранения
        title: Заголовок диалога сохранения
        default_path: Путь по умолчанию
        file_filter: Фильтр типов файлов

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    if not text:
        return False, "Нет текста для сохранения"

    file_name, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        default_path,
        file_filter
    )

    if not file_name:
        return False, "Отменено пользователем"

    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(text)
        return True, f"Данные сохранены в файл {file_name}"
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {file_name}: {str(e)}")
        return False, f"Ошибка при сохранении файла: {str(e)}"

def ensure_dir_exists(directory):
    """Создаёт директорию, если она не существует.

    Args:
        directory: Путь к директории

    Returns:
        True, если директория существует или была создана успешно
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logger.info(f"Создана директория {directory}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании директории {directory}: {str(e)}")
            return False
    return True

def export_article_to_file(parent, article, title="Экспортировать статью", default_path="", file_filter="Текстовые файлы (*.txt);;Все файлы (*.*)"):
    """Экспортирует информацию о статье в файл.

    Args:
        parent: Родительский виджет для диалога
        article: Объект статьи для экспорта
        title: Заголовок диалога экспорта
        default_path: Путь по умолчанию
        file_filter: Фильтр типов файлов

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    if not article:
        return False, "Статья не выбрана"

    file_name, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        default_path,
        file_filter
    )

    if not file_name:
        return False, "Отменено пользователем"

    try:
        # Формируем содержимое файла
        content = f"Название: {article.title}\n"
        content += f"Авторы: {', '.join(article.authors)}\n"
        content += f"Дата публикации: {article.published.strftime('%d.%m.%Y')}\n"
        content += f"Категории: {', '.join(article.categories)}\n"
        content += f"DOI: {article.doi or 'Не указан'}\n"
        content += f"URL: {article.url}\n\n"
        content += "Аннотация:\n"
        content += f"{article.summary}\n"

        # Сохраняем файл
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, f"Статья экспортирована в {file_name}"
    except Exception as e:
        logger.error(f"Ошибка при экспорте статьи в файл {file_name}: {str(e)}")
        return False, f"Ошибка при экспорте статьи: {str(e)}"

def open_file(file_path):
    """Открывает файл в ассоциированной программе.

    Args:
        file_path: Путь к файлу

    Returns:
        Кортеж (успех: bool, сообщение: str)
    """
    if not os.path.exists(file_path):
        return False, f"Файл {file_path} не найден"

    try:
        os.startfile(file_path)
        return True, f"Файл {file_path} открыт"
    except Exception as e:
        logger.error(f"Ошибка при открытии файла {file_path}: {str(e)}")
        return False, f"Ошибка при открытии файла: {str(e)}"

def confirm_file_action(parent, title, message, default_yes=False):
    """Запрашивает подтверждение для действия с файлом.

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