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
        
        self.temf_line = None
        self.temp1_line = None
        self.temp2_line = None
    
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
    Enhanced Seebeck measurement tab UI with graphs, save, and export.
    
    Encapsulates:
    - Instrument status indicators (2182A, 2700, PK160)
    - Parameter controls (interval, pre-time, start/stop current, ramp rates, hold time)
    - Start/Stop controls
    - Live data table fed by SeebeckSessionManager (via KeithleyConnection)
    - Live graphs (TEMF/Temp vs Time, TEMF vs Delta Temp)
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Top row: title + instrument status strip
        top_row = QHBoxLayout()

        header = QLabel("Seebeck Measurement")
        header_font = header.font()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        top_row.addWidget(header)

        top_row.addStretch()

        # Instrument LEDs + Connect / Check
        self._add_instrument_status_row(top_row, instruments=["2182A", "2700", "PK160"])

        layout.addLayout(top_row)

        # Diagram (the only place where parameters are edited)
        self._diagram = SeebeckDiagramWidget(self)
        self._diagram.setMinimumHeight(220)
        layout.addWidget(self._diagram)

        # Start / Stop / Save / Export buttons under the diagram
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("Start Measurement")
        self._start_btn.setFixedHeight(28)
        self._start_btn.clicked.connect(self._start_session)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedHeight(28)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_session)

        self._save_btn = QPushButton("Save Measurement")
        self._save_btn.setFixedHeight(28)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_measurement)

        self._export_csv_btn = QPushButton("Export CSV")
        self._export_csv_btn.setFixedHeight(28)
        self._export_csv_btn.setEnabled(False)
        self._export_csv_btn.clicked.connect(self._export_csv)

        self._export_excel_btn = QPushButton("Export Excel")
        self._export_excel_btn.setFixedHeight(28)
        self._export_excel_btn.setEnabled(False)
        self._export_excel_btn.clicked.connect(self._export_excel)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._export_csv_btn)
        btn_row.addWidget(self._export_excel_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Main content area: Multi-splitter layout for better space utilization
        # Horizontal splitter: Left (Graphs) | Right (IR Camera + Table)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === LEFT SIDE: Graphs (Vertical Stack) ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(4)
        
        # Live Graph
        graph_label = QLabel("Live Graph / ライブグラフ")
        graph_label_font = graph_label.font()
        graph_label_font.setPointSize(10)
        graph_label_font.setBold(True)
        graph_label.setFont(graph_label_font)
        left_layout.addWidget(graph_label)
        
        self._live_graph = LiveGraphWidget(self)
        self._live_graph.setMinimumHeight(300)
        left_layout.addWidget(self._live_graph)
        
        # Delta Temp Graph
        delta_label = QLabel("TEMF vs Delta Temp (Δt) / TEMF vs 差温度")
        delta_label_font = delta_label.font()
        delta_label_font.setPointSize(10)
        delta_label_font.setBold(True)
        delta_label.setFont(delta_label_font)
        left_layout.addWidget(delta_label)
        
        self._delta_graph = DeltaTempGraphWidget(self)
        self._delta_graph.setMinimumHeight(300)
        left_layout.addWidget(self._delta_graph)
        
        main_splitter.addWidget(left_widget)
        
        # === RIGHT SIDE: IR Camera + Data Table (Vertical Split) ===
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # IR Camera (Top, larger)
        self._ir_camera = IRCameraWidget(self)
        self._ir_camera.setMinimumHeight(400)
        right_splitter.addWidget(self._ir_camera)
        
        # Data Table (Bottom, smaller)
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
            ["Time [s]", "TEMF [mV]", "Temp1 [°C]", "Temp2 [°C]", "Delta Temp [°C]"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self._table)
        
        right_splitter.addWidget(table_widget)
        
        # Set right splitter proportions (60% IR Camera, 40% Table)
        right_splitter.setSizes([600, 400])
        
        main_splitter.addWidget(right_splitter)
        
        # Set main splitter proportions (50% Graphs, 50% IR Camera + Table)
        main_splitter.setSizes([800, 800])
        
        layout.addWidget(main_splitter)

    # --- Instrument status strip ---

    def _add_instrument_status_row(self, layout: QHBoxLayout, instruments: list[str]) -> None:
        for name in instruments:
            label = QLabel("● " + name)
            label.setObjectName(f"instrument_led_seebeck_{name}")
            label.setStyleSheet(
                "color: #999; font-size: 11px; padding-left: 4px; padding-right: 8px;"
            )  # grey (unknown)
            layout.addWidget(label)

        if instruments:
            connect_btn = QPushButton("Connect")
            connect_btn.setFixedHeight(24)
            connect_btn.setStyleSheet(
                """
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
                """
            )
            connect_btn.clicked.connect(self._connect_instruments)
            layout.addWidget(connect_btn)

            check_btn = QPushButton("Check Connection")
            check_btn.setFixedHeight(24)
            check_btn.setStyleSheet(
                """
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
                """
            )
            check_btn.clicked.connect(self._check_connections)
            layout.addWidget(check_btn)

    def _update_led(self, name: str, connected: bool) -> None:
        label: QLabel = self.findChild(QLabel, f"instrument_led_seebeck_{name}")
        if not label:
            return
        color = "#28a745" if connected else "#dc3545"  # green / red
        label.setStyleSheet(
            f"color: {color}; font-size: 11px; padding-left: 4px; padding-right: 8px;"
        )

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
