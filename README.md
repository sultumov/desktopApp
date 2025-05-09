# ArXiv Assistant

Приложение для работы с научными статьями из ArXiv. Позволяет искать статьи, создавать краткие содержания, находить источники и сохранять статьи в локальной библиотеке.

## Основные возможности

- Поиск статей на ArXiv
- Генерация кратких содержаний с помощью AI
- Поиск источников в тексте статьи
- Локальная библиотека статей
- Экспорт статей в различные форматы (BibTeX, текст)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/arxiv-assistant.git
cd arxiv-assistant
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env в корневой директории и добавьте необходимые переменные окружения:
```
AI_SERVICE=openai
AI_MODEL=gpt-4-turbo-preview
AI_API_KEY=your_api_key
LANGUAGE=ru
RESULTS_COUNT=10
```

## Использование

Запустите приложение:
```bash
python main.py
```

## Структура проекта

```
arxiv-assistant/
├── main.py              # Точка входа в приложение
├── requirements.txt     # Зависимости проекта
├── .env                # Конфигурация (не включена в репозиторий)
├── models/             # Модели данных
├── services/           # Сервисы для работы с API
├── ui/                 # Пользовательский интерфейс
│   └── icons/         # Иконки приложения
└── logs/              # Логи приложения
```

## Лицензия

MIT License 