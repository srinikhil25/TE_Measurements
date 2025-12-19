from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QTextEdit,
    QApplication,
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session
import secrets
import string

from src.database import get_db
from src.models import User, UserRole, Lab
from src.auth import AuthManager


class CreateUserDialog(QDialog):
    """Dialog for super admins to create new users"""

    def __init__(
        self,
        parent=None,
        preset_role: UserRole | None = None,
        preset_lab_id: int | None = None,
    ):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        self.created_user = None
        self._preset_role = preset_role
        self._preset_lab_id = preset_lab_id
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
        
        # Apply any presets for role/lab after combos are populated
        self._apply_presets()

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

    def _apply_presets(self):
        """Apply optional preset role/lab (used from lab profile window)."""
        if self._preset_role is not None:
            role_text_map = {
                UserRole.RESEARCHER: "Researcher",
                UserRole.LAB_ADMIN: "Lab Admin",
                UserRole.SUPER_ADMIN: "Super Admin",
            }
            text = role_text_map.get(self._preset_role)
            if text:
                index = self.role_combo.findText(text)
                if index >= 0:
                    self.role_combo.setCurrentIndex(index)
                    # Lock role to avoid accidental change
                    self.role_combo.setEnabled(False)

        if self._preset_lab_id is not None:
            index = self.lab_combo.findData(self._preset_lab_id)
            if index >= 0:
                self.lab_combo.setCurrentIndex(index)
                # Lock lab to keep user tied to this lab
                self.lab_combo.setEnabled(False)
    
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
        """Create the user.

        Password is generated automatically as a unique, random
        alphanumeric string (8–16 chars). Super admin never types it.
        """
        # Validate inputs
        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        role_text = self.role_combo.currentText()
        lab_id = self.lab_combo.currentData()
        
        # Validation
        if not all([full_name, username, email]):
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields")
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

            # Generate a unique random password (8–16 chars, alphanumeric)
            password = self._generate_unique_password(db)
            
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

            # Enhanced success dialog with styled credentials and copy support
            msg = QMessageBox(self)
            msg.setWindowTitle("User Created")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(
                "<b>User '{username}' created successfully.</b><br><br>"
                "<span style='color:#555;'>Provide these credentials to the user. "
                "<b>The password will only be shown once.</b></span><br><br>"
                "<table style='font-size:12px;'>"
                "<tr><td align='right'><b>Username:&nbsp;</b></td>"
                "<td><code style='background-color:#f5f5f5; padding:2px 6px;'>{username}</code></td></tr>"
                "<tr><td align='right'><b>Password:&nbsp;</b></td>"
                "<td><code style='background-color:#fff3cd; padding:2px 6px;'>{password}</code></td></tr>"
                "</table>"
            .format(username=username, password=password)
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            copy_btn = msg.addButton(
                "Copy Password", QMessageBox.ButtonRole.ActionRole
            )

            msg.exec()

            if msg.clickedButton() == copy_btn:
                QApplication.clipboard().setText(password)

            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")
        finally:
            db.close()

    def _generate_unique_password(self, db: Session, min_len: int = 8, max_len: int = 16) -> str:
        """Generate a unique, random alphanumeric password.

        Ensures (with extremely high probability) that no existing user's
        password matches by checking against all stored password hashes.
        """
        alphabet = string.ascii_letters + string.digits
        length_range = list(range(min_len, max_len + 1))

        while True:
            length = secrets.choice(length_range)
            candidate = "".join(secrets.choice(alphabet) for _ in range(length))

            # Check uniqueness vs existing users' passwords
            users = db.query(User).all()
            if all(not u.check_password(candidate) for u in users):
                return candidate

