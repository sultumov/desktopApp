import os
import json
from typing import Dict, Any, Optional

class Config:
    """Класс для управления конфигурацией приложения."""
    
    def __init__(self):
        """Инициализирует конфигурацию."""
        # Пути для хранения файлов
        self.data_dir = os.path.join(os.path.expanduser("~"), ".research_assistant")
        self.config_file = os.path.join(self.data_dir, "config.json")
        
        # Настройки по умолчанию
        self.default_settings = {
            "api_keys": {
                "openai": "",
            },
            "search": {
                "max_results": 10,
                "default_source": "Google Scholar",
            },
            "ui": {
                "theme": "light",
                "font_size": 12
            }
        }
        
        # Загружаем настройки
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Загружает настройки из файла.
        
        Returns:
            Словарь с настройками
        """
        # Создаем директорию для данных, если она не существует
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Если файл конфигурации существует, загружаем из него
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Обновляем настройки по умолчанию новыми параметрами
                merged_settings = self.default_settings.copy()
                self._update_nested_dict(merged_settings, settings)
                return merged_settings
            except Exception as e:
                print(f"Ошибка при загрузке настроек: {str(e)}")
                return self.default_settings.copy()
        
        # Если файла нет, создаем его с настройками по умолчанию
        else:
            self._save_settings(self.default_settings)
            return self.default_settings.copy()
    
    def _save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки в файл.
        
        Args:
            settings: Словарь с настройками
            
        Returns:
            True, если настройки успешно сохранены
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {str(e)}")
            return False
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """
        Рекурсивно обновляет вложенный словарь.
        
        Args:
            d: Целевой словарь
            u: Словарь с обновлениями
            
        Returns:
            Обновленный словарь
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение настройки по ключу.
        
        Args:
            key: Ключ в формате "section.key" или "section.subsection.key"
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Значение настройки или default, если ключ не найден
        """
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        Устанавливает значение настройки по ключу.
        
        Args:
            key: Ключ в формате "section.key" или "section.subsection.key"
            value: Новое значение
            
        Returns:
            True, если настройка успешно обновлена
        """
        keys = key.split('.')
        
        # Если нет ключей, ничего не делаем
        if not keys:
            return False
        
        # Находим родительский словарь для последнего ключа
        current = self.settings
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Устанавливаем значение
        current[keys[-1]] = value
        
        # Сохраняем настройки
        return self._save_settings(self.settings)
    
    def save(self) -> bool:
        """
        Сохраняет текущие настройки в файл.
        
        Returns:
            True, если настройки успешно сохранены
        """
        return self._save_settings(self.settings)

# Создаем глобальный экземпляр конфигурации
config = Config() 