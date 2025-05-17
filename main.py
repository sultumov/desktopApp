"""
ArXiv Assistant - приложение для работы с научными статьями.
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils import ensure_dir_exists

# Создаем директорию для логов
ensure_dir_exists('logs')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

def main():
    """Точка входа в приложение."""
    try:
        # Создание приложения
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

        # Создание и отображение главного окна
        window = MainWindow()
        window.show()

        # Запуск цикла обработки событий
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 