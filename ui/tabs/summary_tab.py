"""Вкладка краткого содержания."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ..custom_widgets import CustomSplitter, CollapsiblePanel
from ..components.article_details import ArticleDetails
from ..components.action_buttons import ActionButtons

class SummaryTab(QWidget):
    """Вкладка с кратким содержанием статьи."""
    
    def __init__(self, parent=None):
        """Инициализирует вкладку краткого содержания.
        
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
        self.summary_splitter = CustomSplitter(Qt.Orientation.Vertical, "summary_splitter")
        if hasattr(self.parent, 'splitter_sizes_changed'):
            self.summary_splitter.splitterMoved.connect(self.parent.splitter_sizes_changed)
        
        # Восстановление размеров разделителя
        saved_sizes = None
        if hasattr(self.parent, 'user_settings'):
            saved_sizes = self.parent.user_settings.get_splitter_sizes("summary_splitter")

        # Верхняя панель (заголовок и описание)
        top_panel = self._create_info_panel()
        
        # Создаем сворачиваемую панель для заголовка
        header_collapsible = CollapsiblePanel("Информация")
        header_collapsible.set_content(top_panel)
        self.summary_splitter.addWidget(header_collapsible)
        
        # Нижняя панель (текст и кнопки)
        bottom_panel = self._create_content_panel()
        
        # Создаем сворачиваемую панель для содержимого
        content_collapsible = CollapsiblePanel("Содержание")
        content_collapsible.set_content(bottom_panel)
        self.summary_splitter.addWidget(content_collapsible)
        
        # Установка пропорций разделителя
        if saved_sizes:
            self.summary_splitter.setSizes(saved_sizes)
        else:
            self.summary_splitter.setStretchFactor(0, 1)  # Заголовок
            self.summary_splitter.setStretchFactor(1, 3)  # Содержание

        layout.addWidget(self.summary_splitter)
        
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
        title_label = QLabel("Краткое содержание")
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
            "Здесь вы можете создать краткое содержание статьи с помощью искусственного интеллекта. "
            "Выберите статью на вкладке поиска и нажмите кнопку 'Создать краткое содержание'."
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
        
    def _create_content_panel(self):
        """Создает панель содержания.
        
        Returns:
            Виджет панели содержания
        """
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # Текстовое поле для краткого содержания
        self.summary_text = ArticleDetails()
        bottom_layout.addWidget(self.summary_text)

        # Панель действий
        self.action_buttons = ActionButtons(mode="summary")
        
        # Подключаем сигналы
        self.action_buttons.copy_clicked.connect(self._copy_summary)
        self.action_buttons.save_clicked.connect(self._save_summary)
        
        bottom_layout.addWidget(self.action_buttons)
        
        return bottom_panel
        
    def _copy_summary(self):
        """Копирует краткое содержание в буфер обмена."""
        if hasattr(self.parent, 'copy_summary'):
            self.parent.copy_summary()
            
    def _save_summary(self):
        """Сохраняет краткое содержание в файл."""
        if hasattr(self.parent, 'save_summary'):
            self.parent.save_summary()
            
    def set_summary(self, text, title=None):
        """Устанавливает краткое содержание.
        
        Args:
            text: Текст краткого содержания
            title: Заголовок (если есть)
        """
        self.summary_text.display_text(text, title)
        
    def clear_summary(self):
        """Очищает краткое содержание."""
        self.summary_text.clear_details()
        
    def get_summary_text(self):
        """Возвращает текст краткого содержания.
        
        Returns:
            Текст краткого содержания
        """
        return self.summary_text.toPlainText() 