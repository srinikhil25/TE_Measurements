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
    QMessageBox,
    QSizePolicy,
    QToolButton,
    QMenu,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction

from sqlalchemy import func
from datetime import datetime

from src.gui.base_dashboard import BaseDashboard
from src.database import get_db
from src.models import Workbook
from src.services.workbook_service import WorkbookService
from src.gui.workbook_window import WorkbookWindow
from src.i18n import tr

class ResearcherDashboard(BaseDashboard):
    """Dashboard for researchers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workbook_service = WorkbookService()
        self.workbooks_all: list[Workbook] = []
        self.workbooks_filtered: list[Workbook] = []
        self.card_widgets: list[QFrame] = []
        self.cards_layout: QGridLayout | None = None
        self.search_input: QLineEdit | None = None
        self.open_workbook_windows: list[WorkbookWindow] = []
        self.init_ui()
    
    def _create_role_badge(self):
        """Create role badge for researcher"""
        badge = QLabel(tr("dashboard.researcher"))
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
        """Initialize UI components specific to researcher (card grid of workbooks)"""
        print("[ResearcherDashboard] init_ui starting")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Toolbar: search + refresh
        toolbar = QHBoxLayout()

        self.search_label_ref = QLabel(tr("researcher.search_workbooks"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("researcher.search_placeholder"))
        self.search_input.textChanged.connect(self._apply_filter)

        toolbar.addWidget(self.search_label_ref)
        toolbar.addWidget(self.search_input)

        self.refresh_button_ref = QPushButton(tr("researcher.refresh"))
        self.refresh_button_ref.clicked.connect(self.load_data)
        toolbar.addWidget(self.refresh_button_ref)

        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Scroll area with card grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Ensure contents are anchored at the top-left, not centered
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        cards_container = QWidget()
        cards_container.setStyleSheet("background-color: #f4f5fb;")
        # Let the cards area expand with the viewport so cards stay anchored
        cards_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(24)
        # Ensure cards are placed from top-left, not centered
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        cards_container.setLayout(self.cards_layout)

        scroll_area.setWidget(cards_container)
        layout.addWidget(scroll_area)

        self.content_layout.addWidget(container)

        # Initial build (shows New Workbook card even before any data)
        print(
            f"[ResearcherDashboard] init_ui completed. cards_layout is "
            f"{'set' if self.cards_layout is not None else 'None'}"
        )
        self._build_cards()
    
    def _refresh_translated_ui(self):
        """Refresh all translated UI elements with current language"""
        if hasattr(self, 'search_label_ref') and self.search_label_ref:
            self.search_label_ref.setText(tr("researcher.search_workbooks"))
        if hasattr(self, 'refresh_button_ref') and self.refresh_button_ref:
            self.refresh_button_ref.setText(tr("researcher.refresh"))
        if hasattr(self, 'search_input') and self.search_input:
            self.search_input.setPlaceholderText(tr("researcher.search_placeholder"))
        
        # Rebuild cards to refresh translated text in cards
        self._build_cards()
    
    def load_data(self):
        """Load researcher's workbooks and rebuild card grid"""
        super().load_data()  # Update header
        
        # Refresh translated UI elements after login (language may have changed)
        self._refresh_translated_ui()

        user = self.get_current_user()
        if not user:
            return

        db = next(get_db())
        try:
            # Order by most recently accessed: updated_at (if set) or created_at,
            # newest first.
            self.workbooks_all = (
                db.query(Workbook)
                .filter(
                    Workbook.researcher_id == user.id,
                    Workbook.is_active == True,  # noqa: E712
                )
                .order_by(
                    func.coalesce(Workbook.updated_at, Workbook.created_at).desc()
                )
                .all()
            )
        except Exception as e:
            QMessageBox.critical(self, tr("common.error"), f"Failed to load workbooks: {str(e)}")
            self.workbooks_all = []
        finally:
            db.close()

        print(f"[ResearcherDashboard] Loaded {len(self.workbooks_all)} workbook(s)")
        self._apply_filter()  # will rebuild cards

    def _apply_filter(self):
        """Filter workbooks based on search text and rebuild cards."""
        text = ""
        if self.search_input is not None:
            text = self.search_input.text().strip().lower()

        if not text:
            self.workbooks_filtered = list(self.workbooks_all)
        else:
            filtered: list[Workbook] = []
            for wb in self.workbooks_all:
                name_match = text in (wb.title or "").lower()
                if name_match:
                    filtered.append(wb)
            self.workbooks_filtered = filtered

        self._build_cards()

    def _build_cards(self):
        """Create card widgets for each workbook, plus a New Workbook card."""
        print(
            f"[ResearcherDashboard] _build_cards called. "
            f"cards_layout is {'set' if self.cards_layout is not None else 'None'}"
        )
        # QGridLayout implements __len__, so `if not self.cards_layout` is False
        # when it has no children. We only want to exit if it is actually None.
        if self.cards_layout is None:
            print("[ResearcherDashboard] _build_cards exiting because cards_layout is None")
            return

        # Clear existing items
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.card_widgets = []

        print(
            f"[ResearcherDashboard] Building cards for "
            f"{len(self.workbooks_filtered)} filtered workbook(s)"
        )

        # First card: New Workbook
        new_card = self._create_new_workbook_card()
        self.card_widgets.append(new_card)

        # Workbook cards
        for wb in self.workbooks_filtered:
            card = self._create_workbook_card(wb)
            self.card_widgets.append(card)

        # Layout cards in grid; number per row depends on available width
        # Layout cards in grid; number per row depends on available width
        # Use the dashboard width as an approximation of available space.
        available_width = max(self.width() - 80, 320)
        card_width = 260  # fixed card width
        spacing = self.cards_layout.horizontalSpacing() or 24
        cards_per_row = max(1, int(available_width / (card_width + spacing)))
        row = 0
        col = 0
        for card in self.card_widgets:
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= cards_per_row:
                col = 0
                row += 1

    def _create_new_workbook_card(self) -> QFrame:
        """Create the fixed 'New Workbook' card."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setObjectName("newWorkbookCard")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(
            """
            QFrame#newWorkbookCard {
                border: 1px dashed #9fc5e8;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QFrame#newWorkbookCard:hover {
                border: 1px solid #0078d4;
                background-color: #f0f6ff;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel(tr("researcher.new_workbook"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        subtitle = QLabel(tr("researcher.new_workbook_subtitle"))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(subtitle)

        layout.addStretch()

        button = QPushButton(tr("researcher.create_workbook"))
        button.setMinimumHeight(32)
        button.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            """
        )
        button.clicked.connect(self.create_workbook)
        layout.addWidget(button)

        # Consistent card size
        card.setFixedWidth(260)
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)
        return card

    def _create_workbook_card(self, workbook: Workbook) -> QFrame:
        """Create a card widget for a single workbook."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setObjectName("workbookCard")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(
            """
            QFrame#workbookCard {
                border: 1px solid #d0d7de;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QFrame#workbookCard:hover {
                border: 1px solid #0078d4;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        # Header row: editable title + overflow menu (three vertical dots)
        title_edit = QLineEdit(workbook.title or "Untitled Workbook")
        title_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_edit.setFrame(False)
        title_edit.setStyleSheet(
            """
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-bottom: 1px solid #0078d4;
                background: #f0f6ff;
            }
            """
        )
        title_edit.setToolTip("Click to rename this workbook; press Enter to save")
        title_edit.editingFinished.connect(
            lambda wb_id=workbook.id, editor=title_edit: self.inline_rename_workbook(
                wb_id, editor
            )
        )

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(4)
        header_row.addWidget(title_edit, 1)

        # Three-dot overflow button for workbook actions (e.g., delete)
        options_button = QToolButton(card)
        options_button.setText("⋮")
        options_button.setToolTip("More options")
        options_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        options_button.setStyleSheet(
            """
            QToolButton {
                border: none;
                font-weight: bold;
                color: #888;
                padding: 0 2px;
            }
            QToolButton::menu-indicator {
                image: none;
            }
            QToolButton:hover {
                color: #000;
            }
            """
        )

        menu = QMenu(options_button)
        delete_action = QAction(tr("researcher.delete_workbook"), options_button)
        delete_action.triggered.connect(
            lambda _=False, wb_id=workbook.id, wb_title=workbook.title: self.confirm_delete_workbook(
                wb_id, wb_title or "Untitled Workbook"
            )
        )
        menu.addAction(delete_action)
        options_button.setMenu(menu)

        header_row.addWidget(
            options_button, 0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        layout.addLayout(header_row)

        if workbook.sample_name:
            sample_label = QLabel(f"{tr('researcher.sample')} {workbook.sample_name}")
            sample_label.setStyleSheet("color: #555; font-size: 11px;")
            layout.addWidget(sample_label)

        dates = []
        if workbook.created_at:
            dates.append(f"{tr('researcher.created')} {workbook.created_at.strftime('%Y-%m-%d %H:%M')}")
        if workbook.last_measurement_at:
            dates.append(
                f"{tr('researcher.last_measurement')} {workbook.last_measurement_at.strftime('%Y-%m-%d %H:%M')}"
            )

        if dates:
            date_label = QLabel(" | ".join(dates))
            date_label.setStyleSheet("color: #777; font-size: 10px;")
            date_label.setWordWrap(True)
            layout.addWidget(date_label)

        layout.addStretch()

        open_button = QPushButton(tr("researcher.open_workbook"))
        open_button.setMinimumHeight(28)
        open_button.setStyleSheet(
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
        open_button.clicked.connect(lambda _=False, wb_id=workbook.id: self.open_workbook_by_id(wb_id))
        layout.addWidget(open_button)

        card.setFixedWidth(260)
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)
        return card

    def create_workbook(self):
        """Create a new workbook with a default untitled name and refresh."""
        user = self.get_current_user()
        if not user:
            return

        db = next(get_db())
        try:
            wb = self.workbook_service.create_workbook(
                db, user, title="Untitled Workbook", sample_name=None, sample_id=None
            )
            QMessageBox.information(
                self, tr("researcher.workbook_created"), tr("researcher.created_message", "Created workbook '{title}'.").format(title=wb.title)
            )
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, tr("common.error"), f"Failed to create workbook: {str(e)}")
        finally:
            db.close()

        self.load_data()
    
    def open_workbook_by_id(self, workbook_id):
        """Open workbook by ID"""
        # Open workbook as a separate, maximized window
        window = WorkbookWindow(workbook_id, None)
        window.showMaximized()
        # Keep reference so it's not garbage-collected
        self.open_workbook_windows.append(window)

    def inline_rename_workbook(self, workbook_id: int, editor: QLineEdit):
        """Inline rename handler for title edit field."""
        new_title = editor.text().strip()
        if not new_title:
            # Revert on empty; reload titles from DB
            self.load_data()
            return

        db = next(get_db())
        try:
            wb = db.query(Workbook).filter(Workbook.id == workbook_id).first()
            if not wb:
                return
            if wb.title == new_title:
                return
            wb.title = new_title
            wb.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, tr("common.error"), f"Failed to rename workbook: {str(e)}")
        finally:
            db.close()

        self.load_data()

    def confirm_delete_workbook(self, workbook_id: int, title: str):
        """Ask for confirmation and soft-delete the workbook via service."""
        user = self.get_current_user()
        if not user:
            return

        reply = QMessageBox.question(
            self,
            tr("researcher.delete_workbook"),
            (
                f"{tr('researcher.delete_confirm')} '{title}'?\n\n"
                f"{tr('researcher.delete_confirm_detail')}"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        db = next(get_db())
        try:
            self.workbook_service.delete_workbook(db, workbook_id, user)
        except PermissionError as e:
            QMessageBox.warning(self, tr("common.warning"), str(e))
        except Exception as e:
            db.rollback()
            QMessageBox.critical(
                self, tr("common.error"), f"Failed to delete workbook: {str(e)}"
            )
        finally:
            db.close()

        self.load_data()

    def resizeEvent(self, event):
        """Rebuild card layout on resize to keep grid responsive."""
        super().resizeEvent(event)
        self._build_cards()

