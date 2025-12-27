from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, QTimer

from src.instruments.keithley_connection import KeithleyConnection
from src.gui.seebeck_diagram_widget import SeebeckDiagramWidget


class SeebeckTab(QWidget):
    """
    Seebeck measurement tab UI.

    Encapsulates:
    - Instrument status indicators (2182A, 2700, PK160)
    - Parameter controls (interval, pre-time, start/stop current, ramp rates, hold time)
    - Start/Stop controls
    - Live data table fed by SeebeckSessionManager (via KeithleyConnection)
    """

    def __init__(self, keithley: KeithleyConnection, parent: QWidget | None = None):
        super().__init__(parent)
        self.keithley = keithley

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

        # Start / Stop buttons under the diagram
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("Start Measurement")
        self._start_btn.setFixedHeight(28)
        self._start_btn.clicked.connect(self._start_session)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedHeight(28)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_session)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Live data table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Time [s]", "TEMF [mV]", "Temp1 [°C]", "Temp2 [°C]", "Delta Temp [°C]"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

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
            return

        if self._table:
            self._table.setRowCount(0)
        self._last_count = 0

        if self._start_btn and self._stop_btn:
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(True)

        self._timer.start()

    def _stop_session(self) -> None:
        self.keithley.stop_seebeck_session()
        self._timer.stop()
        if self._start_btn and self._stop_btn:
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)

    # --- Live data polling ---

    def _refresh_live_data(self) -> None:
        status = self.keithley.get_seebeck_status()
        if not status.get("active"):
            self._timer.stop()
            if self._start_btn and self._stop_btn:
                self._start_btn.setEnabled(True)
                self._stop_btn.setEnabled(False)
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

    @staticmethod
    def _fmt_float(value) -> str:
        try:
            if value is None:
                return ""
            return f"{float(value):.3f}"
        except Exception:
            return str(value) if value is not None else ""


