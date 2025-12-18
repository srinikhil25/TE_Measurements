from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QComboBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, UserRole, Lab
from src.auth import AuthManager


class CreateUserDialog(QDialog):
    """Dialog for super admins to create new users"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        self.created_user = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Create New User")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Info label
        info_label = QLabel(
            "Only super admins can create user accounts. "
            "Users will receive their credentials from the administrator."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Full Name
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Enter full name")
        form_layout.addRow("Full Name *:", self.full_name_input)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username *:", self.username_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        form_layout.addRow("Email *:", self.email_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Researcher", "Lab Admin", "Super Admin"])
        form_layout.addRow("Role *:", self.role_combo)
        
        # Lab (for researchers and lab admins)
        self.lab_combo = QComboBox()
        self.lab_combo.addItem("Select Lab", None)
        self.load_labs()
        form_layout.addRow("Lab *:", self.lab_combo)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password (min 8 characters)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password *:", self.password_input)
        
        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Confirm Password *:", self.confirm_password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        create_button = QPushButton("Create User")
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        create_button.clicked.connect(self.create_user)
        button_layout.addWidget(create_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_labs(self):
        """Load available labs"""
        db = next(get_db())
        try:
            labs = db.query(Lab).filter(Lab.is_active == True).all()
            for lab in labs:
                self.lab_combo.addItem(lab.name, lab.id)
        except Exception as e:
            print(f"Error loading labs: {e}")
        finally:
            db.close()
    
    def create_user(self):
        """Create the user"""
        # Validate inputs
        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role_text = self.role_combo.currentText()
        lab_id = self.lab_combo.currentData()
        
        # Validation
        if not all([full_name, username, email, password]):
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match")
            return
        
        if len(password) < 8:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 8 characters")
            return
        
        # Map role text to enum
        role_map = {
            "Researcher": UserRole.RESEARCHER,
            "Lab Admin": UserRole.LAB_ADMIN,
            "Super Admin": UserRole.SUPER_ADMIN
        }
        role = role_map[role_text]
        
        # Lab is required for researchers and lab admins
        if role in [UserRole.RESEARCHER, UserRole.LAB_ADMIN] and not lab_id:
            QMessageBox.warning(self, "Validation Error", "Please select a lab for this user")
            return
        
        # Create user
        db = next(get_db())
        try:
            # Check if username already exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                QMessageBox.warning(self, "Error", f"Username '{username}' already exists")
                return
            
            # Check if email already exists
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                QMessageBox.warning(self, "Error", f"Email '{email}' is already registered")
                return
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                lab_id=lab_id if role != UserRole.SUPER_ADMIN else None,
                is_active=True
            )
            new_user.set_password(password)
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            self.created_user = new_user
            
            QMessageBox.information(
                self,
                "Success",
                f"User '{username}' created successfully!\n\n"
                f"Please provide these credentials to the user:\n"
                f"Username: {username}\n"
                f"Password: {password}"
            )
            
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")
        finally:
            db.close()

