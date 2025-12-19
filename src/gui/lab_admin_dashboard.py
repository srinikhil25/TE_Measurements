from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QGridLayout,
    QLineEdit,
    QGroupBox,
    QMessageBox,
    QSizePolicy,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta

from src.gui.base_dashboard import BaseDashboard
from src.database import get_db
from src.models import User, Workbook, UserRole
from src.services.statistics_service import StatisticsService
from src.gui.researcher_profile_window import ResearcherProfileWindow



























































class LabAdminDashboard(BaseDashboard):
    """Dashboard for lab administrators"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.statistics_service = StatisticsService()
        self.researchers_all: list[User] = []
        self.researchers_filtered: list[User] = []
        self.researcher_cards_layout: QGridLayout | None = None
        self.search_input: QLineEdit | None = None
        self.profile_windows: list[ResearcherProfileWindow] = []
        self.activity_table: QTableWidget | None = None
        self.activity_range: QComboBox | None = None
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

        # Top-level tab widget: Researchers | Statistics
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        #
        # Statistics tab
        #
        stats_tab = QWidget()
        stats_tab_layout = QVBoxLayout(stats_tab)
        stats_tab_layout.setContentsMargins(0, 0, 0, 0)
        stats_tab_layout.setSpacing(8)

        # Statistics section
        stats_group = QGroupBox("Lab Statistics")
        stats_layout = QVBoxLayout()

        # Summary statistics label (filled in load_statistics)
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        stats_layout.addWidget(self.stats_label)

        # Recent activity controls
        range_row = QHBoxLayout()
        range_label = QLabel("Recent activity:")
        self.activity_range = QComboBox()
        self.activity_range.addItems(["Last 7 days", "Last 30 days", "All time"])
        self.activity_range.currentIndexChanged.connect(self.load_activity_feed)
        range_row.addWidget(range_label)
        range_row.addWidget(self.activity_range)
        range_row.addStretch()
        stats_layout.addLayout(range_row)

        # Recent activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(
            ["Time", "Researcher", "Action", "Details"]
        )
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.activity_table.setMaximumHeight(180)
        stats_layout.addWidget(self.activity_table)

        stats_group.setLayout(stats_layout)
        stats_tab_layout.addWidget(stats_group)

        #
        # Researchers tab
        #
        researchers_tab = QWidget()
        researchers_layout = QVBoxLayout(researchers_tab)
        researchers_layout.setContentsMargins(0, 8, 0, 0)
        researchers_layout.setSpacing(8)

        header_row = QHBoxLayout()
        title = QLabel("Researchers in Lab")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_row.addWidget(title)
        header_row.addStretch()
        researchers_layout.addLayout(header_row)

        # Search bar
        search_row = QHBoxLayout()
        search_label = QLabel("Search researchers:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type name or username...")
        self.search_input.textChanged.connect(self._apply_filter)
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_input)
        researchers_layout.addLayout(search_row)

        # Scrollable card grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        cards_container = QWidget()
        cards_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.researcher_cards_layout = QGridLayout()
        self.researcher_cards_layout.setSpacing(24)
        self.researcher_cards_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        cards_container.setLayout(self.researcher_cards_layout)

        scroll_area.setWidget(cards_container)
        researchers_layout.addWidget(scroll_area)

        # Add tabs to main content
        tabs.addTab(researchers_tab, "Researchers")
        tabs.addTab(stats_tab, "Statistics")
        tabs.setCurrentIndex(0)

        self.content_layout.addWidget(tabs)
    
    def load_data(self):
        """Load lab admin dashboard data"""
        super().load_data()  # Update header
        self.load_researchers()
        self.load_statistics()
        self.load_activity_feed()
    
    def load_researchers(self):
        """Load researchers in the lab"""
        user = self.get_current_user()
        if not user or not user.lab_id:
            return
        
        db = next(get_db())
        try:
            self.researchers_all = (
                db.query(User)
                .filter(
                    User.lab_id == user.lab_id,
                    User.role == UserRole.RESEARCHER,
                    User.is_active == True,  # noqa: E712
                )
                .order_by(User.full_name.asc())
                .all()
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load researchers: {str(e)}")
            self.researchers_all = []
        finally:
            db.close()

        self._apply_filter()

    def _apply_filter(self):
        """Filter researchers based on search text and rebuild cards."""
        text = ""
        if self.search_input is not None:
            text = self.search_input.text().strip().lower()

        if not text:
            self.researchers_filtered = list(self.researchers_all)
        else:
            filtered: list[User] = []
            for r in self.researchers_all:
                name = (r.full_name or "").lower()
                username = (r.username or "").lower()
                if text in name or text in username:
                    filtered.append(r)
            self.researchers_filtered = filtered

        self._build_researcher_cards()

    def _build_researcher_cards(self):
        """Create cards for each researcher in the lab."""
        if self.researcher_cards_layout is None:
            return

        # Clear existing items
        while self.researcher_cards_layout.count():
            item = self.researcher_cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        if not self.researchers_filtered:
            placeholder = QLabel("No researchers found in this lab.")
            placeholder.setStyleSheet("color: #888; font-size: 11px;")
            self.researcher_cards_layout.addWidget(placeholder, 0, 0)
            return

        # Fetch per-researcher statistics
        db = next(get_db())
        stats_by_researcher: dict[int, dict] = {}
        try:
            for r in self.researchers_filtered:
                stats_by_researcher[r.id] = self.statistics_service.get_researcher_statistics(
                    db, r.id
                )
        finally:
            db.close()

        # Layout cards
        available_width = max(self.width() - 80, 320)
        card_width = 260
        spacing = self.researcher_cards_layout.horizontalSpacing() or 24
        cards_per_row = max(1, int(available_width / (card_width + spacing)))

        row = 0
        col = 0
        for researcher in self.researchers_filtered:
            card = self._create_researcher_card(
                researcher, stats_by_researcher.get(researcher.id)
            )
            self.researcher_cards_layout.addWidget(card, row, col)
            col += 1
            if col >= cards_per_row:
                col = 0
                row += 1

    def _create_researcher_card(self, researcher: User, stats: dict | None) -> QFrame:
        """Create a card widget for a single researcher."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setObjectName("researcherCard")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(
            """
            QFrame#researcherCard {
                border: 1px solid #d0d7de;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QFrame#researcherCard:hover {
                border: 1px solid #28a745;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        name_label = QLabel(researcher.full_name or researcher.username)
        name_font = name_label.font()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        username_label = QLabel(f"Username: {researcher.username}")
        username_label.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(username_label)

        total_workbooks = stats.get("total_workbooks", 0) if stats else 0
        total_measurements = stats.get("total_measurements", 0) if stats else 0
        instrument_uses = stats.get("instrument_usage_count", 0) if stats else 0

        info_parts = [
            f"Workbooks: {total_workbooks}",
            f"Measurements: {total_measurements}",
            f"Instrument uses: {instrument_uses}",
        ]
        if researcher.last_login:
            info_parts.append(
                f"Last active: {researcher.last_login.strftime('%Y-%m-%d %H:%M')}"
            )
        info_label = QLabel(" | ".join(info_parts))
        info_label.setStyleSheet("color: #777; font-size: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Activity "health" badge
        status_label = QLabel()
        if researcher.last_login:
            last_login = researcher.last_login
            # Normalise to naive UTC before computing delta to avoid
            # mixing offset-aware and offset-naive datetimes.
            if last_login.tzinfo is not None:
                last_login = last_login.astimezone(tz=None).replace(tzinfo=None)
            delta = datetime.utcnow() - last_login
            if delta.days <= 30:
                status_label.setText("Active recently")
                status_label.setStyleSheet(
                    "color: #2e7d32; font-size: 10px; font-weight: 600;"
                )
            else:
                status_label.setText("Inactive (>30 days)")
                status_label.setStyleSheet(
                    "color: #b71c1c; font-size: 10px; font-weight: 600;"
                )
        else:
            status_label.setText("No login yet")
            status_label.setStyleSheet(
                "color: #757575; font-size: 10px; font-weight: 600;"
            )
        layout.addWidget(status_label)

        layout.addStretch()

        view_button = QPushButton("View Workbooks")
        view_button.setMinimumHeight(28)
        view_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #28a745;
                border: 1px solid #28a745;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e6f4ea;
            }
            QPushButton:pressed {
                background-color: #c8e6c9;
            }
            """
        )
        view_button.clicked.connect(
            lambda _=False, r_id=researcher.id: self.view_researcher_work(r_id)
        )
        layout.addWidget(view_button)

        card.setFixedWidth(260)
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)

        return card

    def load_statistics(self):
        """Load and display aggregate lab statistics in the header section."""
        user = self.get_current_user()
        if not user or not user.lab_id:
            return

        db = next(get_db())
        try:
            lab_stats = self.statistics_service.get_lab_statistics(db, user.lab_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load statistics: {str(e)}")
            return
        finally:
            db.close()

        researcher_stats = lab_stats.get("researcher_stats", {})
        total_workbooks = sum(
            rs.get("total_workbooks", 0) for rs in researcher_stats.values()
        )
        total_measurements = sum(
            rs.get("total_measurements", 0) for rs in researcher_stats.values()
        )
        instrument_uses = sum(
            rs.get("instrument_usage_count", 0) for rs in researcher_stats.values()
        )

        total_researchers = lab_stats.get("total_researchers", 0)

        self.stats_label.setText(
            f"Researchers: {total_researchers} | "
            f"Workbooks: {total_workbooks} | "
            f"Measurements: {total_measurements} | "
            f"Instrument uses: {instrument_uses}"
        )

    def load_activity_feed(self):
        """Load recent activity logs into the activity table."""
        if self.activity_table is None or self.activity_range is None:
            return

        user = self.get_current_user()
        if not user or not user.lab_id:
            return

        # Determine date range
        selection = self.activity_range.currentText()
        since: datetime | None = None
        now = datetime.utcnow()
        if "7 days" in selection:
            since = now - timedelta(days=7)
        elif "30 days" in selection:
            since = now - timedelta(days=30)
        else:
            since = None  # All time

        db = next(get_db())
        try:
            logs = self.statistics_service.get_lab_activity_logs(
                db, user.lab_id, since=since, limit=50
            )

            self.activity_table.setRowCount(len(logs))
            for row, log in enumerate(logs):
                time_str = (
                    log.created_at.strftime("%Y-%m-%d %H:%M")
                    if log.created_at
                    else ""
                )
                researcher_name = (
                    (log.user.full_name or log.user.username)
                    if getattr(log, "user", None)
                    else "System"
                )
                action_text = log.action_type.value.replace("_", " ").title()
                details = log.description or ""

                self.activity_table.setItem(row, 0, QTableWidgetItem(time_str))
                self.activity_table.setItem(row, 1, QTableWidgetItem(researcher_name))
                self.activity_table.setItem(row, 2, QTableWidgetItem(action_text))
                self.activity_table.setItem(row, 3, QTableWidgetItem(details))
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load recent activity: {str(e)}"
            )
        finally:
            db.close()

    def view_researcher_work(self, researcher_id: int):
        """Open a read-only researcher profile with their workbooks."""
        window = ResearcherProfileWindow(researcher_id, None)
        window.showMaximized()
        self.profile_windows.append(window)

    def resizeEvent(self, event):
        """Rebuild card layout on resize to keep grid responsive."""
        super().resizeEvent(event)
        self._build_researcher_cards()

