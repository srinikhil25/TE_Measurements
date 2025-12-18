from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QGroupBox, QFormLayout, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session

from src.gui.base_dashboard import BaseDashboard
from src.database import get_db
from src.models import Workbook, Measurement, MeasurementType
from src.services.workbook_service import WorkbookService
from src.services.measurement_service import MeasurementService


class ResearcherDashboard(BaseDashboard):
    """Dashboard for researchers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbook_service = WorkbookService()
        self.measurement_service = MeasurementService()
        self.init_ui()
    
    def _create_role_badge(self):
        """Create role badge for researcher"""
        badge = QLabel("Researcher")
        badge.setStyleSheet("""
            QLabel {
                background-color: #17a2b8;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        return badge
    
    def init_ui(self):
        """Initialize UI components specific to researcher"""
        # Main content area
        self.tab_widget = QTabWidget()
        
        # Workbooks tab
        self.workbooks_tab = self.create_workbooks_tab()
        self.tab_widget.addTab(self.workbooks_tab, "My Workbooks")
        
        self.content_layout.addWidget(self.tab_widget)
    
    def create_workbooks_tab(self):
        """Create workbooks management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        create_button = QPushButton("Create New Workbook")
        create_button.clicked.connect(self.create_workbook)
        toolbar.addWidget(create_button)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_button)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Workbooks table
        self.workbooks_table = QTableWidget()
        self.workbooks_table.setColumnCount(5)
        self.workbooks_table.setHorizontalHeaderLabels([
            "Title", "Sample Name", "Created", "Last Measurement", "Actions"
        ])
        self.workbooks_table.horizontalHeader().setStretchLastSection(True)
        self.workbooks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.workbooks_table.doubleClicked.connect(self.open_workbook)
        
        layout.addWidget(self.workbooks_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """Load researcher's workbooks"""
        super().load_data()  # Update header
        
        user = self.get_current_user()
        if not user:
            return
        
        db = next(get_db())
        try:
            workbooks = db.query(Workbook).filter(
                Workbook.researcher_id == user.id,
                Workbook.is_active == True
            ).order_by(Workbook.created_at.desc()).all()
            
            self.workbooks_table.setRowCount(len(workbooks))
            
            for row, workbook in enumerate(workbooks):
                self.workbooks_table.setItem(row, 0, QTableWidgetItem(workbook.title))
                self.workbooks_table.setItem(row, 1, QTableWidgetItem(workbook.sample_name or ""))
                self.workbooks_table.setItem(row, 2, QTableWidgetItem(
                    workbook.created_at.strftime("%Y-%m-%d %H:%M") if workbook.created_at else ""
                ))
                self.workbooks_table.setItem(row, 3, QTableWidgetItem(
                    workbook.last_measurement_at.strftime("%Y-%m-%d %H:%M") if workbook.last_measurement_at else "No measurements"
                ))
                
                # Actions button
                view_button = QPushButton("View")
                view_button.clicked.connect(lambda checked, wb_id=workbook.id: self.open_workbook_by_id(wb_id))
                self.workbooks_table.setCellWidget(row, 4, view_button)
            
            self.workbooks_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load workbooks: {str(e)}")
        finally:
            db.close()
    
    def create_workbook(self):
        """Create a new workbook"""
        # TODO: Implement workbook creation dialog
        QMessageBox.information(self, "Info", "Workbook creation dialog will be implemented")
    
    def open_workbook(self, index):
        """Open workbook for viewing/editing"""
        row = index.row()
        workbook_id = self.workbooks_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if workbook_id:
            self.open_workbook_by_id(workbook_id)
    
    def open_workbook_by_id(self, workbook_id):
        """Open workbook by ID"""
        # TODO: Implement workbook viewer/editor with 3 tabs (Seebeck, Resistivity, Thermal Conductivity)
        QMessageBox.information(self, "Info", f"Opening workbook {workbook_id} - Will show 3 measurement pages")

