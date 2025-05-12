import os
import json
import logging
from typing import Dict, Any, Optional

class UserSettings:
    """Класс для управления пользовательскими настройками интерфейса."""
    
    def __init__(self, settings_file: str = "user_settings.json"):
        """Инициализирует объект настроек пользователя.
        
        Args:
            settings_file: Путь к файлу настроек
        """
        self.settings_file = settings_file
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Загружает настройки из файла.
        
        Returns:
            Словарь с настройками пользователя
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
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return settings
        except Exception as e:
            logging.error(f"Ошибка загрузки настроек: {e}")
        
        return default_settings
    
    def save_settings(self) -> bool:
        """Сохраняет настройки в файл.
        
        Returns:
            True если сохранение прошло успешно, иначе False
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"Ошибка сохранения настроек: {e}")
            return False
    
    def get_splitter_sizes(self, splitter_name: str) -> Optional[list]:
        """Получает размеры для указанного разделителя.
        
        Args:
            splitter_name: Имя разделителя
            
        Returns:
            Список размеров для разделителя или None
        """
        return self.settings["interface"]["splitter_sizes"].get(splitter_name)
    
    def set_splitter_sizes(self, splitter_name: str, sizes: list) -> None:
        """Устанавливает размеры для указанного разделителя.
        
        Args:
            splitter_name: Имя разделителя
            sizes: Список размеров
        """
        self.settings["interface"]["splitter_sizes"][splitter_name] = sizes
        
    def get_window_size(self) -> list:
        """Получает сохраненный размер окна.
        
        Returns:
            Список [ширина, высота]
        """
        return self.settings["interface"]["window_size"]
    
    def set_window_size(self, width: int, height: int) -> None:
        """Устанавливает размер окна.
        
        Args:
            width: Ширина окна
            height: Высота окна
        """
        self.settings["interface"]["window_size"] = [width, height]
    
    def get_window_position(self) -> list:
        """Получает сохраненную позицию окна.
        
        Returns:
            Список [x, y]
        """
        return self.settings["interface"]["window_position"]
    
    def set_window_position(self, x: int, y: int) -> None:
        """Устанавливает позицию окна.
        
        Args:
            x: Координата x
            y: Координата y
        """
        self.settings["interface"]["window_position"] = [x, y]
    
    def get_current_tab(self) -> int:
        """Получает индекс текущей вкладки.
        
        Returns:
            Индекс вкладки
        """
        return self.settings["interface"]["current_tab"]
    
    def set_current_tab(self, tab_index: int) -> None:
        """Устанавливает индекс текущей вкладки.
        
        Args:
            tab_index: Индекс вкладки
        """
        self.settings["interface"]["current_tab"] = tab_index
    
    def get_theme(self) -> str:
        """Получает текущую тему.
        
        Returns:
            Название темы
        """
        return self.settings["interface"]["theme"]
    
    def set_theme(self, theme: str) -> None:
        """Устанавливает текущую тему.
        
        Args:
            theme: Название темы
        """
        self.settings["interface"]["theme"] = theme 