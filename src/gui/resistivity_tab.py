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
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import csv
import json
import os
from datetime import datetime
from typing import Optional

from src.instruments.keithley_connection import KeithleyConnection
from src.database import get_db
from src.models import MeasurementType
from src.services.measurement_service import MeasurementService
from src.auth import SessionManager
from src.utils import Config


class IVCurveGraphWidget(QWidget):
    """I-V curve graph showing Current vs Voltage"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.set_xlabel('Voltage (V)', fontsize=10)
        self.ax.set_ylabel('Current (A)', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        self.figure.tight_layout()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
    
    def update_data(self, data: list, show_fit_line: bool = False):
        """Update graph with new data"""
        if not data:
            return
        
        voltages = [row.get("Voltage [V]") for row in data if row.get("Voltage [V]") is not None]
        currents = [row.get("Current [A]") for row in data if row.get("Current [A]") is not None]
        
        self.ax.clear()
        self.ax.set_xlabel('Voltage (V)', fontsize=10)
        self.ax.set_ylabel('Current (A)', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        if voltages and currents:
            valid_indices = [i for i, (v, i) in enumerate(zip(voltages, currents)) 
                           if v is not None and i is not None]
            if valid_indices:
                valid_voltages = [voltages[i] for i in valid_indices]
                valid_currents = [currents[i] for i in valid_indices]
                self.ax.plot(valid_voltages, valid_currents, 'bo-', markersize=4, 
                           linewidth=1.5, label='I-V Curve', alpha=0.7)
                
                # Linear fit line if requested
                if show_fit_line and len(valid_voltages) >= 2:
                    try:
                        coeffs = np.polyfit(valid_voltages, valid_currents, 1)
                        fit_line = np.poly1d(coeffs)
                        v_min, v_max = min(valid_voltages), max(valid_voltages)
                        v_fit = np.linspace(v_min, v_max, 100)
                        i_fit = fit_line(v_fit)
                        self.ax.plot(v_fit, i_fit, 'r--', linewidth=1.5, 
                                   label='Linear Fit', alpha=0.6)
                    except:
                        pass
        
        self.ax.legend(loc='best', fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()


class ResistanceGraphWidget(QWidget):
    """Resistance vs Voltage graph"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.set_xlabel('Voltage (V)', fontsize=10)
        self.ax.set_ylabel('Resistance (Ω)', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        self.figure.tight_layout()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
    
    def update_data(self, data: list):
        """Update graph with new data"""
        if not data:
            return
        
        voltages = [row.get("Voltage [V]") for row in data if row.get("Voltage [V]") is not None]
        resistances = [row.get("Resistance [Ohm]") for row in data 
                      if row.get("Resistance [Ohm]") is not None]
        
        self.ax.clear()
        self.ax.set_xlabel('Voltage (V)', fontsize=10)
        self.ax.set_ylabel('Resistance (Ω)', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        
        if voltages and resistances:
            valid_indices = [i for i, (v, r) in enumerate(zip(voltages, resistances)) 
                           if v is not None and r is not None]
            if valid_indices:
                valid_voltages = [voltages[i] for i in valid_indices]
                valid_resistances = [resistances[i] for i in valid_indices]
                self.ax.plot(valid_voltages, valid_resistances, 'ro-', markersize=4, 
                           linewidth=1.5, label='Resistance', alpha=0.7)
        
        self.ax.legend(loc='best', fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()


class ResistivityTab(QWidget):
    """
    Resistivity measurement tab UI with I-V sweep functionality.
    
    Features:
    - I-V sweep measurement parameters
    - Sample dimensions input (for resistivity calculation)
    - Live I-V curve and Resistance vs Voltage graphs
    - Data table with real-time updates
    - Save measurement to database
    - Export to CSV/Excel
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
        self._timer.setInterval(500)  # Poll every 500ms during sweep
        self._timer.timeout.connect(self._refresh_live_data)
        self._last_count: int = 0

        # UI references
        self._table: QTableWidget | None = None
        self._start_btn: QPushButton | None = None
        self._stop_btn: QPushButton | None = None
        self._save_btn: QPushButton | None = None
        self._export_csv_btn: QPushButton | None = None
        self._export_excel_btn: QPushButton | None = None
        self._iv_graph: IVCurveGraphWidget | None = None
        self._resistance_graph: ResistanceGraphWidget | None = None

        # Parameter inputs
        self._start_voltage_input: QDoubleSpinBox | None = None
        self._stop_voltage_input: QDoubleSpinBox | None = None
        self._points_input: QSpinBox | None = None
        self._delay_input: QDoubleSpinBox | None = None
        self._current_limit_input: QDoubleSpinBox | None = None
        self._voltage_limit_input: QDoubleSpinBox | None = None
        self._length_input: QDoubleSpinBox | None = None
        self._width_input: QDoubleSpinBox | None = None
        self._thickness_input: QDoubleSpinBox | None = None
        self._show_resistivity_check: QCheckBox | None = None
        self._show_fit_line_check: QCheckBox | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Top row: title + instrument status strip
        top_row = QHBoxLayout()

        header = QLabel("Resistivity Measurement / 抵抗率測定")
        header_font = header.font()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        top_row.addWidget(header)

        top_row.addStretch()

        # Instrument LED for 2401
        self._add_instrument_status_row(top_row, instruments=["2401"])

        layout.addLayout(top_row)

        # Main content: Splitter for parameters (left) and graphs+table (right)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT SIDE: Parameters Panel ===
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        params_layout.setContentsMargins(4, 4, 4, 4)
        params_layout.setSpacing(8)

        # Sweep Parameters
        sweep_group = QGroupBox("Sweep Parameters")
        sweep_layout = QFormLayout()
        sweep_layout.setSpacing(6)

        self._start_voltage_input = QDoubleSpinBox()
        self._start_voltage_input.setRange(-100.0, 100.0)
        self._start_voltage_input.setValue(0.0)
        self._start_voltage_input.setDecimals(3)
        self._start_voltage_input.setSuffix(" V")
        sweep_layout.addRow("Start Voltage:", self._start_voltage_input)

        self._stop_voltage_input = QDoubleSpinBox()
        self._stop_voltage_input.setRange(-100.0, 100.0)
        self._stop_voltage_input.setValue(10.0)
        self._stop_voltage_input.setDecimals(3)
        self._stop_voltage_input.setSuffix(" V")
        sweep_layout.addRow("Stop Voltage:", self._stop_voltage_input)

        self._points_input = QSpinBox()
        self._points_input.setRange(2, 1000)
        self._points_input.setValue(10)
        sweep_layout.addRow("Points:", self._points_input)

        self._delay_input = QDoubleSpinBox()
        self._delay_input.setRange(10.0, 1000.0)
        self._delay_input.setValue(50.0)
        self._delay_input.setDecimals(0)
        self._delay_input.setSuffix(" ms")
        sweep_layout.addRow("Delay:", self._delay_input)

        self._current_limit_input = QDoubleSpinBox()
        self._current_limit_input.setRange(0.001, 1.0)
        self._current_limit_input.setValue(0.1)
        self._current_limit_input.setDecimals(3)
        self._current_limit_input.setSuffix(" A")
        sweep_layout.addRow("Current Limit:", self._current_limit_input)

        self._voltage_limit_input = QDoubleSpinBox()
        self._voltage_limit_input.setRange(1.0, 100.0)
        self._voltage_limit_input.setValue(21.0)
        self._voltage_limit_input.setDecimals(1)
        self._voltage_limit_input.setSuffix(" V")
        sweep_layout.addRow("Voltage Limit:", self._voltage_limit_input)

        sweep_group.setLayout(sweep_layout)
        params_layout.addWidget(sweep_group)

        # Sample Dimensions
        dims_group = QGroupBox("Sample Dimensions (for Resistivity)")
        dims_layout = QFormLayout()
        dims_layout.setSpacing(6)

        self._length_input = QDoubleSpinBox()
        self._length_input.setRange(0.000001, 1.0)
        self._length_input.setValue(0.01)
        self._length_input.setDecimals(6)
        self._length_input.setSuffix(" m")
        dims_layout.addRow("Length:", self._length_input)

        self._width_input = QDoubleSpinBox()
        self._width_input.setRange(0.000001, 1.0)
        self._width_input.setValue(0.01)
        self._width_input.setDecimals(6)
        self._width_input.setSuffix(" m")
        dims_layout.addRow("Width:", self._width_input)

        self._thickness_input = QDoubleSpinBox()
        self._thickness_input.setRange(0.000001, 1.0)
        self._thickness_input.setValue(0.001)
        self._thickness_input.setDecimals(6)
        self._thickness_input.setSuffix(" m")
        dims_layout.addRow("Thickness:", self._thickness_input)

        dims_group.setLayout(dims_layout)
        params_layout.addWidget(dims_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self._show_resistivity_check = QCheckBox("Show Resistivity Column")
        self._show_resistivity_check.setChecked(False)
        self._show_resistivity_check.toggled.connect(self._update_table_columns)
        options_layout.addWidget(self._show_resistivity_check)
        
        self._show_fit_line_check = QCheckBox("Show Linear Fit on I-V Curve")
        self._show_fit_line_check.setChecked(False)
        options_layout.addWidget(self._show_fit_line_check)
        
        options_group.setLayout(options_layout)
        params_layout.addWidget(options_group)

        # Control buttons
        btn_layout = QVBoxLayout()
        
        self._start_btn = QPushButton("Start I-V Sweep")
        self._start_btn.setFixedHeight(32)
        self._start_btn.setStyleSheet("""
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
        """)
        self._start_btn.clicked.connect(self._start_sweep)
        btn_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedHeight(32)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_sweep)
        btn_layout.addWidget(self._stop_btn)

        self._save_btn = QPushButton("Save Measurement")
        self._save_btn.setFixedHeight(28)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_measurement)
        btn_layout.addWidget(self._save_btn)

        self._export_csv_btn = QPushButton("Export CSV")
        self._export_csv_btn.setFixedHeight(28)
        self._export_csv_btn.setEnabled(False)
        self._export_csv_btn.clicked.connect(self._export_csv)
        btn_layout.addWidget(self._export_csv_btn)

        self._export_excel_btn = QPushButton("Export Excel")
        self._export_excel_btn.setFixedHeight(28)
        self._export_excel_btn.setEnabled(False)
        self._export_excel_btn.clicked.connect(self._export_excel)
        btn_layout.addWidget(self._export_excel_btn)

        params_layout.addLayout(btn_layout)
        params_layout.addStretch()

        main_splitter.addWidget(params_widget)

        # === RIGHT SIDE: Graphs + Table (Vertical Split) ===
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Graphs (Top)
        graphs_widget = QWidget()
        graphs_layout = QVBoxLayout(graphs_widget)
        graphs_layout.setContentsMargins(4, 4, 4, 4)
        graphs_layout.setSpacing(4)

        # I-V Curve
        iv_label = QLabel("I-V Curve / I-V特性")
        iv_label_font = iv_label.font()
        iv_label_font.setPointSize(10)
        iv_label_font.setBold(True)
        iv_label.setFont(iv_label_font)
        graphs_layout.addWidget(iv_label)

        self._iv_graph = IVCurveGraphWidget(self)
        self._iv_graph.setMinimumHeight(300)
        graphs_layout.addWidget(self._iv_graph)

        # Resistance vs Voltage
        r_label = QLabel("Resistance vs Voltage / 抵抗 vs 電圧")
        r_label_font = r_label.font()
        r_label_font.setPointSize(10)
        r_label_font.setBold(True)
        r_label.setFont(r_label_font)
        graphs_layout.addWidget(r_label)

        self._resistance_graph = ResistanceGraphWidget(self)
        self._resistance_graph.setMinimumHeight(300)
        graphs_layout.addWidget(self._resistance_graph)

        right_splitter.addWidget(graphs_widget)

        # Data Table (Bottom)
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(4, 4, 4, 4)
        table_layout.setSpacing(4)

        table_label = QLabel("Data Table / データ表")
        table_label_font = table_label.font()
        table_label_font.setPointSize(10)
        table_label_font.setBold(True)
        table_label.setFont(table_label_font)
        table_layout.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["#", "Voltage [V]", "Current [A]", "Resistance [Ω]", "Resistivity [Ω·m]"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        # Initially hide resistivity column
        self._table.setColumnHidden(4, True)
        table_layout.addWidget(self._table)

        right_splitter.addWidget(table_widget)
        right_splitter.setSizes([600, 400])

        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([400, 1000])

        layout.addWidget(main_splitter)

    # --- Instrument status strip ---

    def _add_instrument_status_row(self, layout: QHBoxLayout, instruments: list[str]) -> None:
        for name in instruments:
            label = QLabel("● " + name)
            label.setObjectName(f"instrument_led_resistivity_{name}")
            label.setStyleSheet(
                "color: #999; font-size: 11px; padding-left: 4px; padding-right: 8px;"
            )
            layout.addWidget(label)

        if instruments:
            connect_btn = QPushButton("Connect")
            connect_btn.setFixedHeight(24)
            connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 2px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
            """)
            connect_btn.clicked.connect(self._connect_instruments)
            layout.addWidget(connect_btn)

            check_btn = QPushButton("Check Connection")
            check_btn.setFixedHeight(24)
            check_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 4px;
                    padding: 2px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f0f6ff;
                }
            """)
            check_btn.clicked.connect(self._check_connections)
            layout.addWidget(check_btn)

    def _update_led(self, name: str, connected: bool) -> None:
        label: QLabel = self.findChild(QLabel, f"instrument_led_resistivity_{name}")
        if not label:
            return
        color = "#28a745" if connected else "#dc3545"
        label.setStyleSheet(
            f"color: {color}; font-size: 11px; padding-left: 4px; padding-right: 8px;"
        )

    def _connect_instruments(self) -> None:
        statuses = self.keithley.connect_all()
        status = statuses.get("2401")
        self._update_led("2401", bool(status and status.connected))

    def _check_connections(self) -> None:
        statuses = self.keithley.get_connection_status()
        status = statuses.get("2401")
        self._update_led("2401", bool(status and status.connected))
    
    def _update_table_columns(self) -> None:
        """Show/hide resistivity column based on checkbox"""
        if self._table and self._show_resistivity_check:
            show = self._show_resistivity_check.isChecked()
            self._table.setColumnHidden(4, not show)
            # Update existing rows to show/hide resistivity values
            data = self.keithley.get_iv_sweep_data()
            if data and self._table.rowCount() > 0:
                for i, row in enumerate(data):
                    if i < self._table.rowCount():
                        resistivity = row.get("Resistivity [Ohm·m]")
                        if show and resistivity is not None:
                            self._table.setItem(i, 4, QTableWidgetItem(self._fmt_scientific(resistivity)))
                        elif not show:
                            self._table.setItem(i, 4, QTableWidgetItem(""))

    # --- Session control ---

    def _start_sweep(self) -> None:
        if not all([self._start_voltage_input, self._stop_voltage_input, 
                   self._points_input, self._delay_input]):
            return

        params = {
            "start_voltage": self._start_voltage_input.value(),
            "stop_voltage": self._stop_voltage_input.value(),
            "points": self._points_input.value(),
            "delay_ms": self._delay_input.value(),
            "current_limit": self._current_limit_input.value(),
            "voltage_limit": self._voltage_limit_input.value(),
        }

        # Add sample dimensions if provided
        if self._length_input and self._width_input and self._thickness_input:
            if (self._length_input.value() > 0 and 
                self._width_input.value() > 0 and 
                self._thickness_input.value() > 0):
                params["length"] = self._length_input.value()
                params["width"] = self._width_input.value()
                params["thickness"] = self._thickness_input.value()

        ok = self.keithley.start_iv_sweep_session(params)
        if not ok:
            QMessageBox.warning(self, "Error", "Failed to start I-V sweep session")
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

        self._timer.start()

    def _stop_sweep(self) -> None:
        self.keithley.stop_iv_sweep_session()
        self._timer.stop()
        if self._start_btn and self._stop_btn:
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)

        # Enable save/export if we have data
        data = self.keithley.get_iv_sweep_data()
        if data and len(data) > 0:
            if self._save_btn:
                self._save_btn.setEnabled(True)
            if self._export_csv_btn:
                self._export_csv_btn.setEnabled(True)
            if self._export_excel_btn:
                self._export_excel_btn.setEnabled(True)

    # --- Live data polling ---

    def _refresh_live_data(self) -> None:
        status = self.keithley.get_iv_sweep_status()
        if not status.get("active"):
            self._timer.stop()
            if self._start_btn and self._stop_btn:
                self._start_btn.setEnabled(True)
                self._stop_btn.setEnabled(False)

            # Enable save/export if we have data
            data = self.keithley.get_iv_sweep_data()
            if data and len(data) > 0:
                if self._save_btn:
                    self._save_btn.setEnabled(True)
                if self._export_csv_btn:
                    self._export_csv_btn.setEnabled(True)
                if self._export_excel_btn:
                    self._export_excel_btn.setEnabled(True)
            return

        data = self.keithley.get_iv_sweep_data()
        if not self._table:
            return

        new_rows = data[self._last_count :]
        current_rows = self._table.rowCount()
        self._table.setRowCount(current_rows + len(new_rows))

        show_resistivity = (self._show_resistivity_check and 
                          self._show_resistivity_check.isChecked())

        for i, row in enumerate(new_rows, start=current_rows):
            self._table.setItem(i, 0, QTableWidgetItem(str(row.get("Index", i + 1))))
            self._table.setItem(i, 1, QTableWidgetItem(self._fmt_float(row.get("Voltage [V]"))))
            self._table.setItem(i, 2, QTableWidgetItem(self._fmt_scientific(row.get("Current [A]"))))
            self._table.setItem(i, 3, QTableWidgetItem(self._fmt_scientific(row.get("Resistance [Ohm]"))))
            
            resistivity = row.get("Resistivity [Ohm·m]")
            if show_resistivity and resistivity is not None:
                self._table.setItem(i, 4, QTableWidgetItem(self._fmt_scientific(resistivity)))
            else:
                self._table.setItem(i, 4, QTableWidgetItem(""))

        self._last_count = len(data)

        # Update graphs
        if self._iv_graph:
            show_fit = (self._show_fit_line_check and 
                       self._show_fit_line_check.isChecked())
            self._iv_graph.update_data(data, show_fit_line=show_fit)
        if self._resistance_graph:
            self._resistance_graph.update_data(data)

        # Auto-scroll table to bottom
        if self._table:
            self._table.scrollToBottom()

    @staticmethod
    def _fmt_float(value) -> str:
        try:
            if value is None:
                return ""
            return f"{float(value):.6f}"
        except Exception:
            return str(value) if value is not None else ""

    @staticmethod
    def _fmt_scientific(value) -> str:
        try:
            if value is None:
                return ""
            val = float(value)
            if abs(val) < 1e-3 or abs(val) > 1e3:
                return f"{val:.3e}"
            return f"{val:.6f}"
        except Exception:
            return str(value) if value is not None else ""

    # --- Save and Export ---

    def _save_measurement(self) -> None:
        """Save current measurement data to database"""
        data = self.keithley.get_iv_sweep_data()
        if not data or len(data) == 0:
            QMessageBox.warning(self, "No Data", "No measurement data to save")
            return

        user = self.session_manager.get_current_user()
        if not user:
            QMessageBox.warning(self, "Error", "User not authenticated")
            return

        # Get measurement parameters
        status = self.keithley.get_iv_sweep_status()
        session_params = status.get("params", {})

        # Save raw data to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resistivity_{timestamp}.json"
        raw_data_path = os.path.join(self.config.raw_data_path, filename)

        os.makedirs(self.config.raw_data_path, exist_ok=True)

        raw_data = {
            "measurement_data": data,
            "parameters": session_params,
            "timestamp": timestamp,
        }

        try:
            with open(raw_data_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save raw data file: {str(e)}")
            return

        # Calculate statistics
        voltages = [row.get("Voltage [V]") for row in data if row.get("Voltage [V]") is not None]
        currents = [row.get("Current [A]") for row in data if row.get("Current [A]") is not None]
        resistances = [row.get("Resistance [Ohm]") for row in data 
                      if row.get("Resistance [Ohm]") is not None]
        resistivities = [row.get("Resistivity [Ohm·m]") for row in data 
                        if row.get("Resistivity [Ohm·m]") is not None]

        parsed_data = {
            "data_points": data,
            "statistics": {
                "voltage": {
                    "min": min(voltages) if voltages else None,
                    "max": max(voltages) if voltages else None,
                    "avg": sum(voltages) / len(voltages) if voltages else None,
                },
                "current": {
                    "min": min(currents) if currents else None,
                    "max": max(currents) if currents else None,
                    "avg": sum(currents) / len(currents) if currents else None,
                },
                "resistance": {
                    "min": min(resistances) if resistances else None,
                    "max": max(resistances) if resistances else None,
                    "avg": sum(resistances) / len(resistances) if resistances else None,
                },
            },
        }

        if resistivities:
            parsed_data["statistics"]["resistivity"] = {
                "min": min(resistivities),
                "max": max(resistivities),
                "avg": sum(resistivities) / len(resistivities),
            }

        # Determine voltage range
        if voltages:
            voltage_range = f"{min(voltages):.3f}-{max(voltages):.3f}V"
        else:
            voltage_range = None

        # Save to database
        db = next(get_db())
        try:
            measurement = self.measurement_service.create_measurement(
                db=db,
                workbook_id=self.workbook_id,
                user=user,
                measurement_type=MeasurementType.RESISTIVITY,
                raw_data_path=raw_data_path,
                parsed_data=parsed_data,
                instrument_settings=session_params,
                temperature_range=voltage_range,
                notes=f"Resistivity measurement with {len(data)} data points",
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
        data = self.keithley.get_iv_sweep_data()
        if not data or len(data) == 0:
            QMessageBox.warning(self, "No Data", "No measurement data to export")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"resistivity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)",
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["Index", "Voltage [V]", "Current [A]", 
                              "Resistance [Ohm]", "Resistivity [Ohm·m]"],
                )
                writer.writeheader()
                for row in data:
                    writer.writerow({
                        "Index": row.get("Index", ""),
                        "Voltage [V]": row.get("Voltage [V]"),
                        "Current [A]": row.get("Current [A]"),
                        "Resistance [Ohm]": row.get("Resistance [Ohm]"),
                        "Resistivity [Ohm·m]": row.get("Resistivity [Ohm·m]"),
                    })
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

        data = self.keithley.get_iv_sweep_data()
        if not data or len(data) == 0:
            QMessageBox.warning(self, "No Data", "No measurement data to export")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Excel",
            f"resistivity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)",
        )

        if not filename:
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Resistivity Data"

            # Write headers
            headers = ["#", "Voltage [V]", "Current [A]", "Resistance [Ω]", "Resistivity [Ω·m]"]
            ws.append(headers)

            # Write data
            for row in data:
                ws.append([
                    row.get("Index", ""),
                    row.get("Voltage [V]"),
                    row.get("Current [A]"),
                    row.get("Resistance [Ohm]"),
                    row.get("Resistivity [Ohm·m]"),
                ])

            # Save graphs as images and add to Excel
            if self._iv_graph:
                buf = io.BytesIO()
                self._iv_graph.figure.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image(buf)
                img.anchor = f'A{len(data) + 3}'
                ws.add_image(img)

            if self._resistance_graph:
                buf = io.BytesIO()
                self._resistance_graph.figure.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image(buf)
                img.anchor = f'A{len(data) + 400}'
                ws.add_image(img)

            wb.save(filename)
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export Excel: {str(e)}")

