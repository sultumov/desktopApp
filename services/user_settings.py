"""Модуль для управления пользовательскими настройками интерфейса."""

import os
import json
import logging
from typing import Dict, Any, Optional

from utils import UserSettingsManager

class UserSettings:
    """Класс для управления пользовательскими настройками интерфейса."""
    
    def __init__(self, settings_file: str = "user_settings.json"):
        """Инициализирует объект настроек пользователя.
        
        Args:
            settings_file: Путь к файлу настроек
        """
        self.settings_manager = UserSettingsManager(settings_file)
    
    def save_settings(self) -> bool:
        """Сохраняет настройки в файл.
        
        Returns:
            True если сохранение прошло успешно, иначе False
        """
        return self.settings_manager.save_settings()
    
    def get_splitter_sizes(self, splitter_name: str) -> Optional[list]:
        """Получает размеры для указанного разделителя.
        
        Args:
            splitter_name: Имя разделителя
            
        Returns:
            Список размеров для разделителя или None
        """
        return self.settings_manager.get_splitter_sizes(splitter_name)
    
    def set_splitter_sizes(self, splitter_name: str, sizes: list) -> None:
        """Устанавливает размеры для указанного разделителя.
        
        Args:
            splitter_name: Имя разделителя
            sizes: Список размеров
        """
        self.settings_manager.set_splitter_sizes(splitter_name, sizes)
        
    def get_window_size(self) -> list:
        """Получает сохраненный размер окна.
        
        Returns:
            Список [ширина, высота]
        """
        return self.settings_manager.get_window_size()
    
    def set_window_size(self, width: int, height: int) -> None:
        """Устанавливает размер окна.
        
        Args:
            width: Ширина окна
            height: Высота окна
        """
        self.settings_manager.set_window_size(width, height)
    
    def get_window_position(self) -> list:
        """Получает сохраненную позицию окна.
        
        Returns:
            Список [x, y]
        """
        return self.settings_manager.get_window_position()
    
    def set_window_position(self, x: int, y: int) -> None:
        """Устанавливает позицию окна.
        
        Args:
            x: Координата x
            y: Координата y
        """
        self.settings_manager.set_window_position(x, y)
    
    def get_current_tab(self) -> int:
        """Получает индекс текущей вкладки.
        
        Returns:
            Индекс вкладки
        """
        return self.settings_manager.get_current_tab()
    
    def set_current_tab(self, tab_index: int) -> None:
        """Устанавливает индекс текущей вкладки.
        
        Args:
            tab_index: Индекс вкладки
        """
        self.settings_manager.set_current_tab(tab_index)
    
    def get_theme(self) -> str:
        """Получает текущую тему.
        
        Returns:
            Название темы
        """
        return self.settings_manager.get_theme()
    
    def set_theme(self, theme: str) -> None:
        """Устанавливает текущую тему.
        
        Args:
            theme: Название темы
        """
        self.settings_manager.set_theme(theme)
        
    def get_setting(self, key, default=None):
        """Возвращает значение настройки по ключу.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или default
        """
        return self.settings_manager.get_setting(key, default)
        
    def set_setting(self, key, value):
        """Устанавливает значение настройки.
        
        Args:
            key: Ключ настройки
            value: Значение настройки
        """
        self.settings_manager.set_setting(key, value) 