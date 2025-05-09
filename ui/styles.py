"""
Модуль содержит стили для пользовательского интерфейса приложения.
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

QTabWidget::pane {
    border: none;
    background: white;
}

QTabWidget::tab-bar {
    alignment: left;
}

QTabBar::tab {
    background: #f0f0f0;
    color: #666666;
    padding: 8px 16px;
    border: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    min-width: 120px;
}

QTabBar::tab:selected {
    background: white;
    color: #2196F3;
    border-bottom: 2px solid #2196F3;
}

QTabBar::tab:hover:!selected {
    background: #e0e0e0;
    color: #333333;
}

QTabBar::tab:selected:hover {
    color: #1976D2;
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

QPushButton:disabled {
    background-color: #BDBDBD;
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

QTextEdit {
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    background: white;
    padding: 8px;
    font-size: 14px;
    line-height: 1.5;
}

QTextEdit:focus {
    border: 1px solid #2196F3;
}

QListWidget {
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    background: white;
    font-size: 14px;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #EEEEEE;
}

QListWidget::item:last {
    border-bottom: none;
}

QListWidget::item:selected {
    background: #E3F2FD;
    color: #1565C0;
}

QListWidget::item:hover:!selected {
    background: #F5F5F5;
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

QStatusBar {
    background: white;
    color: #666666;
    padding: 4px 8px;
    font-size: 13px;
}

QToolBar {
    background: white;
    border-bottom: 1px solid #EEEEEE;
    spacing: 8px;
    padding: 4px;
}

QToolButton {
    border: none;
    border-radius: 4px;
    padding: 4px;
}

QToolButton:hover {
    background: #F5F5F5;
}

QToolButton:pressed {
    background: #E0E0E0;
}

QSplitter::handle {
    background: #EEEEEE;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

QLabel {
    color: #333333;
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