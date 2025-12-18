from typing import Optional
from src.models import User, Lab


class CurrentSession:
    """Singleton class to hold current user session and context (lab, language)"""
    _instance = None
    _user: Optional[User] = None
    _lab: Optional[Lab] = None
    _language: str = "en"  # default language
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CurrentSession, cls).__new__(cls)
        return cls._instance
    
    def set_user(self, user: User):
        """Set current user"""
        self._user = user
        # When user is set, prefer their language setting if available
        if getattr(user, "preferred_language", None):
            self._language = user.preferred_language
    
    def get_user(self) -> Optional[User]:
        """Get current user"""
        return self._user
    
    def clear(self):
        """Clear current session"""
        self._user = None
        self._lab = None
        self._language = "en"
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self._user is not None

    # Lab context ---------------------------------------------------------
    def set_lab(self, lab: Lab):
        """Set current lab context"""
        self._lab = lab

    def get_lab(self) -> Optional[Lab]:
        """Get current lab context"""
        return self._lab

    # Language context ----------------------------------------------------
    def set_language(self, language: str):
        """Set current language context ('en', 'ja', etc.)"""
        self._language = language

    def get_language(self) -> str:
        """Get current language context"""
        return self._language


class SessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.session = CurrentSession()
    
    def login(self, user: User):
        """Set user as logged in"""
        self.session.set_user(user)
    
    def logout(self):
        """Clear current session"""
        self.session.clear()
    
    def get_current_user(self) -> Optional[User]:
        """Get current logged in user"""
        return self.session.get_user()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.session.is_authenticated()

    # Lab helpers ---------------------------------------------------------
    def set_current_lab(self, lab: Lab):
        """Set current lab context"""
        self.session.set_lab(lab)

    def get_current_lab(self) -> Optional[Lab]:
        """Get current lab context"""
        return self.session.get_lab()

    # Language helpers ----------------------------------------------------
    def set_language(self, language: str):
        """Set current language context"""
        self.session.set_language(language)

    def get_language(self) -> str:
        """Get current language context"""
        return self.session.get_language()

