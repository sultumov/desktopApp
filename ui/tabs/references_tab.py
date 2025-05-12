"""Вкладка списка источников."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

from ..custom_widgets import CustomSplitter, CollapsiblePanel
from ..components.article_details import ArticleDetails
from ..components.action_buttons import ActionButtons

class ReferencesTab(QWidget):
    """Вкладка с источниками цитирования."""
    
    def __init__(self, parent=None):
        """Инициализирует вкладку источников.
        
        Args:
            parent: Родительский виджет (MainWindow)
        """
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс вкладки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Создаем разделитель для верхней и нижней части
        self.references_splitter = CustomSplitter(Qt.Orientation.Vertical, "references_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.references_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)
        
        # Восстановление размеров разделителя
        saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            saved_sizes = self.parent.user_settings.get_splitter_sizes("references_splitter")

        # Верхняя панель с заголовком и описанием
        top_panel = self._create_info_panel()
        
        # Создаем сворачиваемую панель для заголовка
        header_collapsible = CollapsiblePanel("Информация")
        header_collapsible.set_content(top_panel)
        self.references_splitter.addWidget(header_collapsible)

        # Создаем разделитель для списка и деталей
        self.references_list_splitter = CustomSplitter(Qt.Orientation.Horizontal, "references_list_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.references_list_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)
        
        # Восстановление размеров разделителя списка
        list_saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            list_saved_sizes = self.parent.user_settings.get_splitter_sizes("references_list_splitter")

        # Список источников
        list_panel = self._create_list_panel()
        
        # Создаем сворачиваемую панель для списка
        list_collapsible = CollapsiblePanel("Список источников")
        list_collapsible.set_content(list_panel)
        self.references_list_splitter.addWidget(list_collapsible)

        # Детали источников
        details_panel = self._create_details_panel()
        
        # Создаем сворачиваемую панель для деталей
        details_collapsible = CollapsiblePanel("Детали источника")
        details_collapsible.set_content(details_panel)
        self.references_list_splitter.addWidget(details_collapsible)

        # Установка пропорций разделителя списка
        if list_saved_sizes:
            self.references_list_splitter.setSizes(list_saved_sizes)
        else:
            self.references_list_splitter.setStretchFactor(0, 1)  # Список
            self.references_list_splitter.setStretchFactor(1, 2)  # Детали

        self.references_splitter.addWidget(self.references_list_splitter)

        # Установка пропорций основного разделителя
        if saved_sizes:
            self.references_splitter.setSizes(saved_sizes)
        else:
            self.references_splitter.setStretchFactor(0, 1)  # Заголовок
            self.references_splitter.setStretchFactor(1, 4)  # Список и детали

        layout.addWidget(self.references_splitter)
        
    def _create_info_panel(self):
        """Создает информационную панель.
        
        Returns:
            Виджет информационной панели
        """
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(16)

        # Заголовок
        title_label = QLabel("Поиск источников")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
            }
        """)
        top_layout.addWidget(title_label)

        # Описание
        description = QLabel(
            "Здесь вы можете найти источники, цитируемые в статье. "
            "Выберите статью на вкладке поиска и нажмите кнопку 'Найти источники'."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        top_layout.addWidget(description)
        
        return top_panel
        
    def _create_list_panel(self):
        """Создает панель списка источников.
        
        Returns:
            Виджет панели списка
        """
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(8)

        # Заголовок списка
        list_title = QLabel("Список источников")
        list_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
        """)
        list_layout.addWidget(list_title)

        # Список источников
        self.references_list = QListWidget()
        self.references_list.itemClicked.connect(self._show_reference)
        self.references_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
                padding: 8px;
            }
            QListWidget::item {
                border-bottom: 1px solid #EEEEEE;
                padding: 12px;
                margin: 2px 4px;
                border-radius: 4px;
                background: #F8F9FA;
                color: #333333;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #1565C0;
                border: 1px solid #90CAF9;
            }
            QListWidget::item:hover:!selected {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                color: #1565C0;
            }
        """)
        list_layout.addWidget(self.references_list)
        
        return list_panel
        
    def _create_details_panel(self):
        """Создает панель деталей источника.
        
        Returns:
            Виджет панели деталей
        """
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)
        
        # Заголовок деталей
        details_title = QLabel("Детали источника")
        details_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
        """)
        details_layout.addWidget(details_title)

        # Текстовое поле для деталей
        self.reference_details = ArticleDetails()
        details_layout.addWidget(self.reference_details)

        # Панель действий
        self.action_buttons = ActionButtons(mode="references")
        
        # Подключаем сигналы
        self.action_buttons.copy_clicked.connect(self._copy_references)
        self.action_buttons.save_clicked.connect(self._save_references)
        
        details_layout.addWidget(self.action_buttons)
        
        return details_panel
        
    def _show_reference(self, item):
        """Отображает детали выбранного источника."""
        reference_text = item.text()
        self.reference_details.display_text(reference_text, "Информация об источнике")
        
    def _copy_references(self):
        """Копирует список источников в буфер обмена."""
        if hasattr(self.parent, 'copy_references'):
            self.parent.copy_references()
            
    def _save_references(self):
        """Сохраняет список источников в файл."""
        if hasattr(self.parent, 'save_references'):
            self.parent.save_references()
            
    def add_reference(self, reference_text):
        """Добавляет источник в список.
        
        Args:
            reference_text: Текст источника
        """
        item = QListWidgetItem(reference_text)
        self.references_list.addItem(item)
        
    def clear_references(self):
        """Очищает список источников."""
        self.references_list.clear()
        self.reference_details.clear_details()
        
    def get_references(self):
        """Возвращает список всех источников.
        
        Returns:
            Список строк с источниками
        """
        references = []
        for i in range(self.references_list.count()):
            references.append(self.references_list.item(i).text())
        return references 