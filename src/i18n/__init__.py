"""
Internationalization (i18n) module for TE Measurements
Handles translation of static UI content based on user's preferred language.
"""

import json
import os
from typing import Dict, Optional

from src.auth import SessionManager


class TranslationManager:
    """Manages translations for static UI content"""
    
    _instance: Optional['TranslationManager'] = None
    _translations: Dict[str, Dict[str, str]] = {}
    _session_manager: Optional[SessionManager] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
            cls._instance._load_translations()
        return cls._instance
    
    def _load_translations(self):
        """Load translation files for all supported languages"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        translations_dir = os.path.join(base_dir, 'translations')
        
        for lang_code in ['en', 'ja']:
            json_path = os.path.join(translations_dir, f'{lang_code}.json')
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load translations for {lang_code}: {e}")
                    self._translations[lang_code] = {}
            else:
                self._translations[lang_code] = {}
    
    def set_session_manager(self, session_manager: SessionManager):
        """Set the session manager to get current language"""
        self._session_manager = session_manager
    
    def get_current_language(self) -> str:
        """Get current language from session, default to 'en'"""
        if self._session_manager:
            return self._session_manager.get_language() or 'en'
        return 'en'
    
    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Translate a key to the current language.
        Supports nested keys with dot notation (e.g., "dashboard.welcome").
        
        Args:
            key: Translation key (e.g., "dashboard.welcome")
            default: Fallback text if key not found (defaults to key itself)
        
        Returns:
            Translated string or default/key if not found
        """
        lang = self.get_current_language()
        translations = self._translations.get(lang, {})
        
        # Handle nested keys with dot notation (e.g., "dashboard.welcome")
        def get_nested_value(d: dict, k: str):
            """Get value from nested dict using dot notation"""
            keys = k.split('.')
            current = d
            for k_part in keys:
                if isinstance(current, dict):
                    current = current.get(k_part)
                    if current is None:
                        return None
                else:
                    return None
            return current if isinstance(current, str) else None
        
        # Try to get translation
        value = get_nested_value(translations, key)
        if value:
            return value
        
        # Fallback to English if current language doesn't have it
        if lang != 'en':
            en_translations = self._translations.get('en', {})
            value = get_nested_value(en_translations, key)
            if value:
                return value
        
        # Return default or key itself
        return default if default is not None else key
    
    def reload(self):
        """Reload translation files (useful after language change)"""
        self._load_translations()


# Global translation function for convenience
_translation_manager = TranslationManager()


def tr(key: str, default: Optional[str] = None) -> str:
    """
    Translate a key to the current user's language.
    
    Usage:
        label.setText(tr("login.title"))
        button.setText(tr("button.save", "Save"))
    
    Args:
        key: Translation key (dot-separated, e.g., "login.title")
        default: Optional fallback text if key not found
    
    Returns:
        Translated string
    """
    return _translation_manager.translate(key, default)


def set_session_manager(session_manager: SessionManager):
    """Set session manager for translation manager"""
    _translation_manager.set_session_manager(session_manager)


def reload_translations():
    """Reload translation files"""
    _translation_manager.reload()

