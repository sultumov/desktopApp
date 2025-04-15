import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QSettings
from dotenv import load_dotenv

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
        
        # Инициализация сервисов
        self.ai_service = AIService()
        self.scholar_service = ScholarService()
        self.storage_service = StorageService()
        
        # Создание и настройка главного окна
        self.main_window = MainWindow(
            ai_service=self.ai_service,
            scholar_service=self.scholar_service,
            storage_service=self.storage_service
        )
        
    def run(self):
        self.main_window.show()
        return self.app.exec()

if __name__ == "__main__":
    app = ResearchAssistantApp()
    sys.exit(app.run()) 