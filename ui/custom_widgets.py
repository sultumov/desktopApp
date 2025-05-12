from PyQt6.QtWidgets import QSplitter, QFrame, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QEvent, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QMouseEvent, QIcon

class CustomSplitter(QSplitter):
    """Расширенный класс разделителя с возможностью сохранения размеров."""
    
    splitterMoved = pyqtSignal(str, list)
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, name="default"):
        """Инициализирует настраиваемый разделитель.
        
        Args:
            orientation: Ориентация разделителя (горизонтальная или вертикальная)
            name: Уникальное имя разделителя для сохранения настроек
        """
        super().__init__(orientation)
        self.name = name
        self.setHandleWidth(6)
        self.setChildrenCollapsible(False)
        
        # Стиль для разделителя
        self.setStyleSheet("""
            QSplitter::handle {
                background-color: #E0E0E0;
                border-radius: 3px;
            }
            QSplitter::handle:hover {
                background-color: #2196F3;
            }
            QSplitter::handle:pressed {
                background-color: #1976D2;
            }
        """)
        
    def moveEvent(self, event):
        """Переопределение метода для отслеживания перемещения разделителя."""
        super().moveEvent(event)
        sizes = self.sizes()
        self.splitterMoved.emit(self.name, sizes)
        
    def setSizes(self, sizes):
        """Устанавливает размеры разделителя.
        
        Args:
            sizes: Список размеров для каждой панели
        """
        if sizes:
            super().setSizes(sizes)


class CollapsiblePanel(QWidget):
    """Панель, которая может сворачиваться и разворачиваться."""
    
    collapsed = pyqtSignal(bool)
    
    def __init__(self, title="Панель", parent=None):
        """Инициализирует сворачиваемую панель.
        
        Args:
            title: Заголовок панели
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.is_collapsed = False
        self.title = title
        self.content = None
        self.animation_duration = 300
        
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс панели."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Заголовок панели
        self.header = QWidget()
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
        """)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        # Заголовок
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333333;
            }
        """)
        
        # Кнопка сворачивания
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon("ui/icons/collapse.svg"))
        self.toggle_button.setFixedSize(24, 24)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #E0E0E0;
                border-radius: 12px;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_collapsed)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_button)
        
        # Контейнер содержимого
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.header)
        layout.addWidget(self.content_container)
        
    def set_content(self, widget):
        """Устанавливает содержимое панели.
        
        Args:
            widget: Виджет для отображения в панели
        """
        if self.content:
            self.content_layout.removeWidget(self.content)
            self.content.deleteLater()
            
        self.content = widget
        self.content_layout.addWidget(widget)
        
    def toggle_collapsed(self):
        """Переключает состояние панели (свернута/развернута)."""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.toggle_button.setIcon(QIcon("ui/icons/expand.svg"))
            self.content_container.setVisible(False)
        else:
            self.toggle_button.setIcon(QIcon("ui/icons/collapse.svg"))
            self.content_container.setVisible(True)
            
        self.collapsed.emit(self.is_collapsed)
        

class DraggableTabWidget(QWidget):
    """Панель с вкладками, которые можно перетаскивать."""
    
    tabMoved = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        """Инициализирует панель с перетаскиваемыми вкладками.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.drag_start_pos = None
        self.tab_under_mouse = -1
        self.drag_tab_index = -1
        
        self.setup_ui()
        
    def setup_ui(self):
        """Настраивает интерфейс панели."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Панель вкладок
        self.tab_bar = QWidget()
        self.tab_bar.setFixedHeight(40)
        self.tab_bar.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        
        self.tab_layout = QHBoxLayout(self.tab_bar)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(0)
        
        # Контейнер содержимого
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout.addWidget(self.tab_bar)
        self.layout.addWidget(self.content_container) 