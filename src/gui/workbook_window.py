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
)
from PyQt6.QtCore import Qt

from src.database import get_db
from src.models import Workbook, Measurement, MeasurementType
from src.instruments.keithley_connection import KeithleyConnection
from src.gui.seebeck_tab import SeebeckTab


class WorkbookWindow(QMainWindow):
    """Workbook window with bottom-positioned tabs for each measurement type."""

    def __init__(self, workbook_id: int, parent=None):
        super().__init__(parent)
        self.workbook_id = workbook_id
        self.workbook: Workbook | None = None
        self.keithley = KeithleyConnection()

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        # Configure main window
        self.setWindowTitle("Workbook - TE Measurements")
        self.resize(1280, 800)

        # Central widget and layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header with workbook title
        header = QHBoxLayout()
        self.title_label = QLabel("Workbook")
        title_font = self.title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        header.addWidget(self.title_label)

        header.addStretch()

        # Close button (just closes this window)
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Tab widget with tabs at the bottom (South), like Excel
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.South)

        # Seebeck tab (dedicated widget)
        self.seebeck_tab = SeebeckTab(self.keithley, self)
        self.tab_widget.addTab(self.seebeck_tab, "Seebeck")

        # Electrical resistivity tab
        self.resistivity_tab = self._create_measurement_tab(
            "Electrical Resistivity", MeasurementType.RESISTIVITY
        )
        self.tab_widget.addTab(self.resistivity_tab, "Resistivity")

        # Thermal conductivity tab
        self.thermal_tab = self._create_measurement_tab(
            "Thermal Conductivity", MeasurementType.THERMAL_CONDUCTIVITY
        )
        self.tab_widget.addTab(self.thermal_tab, "Thermal Conductivity")

        layout.addWidget(self.tab_widget)

        self.setCentralWidget(central)

    def _create_measurement_tab(
        self, title: str, measurement_type: MeasurementType
    ) -> QWidget:
        """Create a basic tab layout for a measurement type."""
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(8)

        # Title for generic tabs
        header = QLabel(title)
        header_font = header.font()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        vbox.addWidget(header)

        # Simple placeholder description and table (for resistivity / thermal, to be expanded later)
        desc = QLabel(
            "This page will display measurement data and controls for this "
            "measurement type.\nData is read-only once acquired from the instrument."
        )
        desc.setStyleSheet("color: #666; font-size: 11px;")
        desc.setWordWrap(True)
        vbox.addWidget(desc)

        table = QTableWidget()
        table.setObjectName(f"table_{measurement_type.value}")
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Index", "X", "Y", "Notes"])
        table.horizontalHeader().setStretchLastSection(True)
        vbox.addWidget(table)

        return tab

    def _load_data(self):
        """Load workbook metadata and measurement placeholders."""
        db = next(get_db())
        try:
            self.workbook = db.query(Workbook).filter(Workbook.id == self.workbook_id).first()
            if self.workbook:
                self.title_label.setText(self.workbook.title or "Untitled Workbook")

                # Load measurements per type (for now, just count rows)
                measurements = (
                    db.query(Measurement)
                    .filter(Measurement.workbook_id == self.workbook_id)
                    .all()
                )

                by_type: dict[MeasurementType, list[Measurement]] = {
                    MeasurementType.SEEBECK: [],
                    MeasurementType.RESISTIVITY: [],
                    MeasurementType.THERMAL_CONDUCTIVITY: [],
                }
                for m in measurements:
                    by_type[m.measurement_type].append(m)

                # Populate tables with simple index info for now
                self._populate_table(MeasurementType.SEEBECK, by_type[MeasurementType.SEEBECK])
                self._populate_table(
                    MeasurementType.RESISTIVITY, by_type[MeasurementType.RESISTIVITY]
                )
                self._populate_table(
                    MeasurementType.THERMAL_CONDUCTIVITY,
                    by_type[MeasurementType.THERMAL_CONDUCTIVITY],
                )
        finally:
            db.close()

    def _populate_table(self, mtype: MeasurementType, rows: list[Measurement]):
        table: QTableWidget = self.findChild(QTableWidget, f"table_{mtype.value}")
        if not table:
            return

        table.setRowCount(len(rows))
        for idx, m in enumerate(rows):
            table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            # The X/Y/Notes columns will be defined when we settle the data schema
            table.setItem(idx, 1, QTableWidgetItem(""))
            table.setItem(idx, 2, QTableWidgetItem(""))
            table.setItem(idx, 3, QTableWidgetItem(m.notes or "" if hasattr(m, "notes") else ""))

