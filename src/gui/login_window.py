import os

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from src.auth import AuthManager


class LoginWindow(QWidget):
    """Login window for user authentication"""
    
    login_successful = pyqtSignal(object)  # Emits User object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components with university logo and modern card layout"""
        # Root layout to center the login card
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 40, 0, 40)
        root_layout.setSpacing(0)

        # Spacer at top
        root_layout.addStretch()

        # Center row
        center_row = QHBoxLayout()
        center_row.addStretch()

        # Card frame
        card = QFrame()
        card.setObjectName("loginCard")
        card.setStyleSheet(
            """
            QFrame#loginCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #d0d7de;
            }
            """
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 32, 40, 32)
        card_layout.setSpacing(20)

        # Header with logo centered above title
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "logo.png"
        )
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
                )
        card_layout.addWidget(logo_label)

        title = QLabel("TE Measurements")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Seebeck Effect Measurement Platform")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setStyleSheet("color: #666; font-size: 11px;")
        card_layout.addWidget(subtitle)

        # Login form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(36)
        self.username_input.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #d0d7de;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            """
        )
        form_layout.addRow("Username:", self.username_input)

        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(36)
        self.password_input.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #d0d7de;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            """
        )
        form_layout.addRow("Password:", self.password_input)

        card_layout.addLayout(form_layout)

        # Login button
        login_button = QPushButton("Login")
        login_button.setMinimumHeight(38)
        login_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 600;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton:disabled {
                background-color: #9fc5e8;
            }
            """
        )
        login_button.clicked.connect(self.handle_login)
        card_layout.addWidget(login_button)

        # Info about account creation (below button)
        info_label = QLabel(
            "Accounts are created by system administrators. "
            "Contact your lab admin for access."
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #888; font-size: 10px; padding-top: 4px;")
        card_layout.addWidget(info_label)

        # Allow Enter key to trigger login
        self.password_input.returnPressed.connect(self.handle_login)

        center_row.addWidget(card)
        center_row.addStretch()

        root_layout.addLayout(center_row)
        # Spacer at bottom
        root_layout.addStretch()

        self.setLayout(root_layout)
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password")
            return
        
        # Authenticate user
        user, error = self.auth_manager.authenticate(username, password)
        
        if user:
            self.login_successful.emit(user)
        else:
            QMessageBox.warning(self, "Login Failed", error or "Invalid credentials")
            self.password_input.clear()
    
    def clear_fields(self):
        """Clear input fields"""
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()

