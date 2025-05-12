"""Компонент с кнопками для действий."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

class ActionButtons(QWidget):
    """Компонент с кнопками для действий над статьей."""
    
    # Сигналы для действий
    summary_clicked = pyqtSignal()
    references_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    download_clicked = pyqtSignal()
    copy_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    
    def __init__(self, parent=None, mode="search"):
        """Инициализирует панель кнопок.
        
        Args:
            parent: Родительский виджет
            mode: Режим кнопок ('search', 'library', 'summary', 'references')
        """
        super().__init__(parent)
        self.mode = mode
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает внешний вид панели."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        
        if self.mode == "search":
            self._setup_search_buttons()
        elif self.mode == "library":
            self._setup_library_buttons()
        elif self.mode == "summary":
            self._setup_summary_buttons()
        elif self.mode == "references":
            self._setup_references_buttons()
            
        self.layout.addStretch()
        
    def _setup_search_buttons(self):
        """Настраивает кнопки для режима поиска."""
        # Кнопка создания краткого содержания
        summary_button = QPushButton("Создать краткое содержание")
        summary_button.setIcon(QIcon("ui/icons/summary.svg"))
        summary_button.clicked.connect(self.summary_clicked.emit)
        summary_button.setStyleSheet(self._get_button_style("primary"))
        self.layout.addWidget(summary_button)

        # Кнопка поиска источников
        references_button = QPushButton("Найти источники")
        references_button.setIcon(QIcon("ui/icons/references.svg"))
        references_button.clicked.connect(self.references_clicked.emit)
        references_button.setStyleSheet(self._get_button_style("primary"))
        self.layout.addWidget(references_button)

        # Кнопка сохранения
        save_button = QPushButton("Сохранить в библиотеку")
        save_button.setIcon(QIcon("ui/icons/save.svg"))
        save_button.clicked.connect(self.save_clicked.emit)
        save_button.setStyleSheet(self._get_button_style("success"))
        self.layout.addWidget(save_button)

        # Кнопка загрузки
        download_button = QPushButton("Скачать PDF")
        download_button.setIcon(QIcon("ui/icons/download.svg"))
        download_button.clicked.connect(self.download_clicked.emit)
        download_button.setStyleSheet(self._get_button_style("warning"))
        self.layout.addWidget(download_button)
        
    def _setup_library_buttons(self):
        """Настраивает кнопки для режима библиотеки."""
        # Кнопка удаления
        delete_button = QPushButton()
        delete_button.setIcon(QIcon("ui/icons/delete.svg"))
        delete_button.setToolTip("Удалить из библиотеки")
        delete_button.clicked.connect(self.delete_clicked.emit)
        delete_button.setFixedSize(40, 40)
        delete_button.setStyleSheet(self._get_button_style("danger", "circle"))
        self.layout.addWidget(delete_button)

        # Кнопка экспорта
        export_button = QPushButton()
        export_button.setIcon(QIcon("ui/icons/export.svg"))
        export_button.setToolTip("Экспортировать")
        export_button.clicked.connect(self.export_clicked.emit)
        export_button.setFixedSize(40, 40)
        export_button.setStyleSheet(self._get_button_style("primary", "circle"))
        self.layout.addWidget(export_button)
        
    def _setup_summary_buttons(self):
        """Настраивает кнопки для режима краткого содержания."""
        # Кнопка копирования
        copy_button = QPushButton()
        copy_button.setIcon(QIcon("ui/icons/copy.svg"))
        copy_button.setToolTip("Копировать в буфер обмена")
        copy_button.clicked.connect(self.copy_clicked.emit)
        copy_button.setFixedSize(40, 40)
        copy_button.setStyleSheet(self._get_button_style("primary", "circle"))
        self.layout.addWidget(copy_button)

        # Кнопка сохранения
        save_button = QPushButton()
        save_button.setIcon(QIcon("ui/icons/save.svg"))
        save_button.setToolTip("Сохранить в файл")
        save_button.clicked.connect(self.save_clicked.emit)
        save_button.setFixedSize(40, 40)
        save_button.setStyleSheet(self._get_button_style("primary", "circle"))
        self.layout.addWidget(save_button)
        
    def _setup_references_buttons(self):
        """Настраивает кнопки для режима списка источников."""
        # Кнопка копирования
        copy_button = QPushButton("Копировать")
        copy_button.setIcon(QIcon("ui/icons/copy.svg"))
        copy_button.clicked.connect(self.copy_clicked.emit)
        copy_button.setStyleSheet(self._get_button_style("primary"))
        self.layout.addWidget(copy_button)

        # Кнопка сохранения
        save_button = QPushButton("Сохранить")
        save_button.setIcon(QIcon("ui/icons/save.svg"))
        save_button.clicked.connect(self.save_clicked.emit)
        save_button.setStyleSheet(self._get_button_style("success"))
        self.layout.addWidget(save_button)
    
    def _get_button_style(self, style_type, shape="rect"):
        """Возвращает CSS стиль для кнопки.
        
        Args:
            style_type: Тип стиля ('primary', 'success', 'warning', 'danger')
            shape: Форма кнопки ('rect', 'circle')
            
        Returns:
            CSS строка стиля
        """
        colors = {
            "primary": {"normal": "#2196F3", "hover": "#1976D2", "pressed": "#0D47A1"},
            "success": {"normal": "#4CAF50", "hover": "#388E3C", "pressed": "#1B5E20"},
            "warning": {"normal": "#FF9800", "hover": "#F57C00", "pressed": "#E65100"},
            "danger": {"normal": "#F44336", "hover": "#D32F2F", "pressed": "#B71C1C"}
        }
        
        color_set = colors.get(style_type, colors["primary"])
        
        if shape == "circle":
            return f"""
                QPushButton {{
                    background: {color_set['normal']};
                    border-radius: 20px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background: {color_set['hover']};
                }}
                QPushButton:pressed {{
                    background: {color_set['pressed']};
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {color_set['normal']};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {color_set['hover']};
                }}
                QPushButton:pressed {{
                    background-color: {color_set['pressed']};
                }}
            """ 