# -*- coding: utf-8 -*-
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QSettings
from dotenv import load_dotenv

# Настройка логирования
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Загрузка локальных переменных окружения
load_dotenv()

# Импортируем наши модули
from ui.main_window import MainWindow
from services.ai_service import AIService
from services.scholar_service import ScholarService
from services.storage_service import StorageService

class ResearchAssistantApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.settings = QSettings("ResearchAssistant", "LitReview")
        
        try:
            # Инициализация сервисов
            logging.info("Инициализация сервисов...")
            self.ai_service = AIService()
            self.scholar_service = ScholarService()
            self.storage_service = StorageService()
            
            # Создание и настройка главного окна
            logging.info("Создание главного окна...")
            self.main_window = MainWindow(
                ai_service=self.ai_service,
                scholar_service=self.scholar_service,
                storage_service=self.storage_service
            )
            logging.info("Приложение успешно инициализировано")
        except Exception as e:
            logging.error(f"Ошибка при инициализации приложения: {str(e)}")
            raise
        
    def run(self):
        try:
            self.main_window.show()
            logging.info("Приложение запущено")
            return self.app.exec()
        except Exception as e:
            logging.error(f"Критическая ошибка при запуске приложения: {str(e)}")
            return 1

if __name__ == "__main__":
    try:
        logging.info("Запуск приложения Research Assistant")
        app = ResearchAssistantApp()
        sys.exit(app.run())
    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}")
        sys.exit(1) 