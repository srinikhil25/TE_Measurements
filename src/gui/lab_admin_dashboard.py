from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta

from src.gui.base_dashboard import BaseDashboard
from src.database import get_db
from src.models import User, Workbook, Measurement, UserRole
from src.services.statistics_service import StatisticsService


class LabAdminDashboard(BaseDashboard):
    """Dashboard for lab administrators"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.statistics_service = StatisticsService()
        self.init_ui()
    
    def _create_role_badge(self):
        """Create role badge for lab admin"""
        badge = QLabel("Lab Admin")
        badge.setStyleSheet("""
            QLabel {
                background-color: #28a745;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        return badge
    
    def init_ui(self):
        """Initialize UI components specific to lab admin"""
        
        # Statistics section
        stats_group = QGroupBox("Lab Statistics")
        stats_layout = QVBoxLayout()
        
        # Date range selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date Range:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("to"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        refresh_stats_button = QPushButton("Refresh Statistics")
        refresh_stats_button.clicked.connect(self.load_statistics)
        date_layout.addWidget(refresh_stats_button)
        
        stats_layout.addLayout(date_layout)
        
        # Statistics display (placeholder)
        self.stats_label = QLabel("Statistics will be displayed here")
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        self.content_layout.addWidget(stats_group)
        
        # Researchers table
        researchers_group = QGroupBox("Researchers in Lab")
        researchers_layout = QVBoxLayout()
        
        self.researchers_table = QTableWidget()
        self.researchers_table.setColumnCount(4)
        self.researchers_table.setHorizontalHeaderLabels([
            "Name", "Username", "Workbooks", "Last Activity"
        ])
        self.researchers_table.horizontalHeader().setStretchLastSection(True)
        self.researchers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.researchers_table.doubleClicked.connect(self.view_researcher_work)
        
        researchers_layout.addWidget(self.researchers_table)
        researchers_group.setLayout(researchers_layout)
        self.content_layout.addWidget(researchers_group)
    
    def load_data(self):
        """Load lab admin dashboard data"""
        super().load_data()  # Update header
        self.load_researchers()
        self.load_statistics()
    
    def load_researchers(self):
        """Load researchers in the lab"""
        user = self.get_current_user()
        if not user or not user.lab_id:
            return
        
        db = next(get_db())
        try:
            researchers = db.query(User).filter(
                User.lab_id == user.lab_id,
                User.role == UserRole.RESEARCHER,
                User.is_active == True
            ).all()
            
            self.researchers_table.setRowCount(len(researchers))
            
            for row, researcher in enumerate(researchers):
                # Count workbooks
                workbook_count = db.query(Workbook).filter(
                    Workbook.researcher_id == researcher.id,
                    Workbook.is_active == True
                ).count()
                
                self.researchers_table.setItem(row, 0, QTableWidgetItem(researcher.full_name))
                self.researchers_table.setItem(row, 1, QTableWidgetItem(researcher.username))
                self.researchers_table.setItem(row, 2, QTableWidgetItem(str(workbook_count)))
                self.researchers_table.setItem(row, 3, QTableWidgetItem(
                    researcher.last_login.strftime("%Y-%m-%d %H:%M") if researcher.last_login else "Never"
                ))
            
            self.researchers_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load researchers: {str(e)}")
        finally:
            db.close()
    
    def load_statistics(self):
        """Load and display statistics"""
        # TODO: Implement comprehensive statistics
        self.stats_label.setText("Statistics loading...")
    
    def view_researcher_work(self, index):
        """View a researcher's workbooks"""
        # TODO: Implement researcher work viewer
        QMessageBox.information(self, "Info", "Researcher work viewer will be implemented")

