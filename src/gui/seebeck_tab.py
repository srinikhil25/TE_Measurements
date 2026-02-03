from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QSplitter,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer

# Configure matplotlib for CJK font support before importing
from src.utils import configure_cjk_fonts
configure_cjk_fonts()

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import csv
import json
import os
from datetime import datetime

from src.instruments.keithley_connection import KeithleyConnection
from src.gui.seebeck_diagram_widget import SeebeckDiagramWidget
from src.gui.ir_camera_widget import IRCameraWidget
from src.database import get_db
from src.models import MeasurementType
from src.services.measurement_service import MeasurementService
from src.auth import SessionManager
from src.utils import Config


class LiveGraphWidget(QWidget):
    """Live graph showing TEMF, Temp1, Temp2 over time"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx()  # Second y-axis for temperatures
        
        self.ax.set_xlabel('Time [s]', fontsize=10)
        self.ax.set_ylabel('TEMF [mV]', fontsize=10, color='#1976d2')
        self.ax2.set_ylabel('Temp [°C]', fontsize=10, color='#d32f2f')
        self.ax.tick_params(axis='y', labelcolor='#1976d2')
        self.ax2.tick_params(axis='y', labelcolor='#d32f2f')
        
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
    
    def update_data(self, data: list):
        """Update graph with new data"""
        if not data:
            return
        
        times = [row.get("Time [s]", 0) for row in data]
        temf = [row.get("TEMF [mV]") for row in data if row.get("TEMF [mV]") is not None]
        temp1 = [row.get("Temp1 [oC]") for row in data if row.get("Temp1 [oC]") is not None]
        temp2 = [row.get("Temp2 [oC]") for row in data if row.get("Temp2 [oC]") is not None]
        
        self.ax.clear()
        self.ax2.clear()
        
        self.ax.set_xlabel('Time [s]', fontsize=10)
        self.ax.set_ylabel('TEMF [mV]', fontsize=10, color='#1976d2')
        self.ax2.set_ylabel('Temp [°C]', fontsize=10, color='#d32f2f')
        self.ax.tick_params(axis='y', labelcolor='#1976d2')
        self.ax2.tick_params(axis='y', labelcolor='#d32f2f')
        
        if times and temf:
            valid_indices = [i for i, v in enumerate(temf) if v is not None]
            if valid_indices:
                valid_times = [times[i] for i in valid_indices]
                valid_temf = [temf[i] for i in valid_indices]
                self.ax.plot(valid_times, valid_temf, 'b-', linewidth=1.5, label='TEMF [mV]', alpha=0.8)
        
        if times and temp1:
            valid_indices = [i for i, v in enumerate(temp1) if v is not None]
            if valid_indices:
                valid_times = [times[i] for i in valid_indices]
                valid_temp1 = [temp1[i] for i in valid_indices]
                self.ax2.plot(valid_times, valid_temp1, 'r-', linewidth=1.5, label='Temp1 [°C]', alpha=0.8)
        
        if times and temp2:
            valid_indices = [i for i, v in enumerate(temp2) if v is not None]
            if valid_indices:
                valid_times = [times[i] for i in valid_indices]
                valid_temp2 = [temp2[i] for i in valid_indices]
                self.ax2.plot(valid_times, valid_temp2, 'g-', linewidth=1.5, label='Temp2 [°C]', alpha=0.8)
        
        self.ax.legend(loc='upper left', fontsize=9)
        self.ax2.legend(loc='upper right', fontsize=9)
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()


class DeltaTempGraphWidget(QWidget):
    """Graph showing TEMF vs Delta Temp"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.set_xlabel('Delta Temp (Δt) / 差温度 [°C]', fontsize=10)
        self.ax.set_ylabel('TEMF [mV]', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
    
    def update_data(self, data: list):
        """Update graph with new data"""
        if not data:
            return
        
        delta_temps = []
        temf_values = []
        
        for row in data:
            delta = row.get("Delta Temp [oC]")
            temf = row.get("TEMF [mV]")
            if delta is not None and temf is not None:
                delta_temps.append(delta)
                temf_values.append(temf)
        
        self.ax.clear()
        self.ax.set_xlabel('Delta Temp (Δt) / 差温度 [°C]', fontsize=10)
        self.ax.set_ylabel('TEMF [mV]', fontsize=10)
        
        if delta_temps and temf_values:
            self.ax.plot(delta_temps, temf_values, 'bo-', markersize=4, linewidth=1.5, alpha=0.7)
        
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()


class SeebeckTab(QWidget):
    """
    Seebeck measurement tab UI with simple 4-quadrant layout (Q1, Q2, Q3, Q4).
    
    Layout:
    - Q1 (Top-Left): Measurement Parameters
    - Q2 (Top-Right): IR Camera Live Stream
    - Q3 (Bottom-Left): Measurement Data Table
    - Q4 (Bottom-Right): Live Data Visualization (Graphs)
    
    Features:
    - Scrollable content area
    - Instrument status indicators
    - Start/Stop controls
    - Save and export functionality
    """

    def __init__(self, keithley: KeithleyConnection, workbook_id: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.keithley = keithley
        self.workbook_id = workbook_id
        self.measurement_service = MeasurementService()
        self.config = Config()
        self.session_manager = SessionManager()

        # Live data polling timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh_live_data)
        self._last_count: int = 0

        # UI references
        self._diagram: SeebeckDiagramWidget | None = None
        self._table: QTableWidget | None = None
        self._start_btn: QPushButton | None = None
        self._stop_btn: QPushButton | None = None
        self._save_btn: QPushButton | None = None
        self._export_csv_btn: QPushButton | None = None
        self._export_excel_btn: QPushButton | None = None
        self._live_graph: LiveGraphWidget | None = None
        self._delta_graph: DeltaTempGraphWidget | None = None
        
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI with simple 4-quadrant layout"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === TOP STATUS BAR ===
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

        # === SCROLLABLE 4-QUADRANT LAYOUT ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create 4-quadrant container
        quadrant_container = QWidget()
        quadrant_layout = QVBoxLayout(quadrant_container)
        quadrant_layout.setContentsMargins(8, 8, 8, 8)
        quadrant_layout.setSpacing(8)
        
        # Create 2x2 grid using nested splitters
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top row: Q1 (Parameters) and Q2 (IR Camera)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Q1: Parameters
        q1_widget = self._create_q1_parameters()
        top_splitter.addWidget(q1_widget)
        
        # Q2: IR Camera
        q2_widget = self._create_q2_ir_camera()
        top_splitter.addWidget(q2_widget)
        
        # Set sizes for top row - Q1 much smaller, Q2 much larger
        # Ratio: Q1 gets 20%, Q2 gets 80% of the width
        top_splitter.setSizes([2, 8])
        # Set maximum heights for top row widgets to limit their size
        q1_widget.setMaximumHeight(250)
        q2_widget.setMaximumHeight(250)
        main_splitter.addWidget(top_splitter)
        
        # Bottom row: Q3 (Data Table) and Q4 (Graphs) - MAIN CONTENT
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Q3: Data Table
        q3_widget = self._create_q3_data_table()
        bottom_splitter.addWidget(q3_widget)
        
        # Q4: Graphs
        q4_widget = self._create_q4_graphs()
        bottom_splitter.addWidget(q4_widget)
        
        # Set equal sizes for bottom row
        bottom_splitter.setSizes([1, 1])
        main_splitter.addWidget(bottom_splitter)
        
        # Give bottom row MUCH more space (Q3 and Q4 are the main content)
        # Ratio: 1 (top) : 4 (bottom) - bottom gets 4x more space
        main_splitter.setSizes([1, 4])
        
        quadrant_layout.addWidget(main_splitter)
        scroll_area.setWidget(quadrant_container)
        
        layout.addWidget(scroll_area)

        # === BOTTOM ACTION BAR ===
        action_bar = self._create_action_bar()
        layout.addWidget(action_bar)

    def _create_status_bar(self) -> QFrame:
        """Create compact status bar with instrument indicators"""
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.Box)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 4, 8, 4)
        status_layout.setSpacing(12)

        # Title - smaller and more compact
        title = QLabel("Seebeck Coefficient Measurement")
        title_font = title.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #212529;")
        status_layout.addWidget(title)

        status_layout.addStretch()

        # Status indicator - smaller
        self._status_indicator = QLabel("● Ready")
        self._status_indicator.setStyleSheet("color: #6c757d; font-weight: bold; font-size: 10px;")
        status_layout.addWidget(self._status_indicator)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #dee2e6;")
        status_layout.addWidget(separator)

        # Instrument status indicators
        self._add_instrument_status_row(status_layout, instruments=["2182A", "2700", "PK160"])

        return status_frame

    def _create_q1_parameters(self) -> QWidget:
        """Create Q1: Measurement Parameters panel - compact version"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        
        
        # Parameters diagram - responsive sizing
        self._diagram = SeebeckDiagramWidget(self)
        # Allow it to use available space but keep reasonable constraints
        self._diagram.setMinimumHeight(150)
        self._diagram.setMaximumHeight(200)
        # Let it expand horizontally to use Q1 width
        layout.addWidget(self._diagram)
        
        return widget

    def _create_q2_ir_camera(self) -> QWidget:
        """Create Q2: IR Camera panel - compact version"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # # Title - smaller
        # title = QLabel("Q2: IR Camera Live Stream")
        # title_font = title.font()
        # title_font.setPointSize(9)
        # title_font.setBold(True)
        # title.setFont(title_font)
        # title.setStyleSheet("color: #495057; margin-bottom: 2px;")
        # layout.addWidget(title)
        
        # IR Camera widget - compact size
        self._ir_camera = IRCameraWidget(self)
        # Allow it to use available space but keep compact
        self._ir_camera.setMaximumHeight(160)
        layout.addWidget(self._ir_camera)
        
        return widget

    def _create_q3_data_table(self) -> QWidget:
        """Create Q3: Data Table panel"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Measurement Data Table")
        title_font = title.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #495057; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Time [s]", "TEMF [mV]", "Temp1 [°C]", "Temp2 [°C]", "Delta Temp [°C]"]
        )
        
        # Professional table styling
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #e0e0e0;
                border: none;
                selection-background-color: #0078d4;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e8f4f8;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 10px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                font-size: 10pt;
                color: #212529;
            }
        """)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setColumnWidth(0, 100)
        self._table.setColumnWidth(1, 120)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(4, 140)
        self._table.horizontalHeader().setStretchLastSection(False)

        layout.addWidget(self._table)
        return widget

    def _create_q4_graphs(self) -> QWidget:
        """Create Q4: Graphs panel"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Live Data Visualization")
        title_font = title.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #495057; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # Create scrollable area for graphs
        graphs_scroll = QScrollArea()
        graphs_scroll.setWidgetResizable(True)
        graphs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        graphs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        graphs_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        graphs_container = QWidget()
        graphs_layout = QHBoxLayout(graphs_container)  # Changed to horizontal layout
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        graphs_layout.setSpacing(12)
        
        # Graph 1: TEMF & Temp vs Time (wrapped in container)
        graph1_container = QWidget()
        graph1_container_layout = QVBoxLayout(graph1_container)
        graph1_container_layout.setContentsMargins(0, 0, 0, 0)
        graph1_container_layout.setSpacing(4)
        
        graph1_label = QLabel("TEMF & Temperature vs Time")
        graph1_label_font = graph1_label.font()
        graph1_label_font.setPointSize(10)
        graph1_label_font.setBold(True)
        graph1_label.setFont(graph1_label_font)
        graph1_label.setStyleSheet("color: #495057;")
        graph1_container_layout.addWidget(graph1_label)
        
        self._live_graph = LiveGraphWidget(self)
        self._live_graph.setMinimumHeight(300)
        graph1_container_layout.addWidget(self._live_graph)
        graphs_layout.addWidget(graph1_container)
        
        # Graph 2: TEMF vs Delta Temp (wrapped in container)
        graph2_container = QWidget()
        graph2_container_layout = QVBoxLayout(graph2_container)
        graph2_container_layout.setContentsMargins(0, 0, 0, 0)
        graph2_container_layout.setSpacing(4)
        
        graph2_label = QLabel("TEMF vs Delta Temperature")
        graph2_label_font = graph2_label.font()
        graph2_label_font.setPointSize(10)
        graph2_label_font.setBold(True)
        graph2_label.setFont(graph2_label_font)
        graph2_label.setStyleSheet("color: #495057;")
        graph2_container_layout.addWidget(graph2_label)
        
        self._delta_graph = DeltaTempGraphWidget(self)
        self._delta_graph.setMinimumHeight(300)
        graph2_container_layout.addWidget(self._delta_graph)
        graphs_layout.addWidget(graph2_container)
        
        graphs_scroll.setWidget(graphs_container)
        layout.addWidget(graphs_scroll)
        
        return widget

    def _create_action_bar(self) -> QFrame:
        """Create bottom action bar with control and data buttons"""
        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.Shape.Box)
        action_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Control buttons group
        control_label = QLabel("Control:")
        control_label.setStyleSheet("font-weight: bold; color: #495057;")
        layout.addWidget(control_label)

        self._start_btn = QPushButton("▶ Start Measurement")
        self._start_btn.setFixedHeight(36)
        self._start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self._start_btn.clicked.connect(self._start_session)
        layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("⏹ Stop")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self._stop_btn.clicked.connect(self._stop_session)
        layout.addWidget(self._stop_btn)

        layout.addSpacing(20)

        # Data actions group
        data_label = QLabel("Data Actions:")
        data_label.setStyleSheet("font-weight: bold; color: #495057;")
        layout.addWidget(data_label)

        self._save_btn = QPushButton("💾 Save Measurement")
        self._save_btn.setFixedHeight(36)
        self._save_btn.setEnabled(False)
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self._save_btn.clicked.connect(self._save_measurement)
        layout.addWidget(self._save_btn)

        self._export_csv_btn = QPushButton("📊 Export CSV")
        self._export_csv_btn.setFixedHeight(36)
        self._export_csv_btn.setEnabled(False)
        self._export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self._export_csv_btn.clicked.connect(self._export_csv)
        layout.addWidget(self._export_csv_btn)

        self._export_excel_btn = QPushButton("📈 Export Excel")
        self._export_excel_btn.setFixedHeight(36)
        self._export_excel_btn.setEnabled(False)
        self._export_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self._export_excel_btn.clicked.connect(self._export_excel)
        layout.addWidget(self._export_excel_btn)

        layout.addStretch()

        return action_frame

    # --- Instrument status strip ---

    def _add_instrument_status_row(self, layout: QHBoxLayout, instruments: list[str]) -> None:
        """Add compact instrument status indicators"""
        for name in instruments:
            label = QLabel("● " + name)
            label.setObjectName(f"instrument_led_seebeck_{name}")
            label.setStyleSheet(
                "color: #6c757d; font-size: 9px; font-weight: bold; padding: 2px 6px;"
            )  # grey (unknown) - smaller font and padding
            layout.addWidget(label)

        if instruments:
            connect_btn = QPushButton("Connect")
            connect_btn.setFixedHeight(24)  # Smaller button
            connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 10px;
                    font-size: 9pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
            """)
            connect_btn.clicked.connect(self._connect_instruments)
            layout.addWidget(connect_btn)

            check_btn = QPushButton("Check")
            check_btn.setFixedHeight(24)  # Smaller button
            check_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 3px;
                    padding: 2px 10px;
                    font-size: 9pt;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0f6ff;
                }
            """)
            check_btn.clicked.connect(self._check_connections)
            layout.addWidget(check_btn)

    def _update_led(self, name: str, connected: bool) -> None:
        """Update instrument status indicator"""
        label: QLabel = self.findChild(QLabel, f"instrument_led_seebeck_{name}")
        if not label:
            return
        color = "#28a745" if connected else "#dc3545"  # green / red
        label.setStyleSheet(
            f"color: {color}; font-size: 9px; font-weight: bold; padding: 2px 6px;"
        )
    
    def _update_status_indicator(self, status: str, color: str = "#6c757d") -> None:
        """Update main status indicator"""
        if hasattr(self, '_status_indicator'):
            self._status_indicator.setText(f"● {status}")
            self._status_indicator.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")

    def _connect_instruments(self) -> None:
        statuses = self.keithley.connect_all()
        for key in ("2182A", "2700", "PK160"):
            status = statuses.get(key)
            self._update_led(key, bool(status and status.connected))

    def _check_connections(self) -> None:
        statuses = self.keithley.get_connection_status()
        for key in ("2182A", "2700", "PK160"):
            status = statuses.get(key)
            self._update_led(key, bool(status and status.connected))

    # --- Session control ---

    def _start_session(self) -> None:
        if not self._diagram:
            return

        params_base = self._diagram.get_params()

        # For now we keep start/stop current fixed; they can be added into the diagram later
        start_current = 0.0
        stop_current = 1.0

        params = {
            "interval": params_base["interval"],
            "pre_time": params_base["pre_time"],
            "start_volt": start_current,
            "stop_volt": stop_current,
            "inc_rate": params_base["inc_rate"],
            "dec_rate": params_base["dec_rate"],
            "hold_time": params_base["hold_time"],
        }

        ok = self.keithley.start_seebeck_session(params)
        if not ok:
            QMessageBox.warning(self, "Error", "Failed to start measurement session")
            return

        if self._table:
            self._table.setRowCount(0)
        self._last_count = 0

        if self._start_btn and self._stop_btn:
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(True)
        
        if self._save_btn:
            self._save_btn.setEnabled(False)
        if self._export_csv_btn:
            self._export_csv_btn.setEnabled(False)
        if self._export_excel_btn:
            self._export_excel_btn.setEnabled(False)

        self._update_status_indicator("Running", "#28a745")
        self._timer.start()

    def _stop_session(self) -> None:
        self.keithley.stop_seebeck_session()
        self._timer.stop()
        if self._start_btn and self._stop_btn:
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)
        
        # Enable save/export buttons if we have data
        data = self.keithley.get_seebeck_data()
        if data and len(data) > 0:
            if self._save_btn:
                self._save_btn.setEnabled(True)
            if self._export_csv_btn:
                self._export_csv_btn.setEnabled(True)
            if self._export_excel_btn:
                self._export_excel_btn.setEnabled(True)
            self._update_status_indicator("Completed", "#17a2b8")
        else:
            self._update_status_indicator("Ready", "#6c757d")

    # --- Live data polling ---

    def _refresh_live_data(self) -> None:
        status = self.keithley.get_seebeck_status()
        if not status.get("active"):
            self._timer.stop()
            if self._start_btn and self._stop_btn:
                self._start_btn.setEnabled(True)
                self._stop_btn.setEnabled(False)
            
            # Enable save/export if we have data
            data = self.keithley.get_seebeck_data()
            if data and len(data) > 0:
                if self._save_btn:
                    self._save_btn.setEnabled(True)
                if self._export_csv_btn:
                    self._export_csv_btn.setEnabled(True)
                if self._export_excel_btn:
                    self._export_excel_btn.setEnabled(True)
                self._update_status_indicator("Completed", "#17a2b8")
            else:
                self._update_status_indicator("Ready", "#6c757d")
            return

        data = self.keithley.get_seebeck_data()
        if not self._table:
            return

        new_rows = data[self._last_count :]
        current_rows = self._table.rowCount()
        self._table.setRowCount(current_rows + len(new_rows))

        for i, row in enumerate(new_rows, start=current_rows):
            self._table.setItem(i, 0, QTableWidgetItem(str(row.get("Time [s]", ""))))
            self._table.setItem(i, 1, QTableWidgetItem(self._fmt_float(row.get("TEMF [mV]"))))
            self._table.setItem(i, 2, QTableWidgetItem(self._fmt_float(row.get("Temp1 [oC]"))))
            self._table.setItem(i, 3, QTableWidgetItem(self._fmt_float(row.get("Temp2 [oC]"))))
            self._table.setItem(
                i, 4, QTableWidgetItem(self._fmt_float(row.get("Delta Temp [oC]")))
            )

        self._last_count = len(data)
        
        # Update graphs
        if self._live_graph:
            self._live_graph.update_data(data)
        if self._delta_graph:
            self._delta_graph.update_data(data)
        
        # Auto-scroll table to bottom
        if self._table:
            self._table.scrollToBottom()

    @staticmethod
    def _fmt_float(value) -> str:
        try:
            if value is None:
                return ""
            return f"{float(value):.3f}"
        except Exception:
            return str(value) if value is not None else ""

    # --- Save and Export ---

    def _save_measurement(self) -> None:
        """Save current measurement data to database"""
        data = self.keithley.get_seebeck_data()
        if not data or len(data) == 0:
            QMessageBox.warning(self, "No Data", "No measurement data to save")
            return
        
        user = self.session_manager.get_current_user()
        if not user:
            QMessageBox.warning(self, "Error", "User not authenticated")
            return
        
        # Get measurement parameters
        params = self._diagram.get_params() if self._diagram else {}
        status = self.keithley.get_seebeck_status()
        session_params = status.get("params", {})
        
        # Save raw data to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seebeck_{timestamp}.json"
        raw_data_path = os.path.join(self.config.raw_data_path, filename)
        
        # Ensure directory exists
        os.makedirs(self.config.raw_data_path, exist_ok=True)
        
        # Save raw data as JSON
        raw_data = {
            "measurement_data": data,
            "parameters": {
                **params,
                **session_params,
            },
            "timestamp": timestamp,
        }
        
        try:
            with open(raw_data_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save raw data file: {str(e)}")
            return
        
        # Calculate statistics
        temf_values = [row.get("TEMF [mV]") for row in data if row.get("TEMF [mV]") is not None]
        temp1_values = [row.get("Temp1 [oC]") for row in data if row.get("Temp1 [oC]") is not None]
        temp2_values = [row.get("Temp2 [oC]") for row in data if row.get("Temp2 [oC]") is not None]
        
        # Prepare parsed data for database
        parsed_data = {
            "data_points": data,
            "statistics": {
                "temf": {
                    "min": min(temf_values) if temf_values else None,
                    "max": max(temf_values) if temf_values else None,
                    "avg": sum(temf_values) / len(temf_values) if temf_values else None,
                },
                "temp1": {
                    "min": min(temp1_values) if temp1_values else None,
                    "max": max(temp1_values) if temp1_values else None,
                    "avg": sum(temp1_values) / len(temp1_values) if temp1_values else None,
                },
                "temp2": {
                    "min": min(temp2_values) if temp2_values else None,
                    "max": max(temp2_values) if temp2_values else None,
                    "avg": sum(temp2_values) / len(temp2_values) if temp2_values else None,
                },
            },
        }
        
        # Determine temperature range
        if temp1_values and temp2_values:
            all_temps = temp1_values + temp2_values
            temp_range = f"{min(all_temps):.1f}-{max(all_temps):.1f}°C"
        else:
            temp_range = None
        
        # Save to database
        db = next(get_db())
        try:
            measurement = self.measurement_service.create_measurement(
                db=db,
                workbook_id=self.workbook_id,
                user=user,
                measurement_type=MeasurementType.SEEBECK,
                raw_data_path=raw_data_path,
                parsed_data=parsed_data,
                instrument_settings=session_params,
                temperature_range=temp_range,
                notes=f"Seebeck measurement with {len(data)} data points",
            )
            QMessageBox.information(
                self,
                "Success",
                f"Measurement saved successfully!\nMeasurement ID: {measurement.id}\nData points: {len(data)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save measurement: {str(e)}")
        finally:
            db.close()

    def _export_csv(self) -> None:
        """Export measurement data to CSV file"""
        data = self.keithley.get_seebeck_data()
        if not data or len(data) == 0:
            QMessageBox.warning(self, "No Data", "No measurement data to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"seebeck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)",
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["Time [s]", "TEMF [mV]", "Temp1 [oC]", "Temp2 [oC]", "Delta Temp [oC]"],
                )
                writer.writeheader()
                writer.writerows(data)
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")

    def _export_excel(self) -> None:
        """Export measurement data to Excel file with graphs"""
        try:
            from openpyxl import Workbook
            from openpyxl.drawing.image import Image
            import io
        except ImportError:
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "openpyxl is required for Excel export. Please install it: pip install openpyxl",
            )
            return
        
        data = self.keithley.get_seebeck_data()
        if not data or len(data) == 0:
            QMessageBox.warning(self, "No Data", "No measurement data to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Excel",
            f"seebeck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)",
        )
        
        if not filename:
            return
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Seebeck Data"
            
            # Write headers
            headers = ["Time [s]", "TEMF [mV]", "Temp1 [oC]", "Temp2 [oC]", "Delta Temp [oC]"]
            ws.append(headers)
            
            # Write data
            for row in data:
                ws.append([
                    row.get("Time [s]", ""),
                    row.get("TEMF [mV]"),
                    row.get("Temp1 [oC]"),
                    row.get("Temp2 [oC]"),
                    row.get("Delta Temp [oC]"),
                ])
            
            # Save graphs as images and add to Excel
            if self._live_graph:
                buf = io.BytesIO()
                self._live_graph.figure.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image(buf)
                img.anchor = f'A{len(data) + 3}'
                ws.add_image(img)
            
            if self._delta_graph:
                buf = io.BytesIO()
                self._delta_graph.figure.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image(buf)
                img.anchor = f'A{len(data) + 400}'  # Place below first graph
                ws.add_image(img)
            
            wb.save(filename)
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export Excel: {str(e)}")
