"""Компонент с кнопками для действий."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

class ActionButtons(QWidget):
    """Панель с кнопками действий."""
    
    # Сигналы
    summary_clicked = pyqtSignal()
    references_clicked = pyqtSignal()
    copy_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    download_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    
    def __init__(self, mode="search", parent=None):
        """Инициализирует панель с кнопками.
        
        Args:
            mode: Режим отображения кнопок ("search", "summary" или "library")
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.mode = mode
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс панели."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        button_style = """
            QPushButton {
                color: white;
                background-color: #3498DB;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 120px;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #2980B9;
            }
            
            QPushButton:pressed {
                background-color: #2472A4;
            }
            
            QPushButton[secondary="true"] {
                color: #2C3E50;
                background-color: #ECF0F1;
            }
            
            QPushButton[secondary="true"]:hover {
                background-color: #BDC3C7;
            }
            
            QPushButton[warning="true"] {
                color: white;
                background-color: #E74C3C;
            }
            
            QPushButton[warning="true"]:hover {
                background-color: #C0392B;
            }
            
            QPushButton:disabled {
                background-color: #BDC3C7;
                color: #95A5A6;
            }
        """
        
        if self.mode == "search":
            # Кнопка создания краткого содержания
            self.summary_button = QPushButton("Краткое содержание")
            self.summary_button.setProperty("secondary", True)
            self.summary_button.setStyleSheet(button_style)
            self.summary_button.clicked.connect(self.summary_clicked.emit)
            layout.addWidget(self.summary_button)
            
            # Кнопка поиска источников
            self.references_button = QPushButton("Найти источники")
            self.references_button.setProperty("secondary", True)
            self.references_button.setStyleSheet(button_style)
            self.references_button.clicked.connect(self.references_clicked.emit)
            layout.addWidget(self.references_button)
            
            # Кнопка сохранения в библиотеку
            self.save_button = QPushButton("В библиотеку")
            self.save_button.setStyleSheet(button_style)
            self.save_button.clicked.connect(self.save_clicked.emit)
            layout.addWidget(self.save_button)
            
            # Кнопка скачивания PDF
            self.download_button = QPushButton("Скачать PDF")
            self.download_button.setStyleSheet(button_style)
            self.download_button.clicked.connect(self.download_clicked.emit)
            layout.addWidget(self.download_button)
            
        elif self.mode == "summary":
            # Кнопка копирования
            self.copy_button = QPushButton("Копировать")
            self.copy_button.setProperty("secondary", True)
            self.copy_button.setStyleSheet(button_style)
            self.copy_button.clicked.connect(self.copy_clicked.emit)
            layout.addWidget(self.copy_button)
            
            # Кнопка сохранения
            self.save_button = QPushButton("Сохранить")
            self.save_button.setStyleSheet(button_style)
            self.save_button.clicked.connect(self.save_clicked.emit)
            layout.addWidget(self.save_button)
            
        elif self.mode == "library":
            # Кнопка удаления
            self.delete_button = QPushButton("Удалить")
            self.delete_button.setProperty("warning", True)
            self.delete_button.setStyleSheet(button_style)
            self.delete_button.clicked.connect(self.delete_clicked.emit)
            layout.addWidget(self.delete_button)
            
            # Кнопка экспорта
            self.export_button = QPushButton("Экспорт")
            self.export_button.setProperty("secondary", True)
            self.export_button.setStyleSheet(button_style)
            self.export_button.clicked.connect(self.export_clicked.emit)
            layout.addWidget(self.export_button)
            
            # Кнопка скачивания PDF
            self.download_button = QPushButton("Скачать PDF")
            self.download_button.setStyleSheet(button_style)
            self.download_button.clicked.connect(self.download_clicked.emit)
            layout.addWidget(self.download_button)
            
        layout.addStretch()
        
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