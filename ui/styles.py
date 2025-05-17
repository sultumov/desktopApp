"""
Модуль содержит стили для пользовательского интерфейса приложения.
"""

MAIN_STYLE = """
/* Основные стили */
QWidget {
    color: #2C3E50;
    font-size: 14px;
}

/* Заголовки */
QLabel[heading="true"] {
    color: #2C3E50;
    font-size: 20px;
    font-weight: bold;
}

/* Подзаголовки */
QLabel[subheading="true"] {
    color: #34495E;
    font-size: 16px;
    font-weight: bold;
}

/* Обычный текст */
QLabel {
    color: #2C3E50;
}

/* Поля ввода */
QLineEdit {
    color: #2C3E50;
    background: white;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
    padding: 8px;
}

QLineEdit:focus {
    border: 1px solid #3498DB;
}

/* Выпадающие списки */
QComboBox {
    color: #2C3E50;
    background: white;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
    padding: 8px;
}

QComboBox:hover {
    border: 1px solid #3498DB;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(ui/icons/down-arrow.svg);
    width: 12px;
    height: 12px;
}

/* Кнопки */
QPushButton {
    color: white;
    background-color: #3498DB;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 100px;
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

/* Списки */
QListWidget {
    color: #2C3E50;
    background: white;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
}

QListWidget::item {
    color: #2C3E50;
    padding: 8px;
}

QListWidget::item:selected {
    color: white;
    background: #3498DB;
}

QListWidget::item:hover {
    background: #ECF0F1;
}

/* Вкладки */
QTabWidget::pane {
    border: none;
    background: white;
}

QTabBar::tab {
    color: #7F8C8D;
    background: #ECF0F1;
    padding: 8px 16px;
    border: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    min-width: 120px;
}

QTabBar::tab:selected {
    color: #2980B9;
    background: white;
    border-bottom: 2px solid #3498DB;
}

QTabBar::tab:hover:!selected {
    color: #2C3E50;
    background: #BDC3C7;
}

/* Полосы прокрутки */
QScrollBar:vertical {
    border: none;
    background: #ECF0F1;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #BDC3C7;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #95A5A6;
}

QScrollBar:horizontal {
    border: none;
    background: #ECF0F1;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #BDC3C7;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #95A5A6;
}

/* Строка состояния */
QStatusBar {
    color: #7F8C8D;
    background: white;
    border-top: 1px solid #ECF0F1;
}

/* Разделители */
QSplitter::handle {
    background: #ECF0F1;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

/* Панель инструментов */
QToolBar {
    background: white;
    border-bottom: 1px solid #ECF0F1;
    spacing: 8px;
    padding: 4px;
}

QToolButton {
    color: #2C3E50;
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
}

QToolButton:hover {
    background: #ECF0F1;
}

QToolButton:pressed {
    background: #BDC3C7;
}

/* Текстовые области */
QTextEdit, QPlainTextEdit {
    color: #2C3E50;
    background: white;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
    padding: 8px;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3498DB;
}

/* Спиннеры */
QSpinBox {
    color: #2C3E50;
    background: white;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
    padding: 8px;
}

QSpinBox:focus {
    border: 1px solid #3498DB;
}
"""

DIALOG_STYLE = """
QDialog {
    background-color: white;
}

QLabel {
    color: #333333;
}

QLineEdit {
    padding: 8px;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    background: white;
}

QLineEdit:focus {
    border: 1px solid #2196F3;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QComboBox {
    padding: 8px;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    background: white;
}

QComboBox:hover {
    border: 1px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(ui/icons/down-arrow.svg);
    width: 12px;
    height: 12px;
}

QDialogButtonBox {
    button-layout: spread;
}
""" 