from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QPushButton, QLabel, QLineEdit, 
    QTextEdit, QListWidget, QSplitter, QFileDialog,
    QStatusBar, QComboBox, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
import os

class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.resize(400, 200)
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка текущих настроек
        self.load_settings()
    
    def init_ui(self):
        """Инициализирует интерфейс диалога."""
        # Основной макет
        layout = QFormLayout(self)
        
        # Выбор AI бэкенда
        self.ai_backend_combo = QComboBox()
        self.ai_backend_combo.addItem("OpenAI (GPT-4)", "openai")
        self.ai_backend_combo.addItem("Hugging Face (локально)", "huggingface")
        layout.addRow("ИИ бэкенд:", self.ai_backend_combo)
        
        # Выбор источника данных
        self.scholar_source_combo = QComboBox()
        self.scholar_source_combo.addItem("Google Scholar", "google_scholar")
        self.scholar_source_combo.addItem("Semantic Scholar", "semantic_scholar")
        layout.addRow("Источник статей:", self.scholar_source_combo)
        
        # API ключ OpenAI
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("OpenAI API ключ:", self.api_key_input)
        
        # API ключ Semantic Scholar (опционально)
        self.semantic_scholar_key_input = QLineEdit()
        self.semantic_scholar_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.semantic_scholar_key_input.setPlaceholderText("Необязательно")
        layout.addRow("Semantic Scholar API ключ:", self.semantic_scholar_key_input)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def load_settings(self):
        """Загружает текущие настройки из .env файла."""
        try:
            # Загружаем .env файл
            env_vars = {}
            env_path = ".env"
            
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            # OpenAI API ключ
            if "OPENAI_API_KEY" in env_vars:
                self.api_key_input.setText(env_vars["OPENAI_API_KEY"])
            
            # Semantic Scholar API ключ
            if "SEMANTIC_SCHOLAR_API_KEY" in env_vars:
                self.semantic_scholar_key_input.setText(env_vars["SEMANTIC_SCHOLAR_API_KEY"])
            
            # AI бэкенд
            if "AI_BACKEND" in env_vars:
                backend = env_vars["AI_BACKEND"].lower()
                index = self.ai_backend_combo.findData(backend)
                if index >= 0:
                    self.ai_backend_combo.setCurrentIndex(index)
            
            # Scholar источник
            if "SCHOLAR_SOURCE" in env_vars:
                source = env_vars["SCHOLAR_SOURCE"].lower()
                index = self.scholar_source_combo.findData(source)
                if index >= 0:
                    self.scholar_source_combo.setCurrentIndex(index)
        
        except Exception as e:
            print(f"Ошибка при загрузке настроек: {str(e)}")
    
    def save_settings(self):
        """Сохраняет настройки в .env файл."""
        try:
            # Получаем значения
            api_key = self.api_key_input.text()
            backend = self.ai_backend_combo.currentData()
            scholar_source = self.scholar_source_combo.currentData()
            semantic_scholar_key = self.semantic_scholar_key_input.text()
            
            # Загружаем текущий .env файл
            env_lines = []
            env_path = ".env"
            
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_lines = f.readlines()
            
            # Обновляем значения
            updated = {
                "OPENAI_API_KEY": False, 
                "AI_BACKEND": False,
                "SCHOLAR_SOURCE": False,
                "SEMANTIC_SCHOLAR_API_KEY": False
            }
            new_lines = []
            
            for line in env_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _ = line.split('=', 1)
                    key = key.strip()
                    
                    if key == "OPENAI_API_KEY":
                        new_lines.append(f"OPENAI_API_KEY={api_key}")
                        updated["OPENAI_API_KEY"] = True
                    elif key == "AI_BACKEND":
                        new_lines.append(f"AI_BACKEND={backend}")
                        updated["AI_BACKEND"] = True
                    elif key == "SCHOLAR_SOURCE":
                        new_lines.append(f"SCHOLAR_SOURCE={scholar_source}")
                        updated["SCHOLAR_SOURCE"] = True
                    elif key == "SEMANTIC_SCHOLAR_API_KEY":
                        new_lines.append(f"SEMANTIC_SCHOLAR_API_KEY={semantic_scholar_key}")
                        updated["SEMANTIC_SCHOLAR_API_KEY"] = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Добавляем недостающие значения
            if not updated["OPENAI_API_KEY"]:
                new_lines.append(f"OPENAI_API_KEY={api_key}")
            if not updated["AI_BACKEND"]:
                new_lines.append(f"AI_BACKEND={backend}")
            if not updated["SCHOLAR_SOURCE"]:
                new_lines.append(f"SCHOLAR_SOURCE={scholar_source}")
            if not updated["SEMANTIC_SCHOLAR_API_KEY"]:
                new_lines.append(f"SEMANTIC_SCHOLAR_API_KEY={semantic_scholar_key}")
            
            # Сохраняем обновленный файл
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            return True
        
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {str(e)}")
            return False
    
    def accept(self):
        """Обработчик нажатия кнопки OK."""
        if self.save_settings():
            super().accept()
            # Сообщаем родителю, что настройки изменились
            if hasattr(self.parent(), "settings_changed"):
                self.parent().settings_changed()

class MainWindow(QMainWindow):
    def __init__(self, ai_service, scholar_service, storage_service):
        super().__init__()
        
        # Сохраняем ссылки на сервисы
        self.ai_service = ai_service
        self.scholar_service = scholar_service
        self.storage_service = storage_service
        
        # Настройка главного окна
        self.setWindowTitle("Research Assistant")
        self.setMinimumSize(1000, 700)
        
        # Создание вкладок для разных функций
        self.init_ui()
        
    def init_ui(self):
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Создаем виджет с вкладками
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Добавляем вкладки для каждой функции
        self.tabs.addTab(self.create_search_tab(), "Поиск статей")
        self.tabs.addTab(self.create_summary_tab(), "Краткое содержание")
        self.tabs.addTab(self.create_references_tab(), "Поиск источников")
        self.tabs.addTab(self.create_library_tab(), "Моя библиотека")
        
        main_layout.addWidget(self.tabs)
        
        # Добавляем статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
        # Создаем меню
        self.create_menu()
        
    def create_menu(self):
        """Создает главное меню приложения."""
        menu_bar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menu_bar.addMenu("Файл")
        
        # Действие "Настройки"
        settings_action = file_menu.addAction("Настройки")
        settings_action.triggered.connect(self.show_settings)
        
        # Действие "Выход"
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
    
    def show_settings(self):
        """Показывает диалог настроек."""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def settings_changed(self):
        """Обработчик изменения настроек."""
        self.status_bar.showMessage("Настройки сохранены. Перезапустите приложение для применения изменений.")
    
    def create_search_tab(self):
        """Создает вкладку для поиска статей."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Верхняя панель с виджетами поиска
        top_layout = QHBoxLayout()
        
        # Выбор источника данных
        source_label = QLabel("Источник:")
        self.source_combo = QComboBox()
        
        # Получаем доступные источники данных
        available_sources = self.scholar_service.get_available_sources()
        for source in available_sources:
            self.source_combo.addItem(source["name"], source["id"])
        
        # Поле поиска
        search_label = QLabel("Тема исследования:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите ключевые слова или тему...")
        self.search_button = QPushButton("Найти")
        self.search_button.clicked.connect(self.search_articles)
        
        # Добавляем виджеты в верхний макет
        top_layout.addWidget(source_label)
        top_layout.addWidget(self.source_combo)
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.search_button)
        
        # Список результатов
        results_label = QLabel("Результаты поиска:")
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        # Панель информации о выбранной статье
        info_layout = QVBoxLayout()
        info_label = QLabel("Информация о статье:")
        self.article_info = QTextEdit()
        self.article_info.setReadOnly(True)
        info_layout.addWidget(info_label)
        info_layout.addWidget(self.article_info)
        
        # Связываем выбор статьи с отображением информации
        self.results_list.currentRowChanged.connect(self.show_article_info)
        
        # Кнопки действий
        action_layout = QHBoxLayout()
        self.add_to_library_btn = QPushButton("Добавить в библиотеку")
        self.add_to_library_btn.clicked.connect(self.add_to_library)
        
        self.show_references_btn = QPushButton("Показать источники")
        self.show_references_btn.clicked.connect(self.show_references)
        self.show_references_btn.setEnabled(False)  # Будет активна только для статей из Semantic Scholar
        
        self.show_citations_btn = QPushButton("Показать цитирования")
        self.show_citations_btn.clicked.connect(self.show_citations)
        self.show_citations_btn.setEnabled(False)  # Будет активна только для статей из Semantic Scholar
        
        action_layout.addWidget(self.add_to_library_btn)
        action_layout.addWidget(self.show_references_btn)
        action_layout.addWidget(self.show_citations_btn)
        
        # Добавляем все на вкладку
        layout.addLayout(top_layout)
        layout.addWidget(results_label)
        layout.addWidget(self.results_list)
        layout.addLayout(info_layout)
        layout.addLayout(action_layout)
        
        return tab
    
    def create_summary_tab(self):
        """Создает вкладку для генерации краткого содержания."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Верхняя панель с кнопками загрузки
        top_layout = QHBoxLayout()
        
        load_btn = QPushButton("Загрузить статью")
        load_btn.clicked.connect(self.load_article_for_summary)
        
        use_selected_btn = QPushButton("Использовать выбранную")
        use_selected_btn.clicked.connect(self.use_selected_article_for_summary)
        
        generate_btn = QPushButton("Сгенерировать резюме")
        generate_btn.clicked.connect(self.generate_summary)
        
        top_layout.addWidget(load_btn)
        top_layout.addWidget(use_selected_btn)
        top_layout.addWidget(generate_btn)
        
        # Разделитель для текста статьи и резюме
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Панель с текстом статьи
        article_widget = QWidget()
        article_layout = QVBoxLayout(article_widget)
        article_layout.addWidget(QLabel("Текст статьи:"))
        self.article_text = QTextEdit()
        self.article_text.setReadOnly(True)
        article_layout.addWidget(self.article_text)
        
        # Панель с результатами
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.addWidget(QLabel("Краткое содержание:"))
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        splitter.addWidget(article_widget)
        splitter.addWidget(summary_widget)
        
        # Добавляем все на вкладку
        layout.addLayout(top_layout)
        layout.addWidget(splitter)
        
        return tab
    
    def create_references_tab(self):
        """Создает вкладку для поиска источников."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Верхняя панель с кнопками загрузки
        top_layout = QHBoxLayout()
        
        load_btn = QPushButton("Загрузить статью")
        load_btn.clicked.connect(self.load_article_for_refs)
        
        use_selected_btn = QPushButton("Использовать выбранную")
        use_selected_btn.clicked.connect(self.use_selected_article_for_refs)
        
        find_refs_btn = QPushButton("Найти источники")
        find_refs_btn.clicked.connect(self.find_references)
        
        # Выбор метода поиска источников
        method_label = QLabel("Метод:")
        self.refs_method_combo = QComboBox()
        self.refs_method_combo.addItem("Анализ текста (ИИ)", "ai")
        self.refs_method_combo.addItem("Метаданные API (если доступно)", "api")
        
        top_layout.addWidget(load_btn)
        top_layout.addWidget(use_selected_btn)
        top_layout.addWidget(method_label)
        top_layout.addWidget(self.refs_method_combo)
        top_layout.addWidget(find_refs_btn)
        
        # Разделитель для текста статьи и найденных источников
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Панель с текстом статьи
        article_widget = QWidget()
        article_layout = QVBoxLayout(article_widget)
        article_layout.addWidget(QLabel("Текст статьи:"))
        self.refs_article_text = QTextEdit()
        self.refs_article_text.setReadOnly(True)
        article_layout.addWidget(self.refs_article_text)
        
        # Панель с результатами
        refs_widget = QWidget()
        refs_layout = QVBoxLayout(refs_widget)
        refs_layout.addWidget(QLabel("Найденные источники:"))
        self.references_list = QListWidget()
        refs_layout.addWidget(self.references_list)
        
        splitter.addWidget(article_widget)
        splitter.addWidget(refs_widget)
        
        # Добавляем все на вкладку
        layout.addLayout(top_layout)
        layout.addWidget(splitter)
        
        return tab
    
    def create_library_tab(self):
        """Создает вкладку для управления библиотекой."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Верхняя панель с кнопками
        top_layout = QHBoxLayout()
        
        category_label = QLabel("Категория:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("Все")
        self.category_combo.addItem("Избранное")
        self.category_combo.addItem("Прочитанное")
        self.category_combo.currentIndexChanged.connect(self.filter_library)
        
        export_btn = QPushButton("Экспорт")
        export_btn.clicked.connect(self.export_library)
        
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_from_library)
        
        top_layout.addWidget(category_label)
        top_layout.addWidget(self.category_combo)
        top_layout.addStretch()
        top_layout.addWidget(export_btn)
        top_layout.addWidget(delete_btn)
        
        # Список статей в библиотеке
        self.library_list = QListWidget()
        
        # Добавляем все на вкладку
        layout.addLayout(top_layout)
        layout.addWidget(self.library_list)
        
        return tab
    
    # Слоты (методы обработки событий)
    def search_articles(self):
        """Поиск статей по заданной теме."""
        query = self.search_input.text()
        if not query:
            self.status_bar.showMessage("Введите запрос для поиска")
            return
        
        # Получаем выбранный источник
        source = self.source_combo.currentData()
        
        self.status_bar.showMessage(f"Поиск статей в {self.source_combo.currentText()}...")
        
        # Вызов сервиса для поиска
        try:
            results = self.scholar_service.search_articles(query, source=source)
            
            # Отображение результатов
            self.results_list.clear()
            for article in results:
                # Используем свойство display_info для форматирования
                self.results_list.addItem(article.display_info)
            
            self.status_bar.showMessage(f"Найдено статей: {len(results)}")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при поиске: {str(e)}")
    
    def show_article_info(self, row):
        """Отображает информацию о выбранной статье."""
        if row < 0:
            return
            
        article = self.scholar_service.get_article_by_index(row)
        if not article:
            return
        
        # Формируем информацию о статье
        info = f"<h2>{article.title}</h2>"
        
        # Авторы
        authors = ", ".join([author.name for author in article.authors])
        info += f"<p><b>Авторы:</b> {authors}</p>"
        
        # Год и журнал
        if article.journal:
            info += f"<p><b>Журнал:</b> {article.journal}, {article.year}</p>"
        else:
            info += f"<p><b>Год:</b> {article.year}</p>"
        
        # Источник данных
        info += f"<p><b>Источник данных:</b> {article.source}</p>"
        
        # Статистика цитирования (если есть)
        if article.citation_count > 0:
            info += f"<p><b>Цитирований:</b> {article.citation_count}</p>"
        
        if article.reference_count > 0:
            info += f"<p><b>Количество источников:</b> {article.reference_count}</p>"
        
        # URL (если есть)
        if article.url:
            info += f"<p><b>URL:</b> <a href='{article.url}'>{article.url}</a></p>"
        
        # Абстракт
        if article.abstract:
            info += f"<h3>Аннотация</h3><p>{article.abstract}</p>"
        
        # Отображаем информацию
        self.article_info.setHtml(info)
        
        # Активируем кнопки только для Semantic Scholar
        has_semantic_scholar = article.source.lower() == "semantic_scholar" and hasattr(article, 'paper_id') and article.paper_id
        self.show_references_btn.setEnabled(has_semantic_scholar)
        self.show_citations_btn.setEnabled(has_semantic_scholar)
    
    def load_article_for_summary(self):
        """Загружает статью из файла для генерации резюме."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл статьи", "", "PDF Files (*.pdf);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                text = self.storage_service.load_file(file_path)
                self.article_text.setText(text)
                self.status_bar.showMessage(f"Статья загружена: {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Ошибка при загрузке файла: {str(e)}")
    
    def use_selected_article_for_summary(self):
        """Использует выбранную статью из результатов поиска для генерации резюме."""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статью из результатов поиска")
            return
        
        # Получение выбранной статьи
        selected_index = self.results_list.row(selected_items[0])
        article = self.scholar_service.get_article_by_index(selected_index)
        
        try:
            # Загрузка полного текста
            text = self.scholar_service.get_article_text(article)
            self.article_text.setText(text)
            self.status_bar.showMessage("Статья загружена")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при загрузке статьи: {str(e)}")
    
    def generate_summary(self):
        """Генерирует краткое содержание для загруженной статьи."""
        text = self.article_text.toPlainText()
        if not text:
            self.status_bar.showMessage("Сначала загрузите статью")
            return
        
        self.status_bar.showMessage("Генерация резюме...")
        
        try:
            summary = self.ai_service.generate_summary(text)
            self.summary_text.setText(summary)
            self.status_bar.showMessage("Резюме сгенерировано")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при генерации резюме: {str(e)}")
    
    def load_article_for_refs(self):
        """Загружает статью из файла для поиска источников."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл статьи", "", "PDF Files (*.pdf);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                text = self.storage_service.load_file(file_path)
                self.refs_article_text.setText(text)
                self.status_bar.showMessage(f"Статья загружена: {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Ошибка при загрузке файла: {str(e)}")
    
    def use_selected_article_for_refs(self):
        """Использует выбранную статью из результатов поиска для поиска источников."""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статью из результатов поиска")
            return
        
        # Получение выбранной статьи
        selected_index = self.results_list.row(selected_items[0])
        article = self.scholar_service.get_article_by_index(selected_index)
        
        try:
            # Загрузка полного текста
            text = self.scholar_service.get_article_text(article)
            self.refs_article_text.setText(text)
            
            # Сохраняем ID статьи для возможного использования API
            self.refs_article_text.setProperty("article", article)
            
            self.status_bar.showMessage("Статья загружена")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при загрузке статьи: {str(e)}")
    
    def find_references(self):
        """Ищет источники для загруженной статьи."""
        text = self.refs_article_text.toPlainText()
        if not text:
            self.status_bar.showMessage("Сначала загрузите статью")
            return
        
        # Определяем метод поиска
        method = self.refs_method_combo.currentData()
        
        # Получаем статью, если она была сохранена в свойствах
        article = self.refs_article_text.property("article")
        
        self.status_bar.showMessage("Поиск источников...")
        
        try:
            references = []
            
            if method == "api" and article and hasattr(article, "paper_id") and article.source == "Semantic Scholar":
                # Используем API для получения источников
                references = self.scholar_service.get_references(article)
                self.status_bar.showMessage(f"Источники получены через API")
            else:
                # Используем ИИ для анализа текста
                references = self.ai_service.find_references(text)
                self.status_bar.showMessage(f"Источники найдены с помощью ИИ")
            
            # Отображение результатов
            self.references_list.clear()
            for ref in references:
                # Используем свойство display_info для форматирования
                item_text = ref.display_info
                if hasattr(ref, "confidence") and ref.confidence > 0:
                    item_text += f" [уверенность: {ref.confidence:.1%}]"
                self.references_list.addItem(item_text)
            
            self.status_bar.showMessage(f"Найдено источников: {len(references)}")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при поиске источников: {str(e)}")
    
    def show_references(self):
        """Показывает источники для выбранной статьи."""
        # Получаем выбранную статью
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статью из результатов поиска")
            return
        
        selected_index = self.results_list.row(selected_items[0])
        article = self.scholar_service.get_article_by_index(selected_index)
        
        if not article:
            self.status_bar.showMessage("Выбранная статья недоступна")
            return
        
        # Проверяем, что у статьи есть paperId
        if not (hasattr(article, 'paper_id') and article.paper_id):
            self.status_bar.showMessage("У этой статьи нет идентификатора для получения источников")
            return
        
        try:
            # Получаем источники
            self.status_bar.showMessage(f"Получение источников для '{article.title}'...")
            references = self.scholar_service.get_references(article)
            
            # Создаем диалоговое окно для отображения источников
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Источники для '{article.title}'")
            dialog.setMinimumSize(800, 600)
            
            # Создаем макет и виджеты
            layout = QVBoxLayout(dialog)
            label = QLabel(f"Источники для статьи: <b>{article.title}</b> ({len(references)} найдено)")
            layout.addWidget(label)
            
            # Список источников
            refs_list = QListWidget()
            for ref in references:
                # Используем свойство display_info для форматирования
                refs_list.addItem(ref.display_info)
            
            layout.addWidget(refs_list)
            
            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            # Показываем диалог
            dialog.exec()
            
            self.status_bar.showMessage(f"Найдено {len(references)} источников")
            
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при получении источников: {str(e)}")
            
    def show_citations(self):
        """Показывает цитирования для выбранной статьи."""
        # Получаем выбранную статью
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статью из результатов поиска")
            return
        
        selected_index = self.results_list.row(selected_items[0])
        article = self.scholar_service.get_article_by_index(selected_index)
        
        if not article:
            self.status_bar.showMessage("Выбранная статья недоступна")
            return
        
        # Проверяем, что у статьи есть paperId
        if not (hasattr(article, 'paper_id') and article.paper_id):
            self.status_bar.showMessage("У этой статьи нет идентификатора для получения цитирований")
            return
        
        try:
            # Получаем цитирования
            self.status_bar.showMessage(f"Получение цитирований для '{article.title}'...")
            citations = self.scholar_service.get_citations(article)
            
            # Создаем диалоговое окно для отображения цитирований
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Цитирования для '{article.title}'")
            dialog.setMinimumSize(800, 600)
            
            # Создаем макет и виджеты
            layout = QVBoxLayout(dialog)
            label = QLabel(f"Статьи, цитирующие: <b>{article.title}</b> ({len(citations)} найдено)")
            layout.addWidget(label)
            
            # Список цитирований
            citations_list = QListWidget()
            for citation in citations:
                # Используем свойство display_info для форматирования
                citations_list.addItem(citation.display_info)
            
            layout.addWidget(citations_list)
            
            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            # Показываем диалог
            dialog.exec()
            
            self.status_bar.showMessage(f"Найдено {len(citations)} цитирований")
            
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при получении цитирований: {str(e)}")
    
    def add_to_library(self):
        """Добавляет выбранную статью в библиотеку."""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статью для добавления в библиотеку")
            return
        
        # Получение выбранной статьи
        selected_index = self.results_list.row(selected_items[0])
        article = self.scholar_service.get_article_by_index(selected_index)
        
        try:
            # Добавляем статью в библиотеку
            if self.storage_service.add_article(article):
                self.status_bar.showMessage(f"Статья '{article.title}' добавлена в библиотеку")
                
                # Обновляем отображение библиотеки
                self.filter_library()
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при добавлении в библиотеку: {str(e)}")
    
    def filter_library(self):
        """Фильтрует библиотеку по выбранной категории."""
        category = self.category_combo.currentText()
        
        try:
            articles = self.storage_service.get_library_articles(category)
            
            # Отображение библиотеки
            self.library_list.clear()
            for article in articles:
                self.library_list.addItem(article.display_info)
            
            self.status_bar.showMessage(f"Статей в библиотеке: {len(articles)}")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при загрузке библиотеки: {str(e)}")
    
    def export_library(self):
        """Экспортирует выбранные статьи из библиотеки."""
        selected_items = self.library_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статьи для экспорта")
            return
        
        # Диалог сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить библиографию", "", "BibTeX (*.bib);;PDF (*.pdf);;Word (*.docx);;JSON (*.json)"
        )
        
        if file_path:
            try:
                # Получаем индексы выбранных статей
                selected_indices = [self.library_list.row(item) for item in selected_items]
                
                # Экспортируем
                self.storage_service.export_articles(selected_indices, file_path)
                self.status_bar.showMessage(f"Экспорт завершен: {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Ошибка при экспорте: {str(e)}")
    
    def delete_from_library(self):
        """Удаляет выбранные статьи из библиотеки."""
        selected_items = self.library_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Выберите статьи для удаления")
            return
        
        try:
            # Получаем индексы выбранных статей
            selected_indices = [self.library_list.row(item) for item in selected_items]
            
            # Удаляем
            self.storage_service.delete_articles(selected_indices)
            
            # Обновляем отображение
            self.filter_library()
            self.status_bar.showMessage("Выбранные статьи удалены")
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при удалении: {str(e)}") 