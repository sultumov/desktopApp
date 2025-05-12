"""Утилиты для работы с пользовательскими настройками."""

import os
import json
import logging
from .settings_utils import load_json_settings, save_json_settings, get_user_data_dir

logger = logging.getLogger(__name__)

class UserSettingsManager:
    """Класс для управления пользовательскими настройками."""
    
    def __init__(self, settings_file="user_settings.json"):
        """Инициализирует объект настроек пользователя.
        
        Args:
            settings_file: Имя файла с настройками
        """
        self.settings_file = settings_file
        self.settings_path = os.path.join(os.getcwd(), settings_file)
        self.settings = self._load_settings()
        
    def _load_settings(self):
        """Загружает настройки из файла.
        
        Returns:
            Словарь с настройками
        """
        default_settings = {
            "interface": {
                "splitter_sizes": {},
                "window_size": [1200, 800],
                "window_position": [100, 100],
                "current_tab": 0,
                "theme": "light"
            }
        }
        
        return load_json_settings(self.settings_path, default_settings)
        
    def save_settings(self):
        """Сохраняет настройки в файл.
        
        Returns:
            True в случае успеха, False в случае ошибки
        """
        success, _ = save_json_settings(self.settings_path, self.settings)
        return success
        
    def get_window_size(self):
        """Возвращает размер окна.
        
        Returns:
            Список [ширина, высота] или None
        """
        return self.settings.get("interface", {}).get("window_size")
        
    def set_window_size(self, width, height):
        """Устанавливает размер окна.
        
        Args:
            width: Ширина окна
            height: Высота окна
        """
        if "interface" not in self.settings:
            self.settings["interface"] = {}
        self.settings["interface"]["window_size"] = [width, height]
        
    def get_window_position(self):
        """Возвращает позицию окна.
        
        Returns:
            Список [x, y] или None
        """
        return self.settings.get("interface", {}).get("window_position")
        
    def set_window_position(self, x, y):
        """Устанавливает позицию окна.
        
        Args:
            x: X-координата окна
            y: Y-координата окна
        """
        if "interface" not in self.settings:
            self.settings["interface"] = {}
        self.settings["interface"]["window_position"] = [x, y]
        
    def get_current_tab(self):
        """Возвращает индекс текущей вкладки.
        
        Returns:
            Индекс вкладки (int)
        """
        return self.settings.get("interface", {}).get("current_tab", 0)
        
    def set_current_tab(self, tab_index):
        """Устанавливает индекс текущей вкладки.
        
        Args:
            tab_index: Индекс вкладки
        """
        if "interface" not in self.settings:
            self.settings["interface"] = {}
        self.settings["interface"]["current_tab"] = tab_index
        
    def get_splitter_sizes(self, name):
        """Возвращает размеры разделителя.
        
        Args:
            name: Имя разделителя
            
        Returns:
            Список размеров или None
        """
        return self.settings.get("interface", {}).get("splitter_sizes", {}).get(name)
        
    def set_splitter_sizes(self, name, sizes):
        """Устанавливает размеры разделителя.
        
        Args:
            name: Имя разделителя
            sizes: Список размеров
        """
        if "interface" not in self.settings:
            self.settings["interface"] = {}
        if "splitter_sizes" not in self.settings["interface"]:
            self.settings["interface"]["splitter_sizes"] = {}
            
        self.settings["interface"]["splitter_sizes"][name] = sizes
        
    def get_theme(self):
        """Возвращает текущую тему.
        
        Returns:
            Имя темы (str)
        """
        return self.settings.get("interface", {}).get("theme", "light")
        
    def set_theme(self, theme):
        """Устанавливает текущую тему.
        
        Args:
            theme: Имя темы
        """
        if "interface" not in self.settings:
            self.settings["interface"] = {}
        self.settings["interface"]["theme"] = theme
        
    def get_setting(self, key, default=None):
        """Возвращает значение настройки по ключу.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или default
        """
        # Пытаемся получить значение из вложенных словарей
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set_setting(self, key, value):
        """Устанавливает значение настройки.
        
        Args:
            key: Ключ настройки
            value: Значение настройки
        """
        # Устанавливаем значение во вложенные словари
        keys = key.split('.')
        current = self.settings
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
            
        current[keys[-1]] = value 