"""
Base Dashboard Class
Provides common functionality for all role-based dashboards
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.auth import SessionManager
from src.models import User
from src.i18n import tr


class BaseDashboard(QWidget):
    """
    Base class for all role-based dashboards.
    Provides common UI elements and functionality.
    """
    
    logout_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager()
        self.current_user = None
        self._setup_base_ui()
    
    def _setup_base_ui(self):
        """Setup base UI components (header, layout)"""
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create header
        self.header_widget = self._create_header()
        self.main_layout.addWidget(self.header_widget)
        
        # Content area (to be populated by subclasses)
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        
        self.setLayout(self.main_layout)
    
    def _create_header(self) -> QWidget:
        """Create common header with welcome message and logout button"""
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Welcome label (will be updated when user loads)
        self.welcome_label = QLabel(tr("dashboard.welcome"))
        welcome_font = QFont()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        self.welcome_label.setFont(welcome_font)
        header_layout.addWidget(self.welcome_label)
        
        # Role badge (optional, can be overridden)
        # Will be created/refreshed in update_header() after login
        self.role_badge = None
        
        header_layout.addStretch()
        
        # User info (optional)
        self.user_info_label = QLabel()
        self.user_info_label.setStyleSheet("color: #666; font-size: 11px;")
        header_layout.addWidget(self.user_info_label)
        
        # Logout button
        self.logout_button = QPushButton(tr("dashboard.logout"))
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 6px 15px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.logout_button.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(self.logout_button)
        
        header_widget.setLayout(header_layout)
        return header_widget
    
    def _create_role_badge(self) -> QLabel:
        """
        Create role badge. Override in subclasses for custom badges.
        Returns None if no badge needed.
        """
        return None
    
    def _get_role_display_name(self) -> str:
        """
        Get display name for the role.
        Override in subclasses to customize.
        """
        user = self.session_manager.get_current_user()
        if user:
            role_map = {
                "researcher": "Researcher",
                "lab_admin": "Lab Administrator",
                "super_admin": "Super Administrator"
            }
            return role_map.get(user.role.value, "User")
        return "User"
    
    def update_header(self):
        """Update header with current user information"""
        user = self.session_manager.get_current_user()
        if user:
            self.current_user = user
            # Translate welcome message with user's name
            welcome_text = tr("dashboard.welcome")
            self.welcome_label.setText(f"{welcome_text}, {user.full_name}")

            # Update role badge with translated text
            if self.role_badge:
                # Remove old badge
                self.role_badge.setParent(None)
            self.role_badge = self._create_role_badge()
            if self.role_badge:
                # Find the header layout and insert badge after welcome label
                header_layout = self.header_widget.layout()
                if header_layout:
                    header_layout.insertWidget(1, self.role_badge)

            # Update logout button text
            if hasattr(self, 'logout_button') and self.logout_button:
                self.logout_button.setText(tr("dashboard.logout"))

            # For now, only show the role in the header to avoid lazy-loading
            # relationships (like user.lab) on detached instances.
            self.user_info_label.setText(self._get_role_display_name())
    
    def load_data(self):
        """
        Load dashboard data. Must be implemented by subclasses.
        This method is called when the dashboard is shown.
        """
        self.update_header()
        # Subclasses should override this method
    
    def refresh(self):
        """Refresh dashboard data"""
        self.load_data()
    
    def get_current_user(self) -> User:
        """Get current logged-in user"""
        return self.session_manager.get_current_user()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.session_manager.is_authenticated()

