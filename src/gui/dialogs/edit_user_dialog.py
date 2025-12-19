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
    QCheckBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session
import secrets
import string

from src.database import get_db
from src.models import User, UserRole, Lab


class EditUserDialog(QDialog):
    """Dialog for super admins to view and edit existing users."""

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user: User | None = None
        self.init_ui()
        self.load_user()

    def init_ui(self):
        self.setWindowTitle("Edit User")
        self.setMinimumWidth(520)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Info label
        info_label = QLabel(
            "Update user profile, role and lab assignment. "
            "You can also reset the password if needed."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Full Name
        self.full_name_input = QLineEdit()
        form_layout.addRow("Full Name *:", self.full_name_input)

        # Username (read-only)
        self.username_display = QLineEdit()
        self.username_display.setReadOnly(True)
        self.username_display.setStyleSheet(
            "QLineEdit { background-color: #f5f5f5; }"
        )
        form_layout.addRow("Username:", self.username_display)

        # Email
        self.email_input = QLineEdit()
        form_layout.addRow("Email *:", self.email_input)

        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Researcher", "Lab Admin", "Super Admin"])
        form_layout.addRow("Role *:", self.role_combo)

        # Lab (for researchers and lab admins)
        self.lab_combo = QComboBox()
        self.lab_combo.addItem("Select Lab", None)
        self._load_labs()
        form_layout.addRow("Lab *:", self.lab_combo)

        # Preferred language
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("日本語", "ja")
        form_layout.addRow("Preferred Language:", self.language_combo)

        # Status flags
        status_row = QHBoxLayout()
        self.active_checkbox = QCheckBox("Active")
        self.locked_checkbox = QCheckBox("Locked")
        status_row.addWidget(self.active_checkbox)
        status_row.addWidget(self.locked_checkbox)
        status_row.addStretch()
        form_layout.addRow("Status:", status_row)

        # Last login (read-only)
        self.last_login_label = QLabel("-")
        self.last_login_label.setStyleSheet("color: #666;")
        form_layout.addRow("Last Login:", self.last_login_label)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        reset_button = QPushButton("Reset Password")
        reset_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ffc107;
                color: #000;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            """
        )
        reset_button.clicked.connect(self.reset_password)
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save Changes")
        save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            """
        )
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_labs(self):
        db = next(get_db())
        try:
            labs = db.query(Lab).filter(Lab.is_active == True).all()  # noqa: E712
            for lab in labs:
                self.lab_combo.addItem(lab.name, lab.id)
        except Exception as e:
            print(f"Error loading labs: {e}")
        finally:
            db.close()

    def load_user(self):
        """Populate form fields with existing user data."""
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == self.user_id).first()
            if not user:
                QMessageBox.warning(self, "Not Found", "User not found.")
                self.reject()
                return

            self.user = user
            self.full_name_input.setText(user.full_name or "")
            self.username_display.setText(user.username or "")
            self.email_input.setText(user.email or "")

            # Role
            role_text_map = {
                UserRole.RESEARCHER: "Researcher",
                UserRole.LAB_ADMIN: "Lab Admin",
                UserRole.SUPER_ADMIN: "Super Admin",
            }
            role_text = role_text_map.get(user.role, "Researcher")
            idx = self.role_combo.findText(role_text)
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)

            # Lab
            if user.lab_id:
                lab_idx = self.lab_combo.findData(user.lab_id)
                if lab_idx >= 0:
                    self.lab_combo.setCurrentIndex(lab_idx)

            # Preferred language
            lang_code = user.preferred_language or "en"
            lang_idx = self.language_combo.findData(lang_code)
            if lang_idx >= 0:
                self.language_combo.setCurrentIndex(lang_idx)

            # Status
            self.active_checkbox.setChecked(bool(user.is_active))
            self.locked_checkbox.setChecked(bool(user.is_locked))

            # Last login
            if user.last_login:
                self.last_login_label.setText(
                    user.last_login.strftime("%Y-%m-%d %H:%M")
                )
            else:
                self.last_login_label.setText("Never")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load user: {str(e)}")
        finally:
            db.close()

    def save_changes(self):
        """Validate and persist user changes."""
        if not self.user:
            return

        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role_text = self.role_combo.currentText()
        lab_id = self.lab_combo.currentData()
        is_active = self.active_checkbox.isChecked()
        is_locked = self.locked_checkbox.isChecked()
        preferred_language = self.language_combo.currentData()

        if not full_name or not email:
            QMessageBox.warning(
                self, "Validation Error", "Full name and email are required."
            )
            return

        role_map = {
            "Researcher": UserRole.RESEARCHER,
            "Lab Admin": UserRole.LAB_ADMIN,
            "Super Admin": UserRole.SUPER_ADMIN,
        }
        role = role_map[role_text]

        if role in [UserRole.RESEARCHER, UserRole.LAB_ADMIN] and not lab_id:
            QMessageBox.warning(
                self, "Validation Error", "Please select a lab for this user."
            )
            return

        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == self.user_id).first()
            if not user:
                QMessageBox.warning(self, "Not Found", "User not found.")
                return

            user.full_name = full_name
            user.email = email
            user.role = role
            user.lab_id = lab_id if role != UserRole.SUPER_ADMIN else None
            user.is_active = is_active
            user.is_locked = is_locked
            user.preferred_language = preferred_language or "en"

            db.commit()
            db.refresh(user)
            self.user = user

            QMessageBox.information(
                self,
                "User Updated",
                "User details have been updated successfully.",
            )
            self.accept()

        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to update user: {str(e)}")
        finally:
            db.close()

    def reset_password(self):
        """Generate and set a new unique password, then show it once."""
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == self.user_id).first()
            if not user:
                QMessageBox.warning(self, "Not Found", "User not found.")
                return

            new_password = self._generate_unique_password(db)

            user.set_password(new_password)
            user.is_locked = False
            user.failed_login_attempts = 0

            db.commit()

            # Show styled one-time password dialog
            msg = QMessageBox(self)
            msg.setWindowTitle("Password Reset")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(
                "<b>Password reset successfully.</b><br><br>"
                "<span style='color:#555;'>Provide these new credentials to the user. "
                "<b>The password will only be shown once.</b></span><br><br>"
                "<table style='font-size:12px;'>"
                "<tr><td align='right'><b>Username:&nbsp;</b></td>"
                "<td><code style='background-color:#f5f5f5; padding:2px 6px;'>{username}</code></td></tr>"
                "<tr><td align='right'><b>Password:&nbsp;</b></td>"
                "<td><code style='background-color:#fff3cd; padding:2px 6px;'>{password}</code></td></tr>"
                "</table>".format(username=user.username, password=new_password)
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            copy_btn = msg.addButton(
                "Copy Password", QMessageBox.ButtonRole.ActionRole
            )

            msg.exec()

            if msg.clickedButton() == copy_btn:
                QApplication.clipboard().setText(new_password)

        except Exception as e:
            db.rollback()
            QMessageBox.critical(
                self, "Error", f"Failed to reset password: {str(e)}"
            )
        finally:
            db.close()

    def _generate_unique_password(
        self, db: Session, min_len: int = 8, max_len: int = 16
    ) -> str:
        """Generate a unique, random alphanumeric password."""
        alphabet = string.ascii_letters + string.digits
        length_range = list(range(min_len, max_len + 1))

        while True:
            length = secrets.choice(length_range)
            candidate = "".join(secrets.choice(alphabet) for _ in range(length))

            users = db.query(User).all()
            if all(not u.check_password(candidate) for u in users):
                return candidate


