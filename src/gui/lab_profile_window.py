from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from datetime import datetime

from src.database import get_db
from src.models import Lab, User, UserRole
from src.gui.dialogs.create_user_dialog import CreateUserDialog


class LabProfileWindow(QMainWindow):
    """Profile view for a lab: admins and researchers, read-only data."""

    def __init__(self, lab_id: int, parent=None):
        super().__init__(parent)
        self.lab_id = lab_id
        self.lab: Lab | None = None
        self.admins_table: QTableWidget | None = None
        self.researchers_table: QTableWidget | None = None

        self._init_ui()
        self._load_lab()
        self._load_admins()
        self._load_researchers()

    def _init_ui(self):
        self.setWindowTitle("Lab Profile - TE Measurements")
        self.resize(1000, 700)

        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        self.name_label = QLabel("Lab")
        name_font = self.name_label.font()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        header.addWidget(self.name_label)

        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #666; font-size: 11px;")
        header.addWidget(self.meta_label)

        header.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        root_layout.addLayout(header)

        # Tabs: Admins | Researchers
        tabs = QTabWidget()

        # Admins tab
        admins_tab = QWidget()
        admins_layout = QVBoxLayout(admins_tab)
        admins_layout.setContentsMargins(0, 0, 0, 0)
        admins_layout.setSpacing(8)

        admins_header = QHBoxLayout()
        admins_title = QLabel("Lab Admins")
        title_font = admins_title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        admins_title.setFont(title_font)
        admins_header.addWidget(admins_title)
        admins_header.addStretch()
        add_admin_btn = QPushButton("Add Lab Admin")
        add_admin_btn.setFixedHeight(28)
        add_admin_btn.clicked.connect(self._add_lab_admin)
        admins_header.addWidget(add_admin_btn)
        admins_layout.addLayout(admins_header)

        self.admins_table = QTableWidget()
        self.admins_table.setColumnCount(4)
        self.admins_table.setHorizontalHeaderLabels(
            ["Name", "Username", "Email", "Last Login"]
        )
        self.admins_table.horizontalHeader().setStretchLastSection(True)
        self.admins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        admins_layout.addWidget(self.admins_table)

        # Researchers tab
        researchers_tab = QWidget()
        researchers_layout = QVBoxLayout(researchers_tab)
        researchers_layout.setContentsMargins(0, 0, 0, 0)
        researchers_layout.setSpacing(8)

        researchers_header = QHBoxLayout()
        researchers_title = QLabel("Researchers")
        r_title_font = researchers_title.font()
        r_title_font.setPointSize(12)
        r_title_font.setBold(True)
        researchers_title.setFont(r_title_font)
        researchers_header.addWidget(researchers_title)
        researchers_header.addStretch()
        add_researcher_btn = QPushButton("Add Researcher")
        add_researcher_btn.setFixedHeight(28)
        add_researcher_btn.clicked.connect(self._add_researcher)
        researchers_header.addWidget(add_researcher_btn)
        researchers_layout.addLayout(researchers_header)

        self.researchers_table = QTableWidget()
        self.researchers_table.setColumnCount(4)
        self.researchers_table.setHorizontalHeaderLabels(
            ["Name", "Username", "Email", "Last Login"]
        )
        self.researchers_table.horizontalHeader().setStretchLastSection(True)
        self.researchers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        researchers_layout.addWidget(self.researchers_table)

        tabs.addTab(admins_tab, "Admins")
        tabs.addTab(researchers_tab, "Researchers")

        root_layout.addWidget(tabs)

        self.setCentralWidget(central)

    def _load_lab(self):
        db = next(get_db())
        try:
            self.lab = db.query(Lab).filter(Lab.id == self.lab_id).first()
            if not self.lab:
                QMessageBox.warning(self, "Not Found", "Lab not found.")
                self.close()
                return

            created_str = (
                self.lab.created_at.strftime("%Y-%m-%d")
                if self.lab.created_at
                else ""
            )
            self.name_label.setText(self.lab.name)
            meta_parts = []
            if self.lab.location:
                meta_parts.append(self.lab.location)
            if created_str:
                meta_parts.append(f"Created: {created_str}")
            meta_parts.append("Active" if self.lab.is_active else "Inactive")
            self.meta_label.setText(" | ".join(meta_parts))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load lab: {str(e)}")
        finally:
            db.close()

    def _load_admins(self):
        if self.admins_table is None:
            return

        db = next(get_db())
        try:
            admins = (
                db.query(User)
                .filter(
                    User.lab_id == self.lab_id,
                    User.role == UserRole.LAB_ADMIN,
                    User.is_active == True,  # noqa: E712
                )
                .order_by(User.full_name.asc())
                .all()
            )

            self.admins_table.setRowCount(len(admins))
            for row, admin in enumerate(admins):
                last_login = (
                    admin.last_login.strftime("%Y-%m-%d %H:%M")
                    if admin.last_login
                    else "Never"
                )
                self.admins_table.setItem(row, 0, QTableWidgetItem(admin.full_name))
                self.admins_table.setItem(row, 1, QTableWidgetItem(admin.username))
                self.admins_table.setItem(row, 2, QTableWidgetItem(admin.email))
                self.admins_table.setItem(row, 3, QTableWidgetItem(last_login))

            self.admins_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load admins: {str(e)}")
        finally:
            db.close()

    def _load_researchers(self):
        if self.researchers_table is None:
            return

        db = next(get_db())
        try:
            researchers = (
                db.query(User)
                .filter(
                    User.lab_id == self.lab_id,
                    User.role == UserRole.RESEARCHER,
                    User.is_active == True,  # noqa: E712
                )
                .order_by(User.full_name.asc())
                .all()
            )

            self.researchers_table.setRowCount(len(researchers))
            for row, r in enumerate(researchers):
                last_login = (
                    r.last_login.strftime("%Y-%m-%d %H:%M")
                    if r.last_login
                    else "Never"
                )
                self.researchers_table.setItem(row, 0, QTableWidgetItem(r.full_name))
                self.researchers_table.setItem(row, 1, QTableWidgetItem(r.username))
                self.researchers_table.setItem(row, 2, QTableWidgetItem(r.email))
                self.researchers_table.setItem(row, 3, QTableWidgetItem(last_login))

            self.researchers_table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load researchers: {str(e)}"
            )
        finally:
            db.close()

    def _add_lab_admin(self):
        """Open user creation dialog preconfigured as lab admin for this lab."""
        dialog = CreateUserDialog(self, preset_role=UserRole.LAB_ADMIN, preset_lab_id=self.lab_id)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._load_admins()

    def _add_researcher(self):
        """Open user creation dialog preconfigured as researcher for this lab."""
        dialog = CreateUserDialog(self, preset_role=UserRole.RESEARCHER, preset_lab_id=self.lab_id)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._load_researchers()


