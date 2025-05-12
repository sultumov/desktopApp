"""Пакет утилит для приложения ArXiv Assistant."""

from .file_utils import save_text_to_file, ensure_dir_exists, export_article_to_file, open_file, confirm_file_action
from .ui_utils import copy_to_clipboard, show_info_message, show_error_message, show_warning_message, set_status_message, delay_call, confirm_action
from .error_utils import log_exception, safe_execute, exception_handler, gui_exception_handler
from .pdf_utils import download_pdf, is_valid_pdf, get_pdf_info
from .settings_utils import load_json_settings, save_json_settings, load_env_settings, save_env_settings, get_config_dir, get_user_data_dir
from .user_settings_utils import UserSettingsManager

__all__ = [
    # Файловые утилиты
    'save_text_to_file', 'ensure_dir_exists', 'export_article_to_file', 'open_file', 'confirm_file_action',
    
    # UI утилиты
    'copy_to_clipboard', 'show_info_message', 'show_error_message', 'show_warning_message', 
    'set_status_message', 'delay_call', 'confirm_action',
    
    # Обработка ошибок
    'log_exception', 'safe_execute', 'exception_handler', 'gui_exception_handler',
    
    # PDF утилиты
    'download_pdf', 'is_valid_pdf', 'get_pdf_info',
    
    # Утилиты для настроек
    'load_json_settings', 'save_json_settings', 'load_env_settings', 'save_env_settings',
    'get_config_dir', 'get_user_data_dir', 'UserSettingsManager',
] 