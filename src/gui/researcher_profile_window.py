from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QGridLayout,
    QLineEdit,
    QSizePolicy,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QSize

from sqlalchemy import func

from src.database import get_db
from src.models import User, Workbook
from src.gui.workbook_window import WorkbookWindow


class ResearcherProfileWindow(QMainWindow):
    """Read-only view of a researcher's workbooks for lab admins."""

    def __init__(self, researcher_id: int, parent=None):
        super().__init__(parent)
        self.researcher_id = researcher_id
        self.researcher: User | None = None
        self.workbooks_all: list[Workbook] = []
        self.workbooks_filtered: list[Workbook] = []
        self.cards_layout: QGridLayout | None = None
        self.search_input: QLineEdit | None = None
        self.open_workbook_windows: list[WorkbookWindow] = []

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        self.setWindowTitle("Researcher Profile - TE Measurements")
        self.resize(1280, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        self.name_label = QLabel("Researcher")
        name_font = self.name_label.font()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        header.addWidget(self.name_label)

        header.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Search bar
        search_row = QHBoxLayout()
        search_label = QLabel("Search workbooks:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type workbook name...")
        self.search_input.textChanged.connect(self._apply_filter)
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        # Scrollable cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        cards_container = QWidget()
        cards_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(24)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        cards_container.setLayout(self.cards_layout)

        scroll_area.setWidget(cards_container)
        layout.addWidget(scroll_area)

        self.setCentralWidget(central)

    def _load_data(self):
        db = next(get_db())
        try:
            self.researcher = db.query(User).filter(User.id == self.researcher_id).first()
            if not self.researcher:
                QMessageBox.warning(self, "Not Found", "Researcher not found.")
                self.close()
                return

            self.name_label.setText(
                f"{self.researcher.full_name or self.researcher.username} - Workbooks"
            )

            self.workbooks_all = (
                db.query(Workbook)
                .filter(
                    Workbook.researcher_id == self.researcher_id,
                    Workbook.is_active == True,  # noqa: E712
                )
                .order_by(
                    func.coalesce(Workbook.updated_at, Workbook.created_at).desc()
                )
                .all()
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load researcher workbooks: {str(e)}")
            self.workbooks_all = []
        finally:
            db.close()

        self._apply_filter()

    def _apply_filter(self):
        text = ""
        if self.search_input is not None:
            text = self.search_input.text().strip().lower()

        if not text:
            self.workbooks_filtered = list(self.workbooks_all)
        else:
            filtered: list[Workbook] = []
            for wb in self.workbooks_all:
                title = (wb.title or "").lower()
                if text in title:
                    filtered.append(wb)
            self.workbooks_filtered = filtered

        self._build_cards()

    def _build_cards(self):
        if self.cards_layout is None:
            return

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        if not self.workbooks_filtered:
            placeholder = QLabel("No workbooks found for this researcher.")
            placeholder.setStyleSheet("color: #888; font-size: 11px;")
            self.cards_layout.addWidget(placeholder, 0, 0)
            return

        available_width = max(self.width() - 80, 320)
        card_width = 260
        spacing = self.cards_layout.horizontalSpacing() or 24
        cards_per_row = max(1, int(available_width / (card_width + spacing)))

        row = 0
        col = 0
        for wb in self.workbooks_filtered:
            card = self._create_workbook_card(wb)
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= cards_per_row:
                col = 0
                row += 1

    def _create_workbook_card(self, workbook: Workbook) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setObjectName("researcherWorkbookCard")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(
            """
            QFrame#researcherWorkbookCard {
                border: 1px solid #d0d7de;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QFrame#researcherWorkbookCard:hover {
                border: 1px solid #0078d4;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        title_label = QLabel(workbook.title or "Untitled Workbook")
        title_font = title_label.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        if workbook.sample_name:
            sample_label = QLabel(f"Sample: {workbook.sample_name}")
            sample_label.setStyleSheet("color: #555; font-size: 11px;")
            layout.addWidget(sample_label)

        dates = []
        if workbook.created_at:
            dates.append(f"Created: {workbook.created_at.strftime('%Y-%m-%d %H:%M')}")
        if workbook.last_measurement_at:
            dates.append(
                f"Last measurement: {workbook.last_measurement_at.strftime('%Y-%m-%d %H:%M')}"
            )
        if dates:
            date_label = QLabel(" | ".join(dates))
            date_label.setStyleSheet("color: #777; font-size: 10px;")
            date_label.setWordWrap(True)
            layout.addWidget(date_label)

        layout.addStretch()

        open_btn = QPushButton("Open Workbook")
        open_btn.setMinimumHeight(28)
        open_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
            }
            QPushButton:pressed {
                background-color: #cde4f7;
            }
            """
        )
        open_btn.clicked.connect(
            lambda _=False, wb_id=workbook.id: self._open_workbook(wb_id)
        )
        layout.addWidget(open_btn)

        card.setFixedWidth(260)
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)
        return card

    def _open_workbook(self, workbook_id: int):
        window = WorkbookWindow(workbook_id, None)
        window.showMaximized()
        self.open_workbook_windows.append(window)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._build_cards()


