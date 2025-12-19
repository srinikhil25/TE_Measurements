from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import Qt

from src.gui.login_window import LoginWindow
from src.gui.researcher_dashboard import ResearcherDashboard
from src.gui.lab_admin_dashboard import LabAdminDashboard
from src.gui.super_admin_dashboard import SuperAdminDashboard
from src.models import UserRole
from src.auth import SessionManager, AuthManager
from src.i18n import set_session_manager


class MainWindow(QMainWindow):
    """Main application window with shared login and role-based dashboards"""

    def __init__(self):
        super().__init__()
        self.session_manager = SessionManager()
        self.auth_manager = AuthManager()
        
        # Initialize translation system with session manager
        set_session_manager(self.session_manager)

        self.setWindowTitle("TE Measurements")
        self.setMinimumSize(1200, 800)

        # Central stacked widget for switching between views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Views
        self.login_window = LoginWindow(self)
        self.researcher_dashboard = ResearcherDashboard(self)
        self.lab_admin_dashboard = LabAdminDashboard(self)
        self.super_admin_dashboard = SuperAdminDashboard(self)

        # Add to stacked widget
        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.addWidget(self.researcher_dashboard)
        self.stacked_widget.addWidget(self.lab_admin_dashboard)
        self.stacked_widget.addWidget(self.super_admin_dashboard)

        # Connect signals
        self.login_window.login_successful.connect(self.on_login_successful)

        # Connect logout signals from all dashboards
        self.researcher_dashboard.logout_requested.connect(self.on_logout)
        self.lab_admin_dashboard.logout_requested.connect(self.on_logout)
        self.super_admin_dashboard.logout_requested.connect(self.on_logout)

        # Show login initially for all roles
        self.show_login()
    
    def show_login(self):
        """Show login window (shared by all roles)."""
        self.stacked_widget.setCurrentWidget(self.login_window)
        self.login_window.clear_fields()

    def on_login_successful(self, user):
        """Handle successful login"""
        self.session_manager.login(user)
        self.show_dashboard_for_user(user)
    
    def show_dashboard_for_user(self, user):
        """Show appropriate dashboard based on user role"""
        if user.role == UserRole.RESEARCHER:
            self.researcher_dashboard.load_data()
            self.stacked_widget.setCurrentWidget(self.researcher_dashboard)
        elif user.role == UserRole.LAB_ADMIN:
            self.lab_admin_dashboard.load_data()
            self.stacked_widget.setCurrentWidget(self.lab_admin_dashboard)
        elif user.role == UserRole.SUPER_ADMIN:
            self.super_admin_dashboard.load_data()
            self.stacked_widget.setCurrentWidget(self.super_admin_dashboard)
        else:
            QMessageBox.warning(self, "Error", "Unknown user role")
            self.show_login()
    
    def on_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_manager.logout()
            self.show_login()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.session_manager.is_authenticated():
            reply = QMessageBox.question(
                self,
                "Exit",
                "Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.session_manager.logout()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

