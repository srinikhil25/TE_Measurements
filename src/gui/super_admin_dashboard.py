from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox,
    QGroupBox, QFormLayout, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt

from src.gui.base_dashboard import BaseDashboard
from src.database import get_db
from src.models import Lab, User, UserRole, AuditLog, AuditActionType
from src.services.statistics_service import StatisticsService
from src.gui.dialogs.create_user_dialog import CreateUserDialog
from src.gui.dialogs.create_lab_dialog import CreateLabDialog


class SuperAdminDashboard(BaseDashboard):
    """Dashboard for super administrators"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.statistics_service = StatisticsService()
        self.init_ui()
    
    def _create_role_badge(self):
        """Create role badge for super admin"""
        badge = QLabel("Super Admin")
        badge.setStyleSheet("""
            QLabel {
                background-color: #dc3545;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        return badge
    
    def init_ui(self):
        """Initialize UI components specific to super admin"""
        
        # Tab widget for different admin functions
        self.tab_widget = QTabWidget()
        
        # Statistics dashboard
        self.stats_tab = self.create_statistics_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics Dashboard")
        
        # Labs management
        self.labs_tab = self.create_labs_tab()
        self.tab_widget.addTab(self.labs_tab, "Labs Management")
        
        # Users management
        self.users_tab = self.create_users_tab()
        self.tab_widget.addTab(self.users_tab, "Users Management")
        
        # Audit logs
        self.audit_tab = self.create_audit_tab()
        self.tab_widget.addTab(self.audit_tab, "Audit Logs")
        
        self.content_layout.addWidget(self.tab_widget)
    
    def create_statistics_tab(self):
        """Create statistics dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # System statistics
        stats_label = QLabel("System-wide statistics will be displayed here")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stats_label)
        
        # Instrument usage table
        usage_group = QGroupBox("Instrument Usage Logs (Most Recent First)")
        usage_layout = QVBoxLayout()
        
        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(5)
        self.usage_table.setHorizontalHeaderLabels([
            "User", "Action", "Time", "Entity", "Details"
        ])
        self.usage_table.horizontalHeader().setStretchLastSection(True)
        
        usage_layout.addWidget(self.usage_table)
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_labs_tab(self):
        """Create labs management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_lab_button = QPushButton("Add Lab")
        add_lab_button.clicked.connect(self.add_lab)
        toolbar.addWidget(add_lab_button)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_labs)
        toolbar.addWidget(refresh_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Labs table
        self.labs_table = QTableWidget()
        self.labs_table.setColumnCount(5)
        self.labs_table.setHorizontalHeaderLabels([
            "Name", "Description", "Admin", "Members", "Actions"
        ])
        self.labs_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.labs_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_users_tab(self):
        """Create users management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_user_button = QPushButton("Add User")
        add_user_button.clicked.connect(self.add_user)
        toolbar.addWidget(add_user_button)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_users)
        toolbar.addWidget(refresh_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "Name", "Username", "Email", "Role", "Lab", "Actions"
        ])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.users_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_audit_tab(self):
        """Create audit logs tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Audit logs table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(6)
        self.audit_table.setHorizontalHeaderLabels([
            "Time", "User", "Action", "Entity", "Description", "IP Address"
        ])
        self.audit_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.audit_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """Load all dashboard data"""
        super().load_data()  # Update header
        self.load_statistics()
        self.load_labs()
        self.load_users()
        self.load_audit_logs()
    
    def load_statistics(self):
        """Load system statistics"""
        # TODO: Implement comprehensive statistics
        pass
    
    def load_labs(self):
        """Load labs table"""
        db = next(get_db())
        try:
            labs = db.query(Lab).filter(Lab.is_active == True).all()
            
            self.labs_table.setRowCount(len(labs))
            
            for row, lab in enumerate(labs):
                self.labs_table.setItem(row, 0, QTableWidgetItem(lab.name))
                self.labs_table.setItem(row, 1, QTableWidgetItem(lab.description or ""))
                self.labs_table.setItem(row, 2, QTableWidgetItem(
                    lab.admin.full_name if lab.admin else "No admin"
                ))
                member_count = len(lab.members)
                self.labs_table.setItem(row, 3, QTableWidgetItem(str(member_count)))
                
                # Actions
                edit_button = QPushButton("Edit")
                edit_button.clicked.connect(lambda checked, lab_id=lab.id: self.edit_lab(lab_id))
                self.labs_table.setCellWidget(row, 4, edit_button)
            
            self.labs_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load labs: {str(e)}")
        finally:
            db.close()
    
    def load_users(self):
        """Load users table"""
        db = next(get_db())
        try:
            users = db.query(User).filter(User.is_active == True).all()
            
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(user.full_name))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.email))
                self.users_table.setItem(row, 3, QTableWidgetItem(user.role.value))
                self.users_table.setItem(row, 4, QTableWidgetItem(
                    user.lab.name if user.lab else "No lab"
                ))
                
                # Actions
                edit_button = QPushButton("Edit")
                edit_button.clicked.connect(lambda checked, user_id=user.id: self.edit_user(user_id))
                self.users_table.setCellWidget(row, 5, edit_button)
            
            self.users_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")
        finally:
            db.close()
    
    def load_audit_logs(self):
        """Load audit logs"""
        db = next(get_db())
        try:
            logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000).all()
            
            self.audit_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.audit_table.setItem(row, 0, QTableWidgetItem(
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
                ))
                self.audit_table.setItem(row, 1, QTableWidgetItem(
                    log.user.username if log.user else "System"
                ))
                self.audit_table.setItem(row, 2, QTableWidgetItem(log.action_type.value))
                self.audit_table.setItem(row, 3, QTableWidgetItem(log.entity_type or ""))
                self.audit_table.setItem(row, 4, QTableWidgetItem(log.description or ""))
                self.audit_table.setItem(row, 5, QTableWidgetItem(log.ip_address or ""))
            
            self.audit_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit logs: {str(e)}")
        finally:
            db.close()
    
    def add_lab(self):
        """Add a new lab"""
        dialog = CreateLabDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Refresh labs table
            self.load_labs()
            QMessageBox.information(
                self,
                "Lab Created",
                f"Lab '{dialog.created_lab.name}' has been created successfully."
            )
    
    def add_user(self):
        """Add a new user"""
        dialog = CreateUserDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Refresh users table
            self.load_users()
            QMessageBox.information(
                self,
                "User Created",
                f"User '{dialog.created_user.username}' has been created successfully.\n\n"
                f"Please provide the credentials to the user."
            )
    
    def edit_lab(self, lab_id):
        """Edit a lab"""
        QMessageBox.information(self, "Info", f"Edit lab {lab_id} dialog will be implemented")
    
    def edit_user(self, user_id):
        """Edit a user"""
        QMessageBox.information(self, "Info", f"Edit user {user_id} dialog will be implemented")

