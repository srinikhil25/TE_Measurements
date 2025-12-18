from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Lab


class CreateLabDialog(QDialog):
    """Dialog for super admins to create new labs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.created_lab = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Create New Lab")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Lab Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter lab name")
        form_layout.addRow("Lab Name *:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter lab description (optional)")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter lab location (optional)")
        form_layout.addRow("Location:", self.location_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        create_button = QPushButton("Create Lab")
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
        create_button.clicked.connect(self.create_lab)
        button_layout.addWidget(create_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_lab(self):
        """Create the lab"""
        # Validate inputs
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        location = self.location_input.text().strip()
        
        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Lab name is required")
            return
        
        # Create lab
        db = next(get_db())
        try:
            # Check if lab name already exists
            existing_lab = db.query(Lab).filter(Lab.name == name).first()
            if existing_lab:
                QMessageBox.warning(self, "Error", f"Lab '{name}' already exists")
                return
            
            # Create new lab
            new_lab = Lab(
                name=name,
                description=description if description else None,
                location=location if location else None,
                is_active=True
            )
            
            db.add(new_lab)
            db.commit()
            db.refresh(new_lab)
            
            self.created_lab = new_lab
            
            QMessageBox.information(
                self,
                "Success",
                f"Lab '{name}' created successfully!"
            )
            
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to create lab: {str(e)}")
        finally:
            db.close()

