from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QLabel,
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QFont, QColor, QBrush


class YellowInputBox(QLineEdit):
    """
    Custom input box styled like VB TextBox with yellow background.
    Units are displayed outside the input field for better visibility.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #ffffcc;
                border: 1px solid #000000;
                border-radius: 0px;
                padding: 2px 4px;
                color: #000000;
                font-weight: bold;
                font-size: 9pt;
                selection-background-color: #316ac5;
                selection-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #000000;
            }
        """)
        # Fixed size for yellow boxes - just for the number
        self.setFixedSize(50, 20)  # Smaller since units are outside
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class SeebeckDiagramWidget(QWidget):
    """
    Exact replica of the Seebeck measurement interval diagram.
    Matches the VB form design with precise input field positions.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        # Flexible size - will scale based on available space
        self.setMinimumHeight(150)
        self.setMinimumWidth(400)  # Much smaller minimum to fit in Q1
        # No maximum constraints - let it use available space
        
        # Use native Windows font
        font = QFont("MS Shell Dlg 2", 9)
        self.setFont(font)

        # Create all yellow input boxes and their unit labels
        # 1. Measurement Interval input (top left, next to label)
        self.interval_input = YellowInputBox(self)
        self.interval_input.setText("2")
        self.interval_input.setValidator(self._create_int_validator(1, 3600))
        self.interval_unit = self._create_unit_label(" s")

        # 2. tPre input (below pre-time segment)
        self.pre_input = YellowInputBox(self)
        self.pre_input.setText("1")
        self.pre_input.setValidator(self._create_int_validator(0, 3600))
        self.pre_unit = self._create_unit_label(" s")

        # 3. tHold input (above hold segment)
        self.hold_input = YellowInputBox(self)
        self.hold_input.setText("600")
        self.hold_input.setValidator(self._create_int_validator(0, 7200))
        self.hold_unit = self._create_unit_label(" s")

        # 4. Inc. Rate input (above ramp-up segment)
        self.inc_input = YellowInputBox(self)
        self.inc_input.setText("1")
        self.inc_input.setValidator(self._create_int_validator(1, 1000))
        self.inc_unit = self._create_unit_label(" mA/s")

        # 5. Dec. Rate input (above ramp-down segment)
        self.dec_input = YellowInputBox(self)
        self.dec_input.setText("1")
        self.dec_input.setValidator(self._create_int_validator(1, 1000))
        self.dec_unit = self._create_unit_label(" mA/s")

        # 6. V-axis "0" input (left of vertical axis, at bottom) - no unit
        self.v0_input = YellowInputBox(self)
        self.v0_input.setText("0")
        self.v0_input.setValidator(self._create_int_validator(0, 10))

        # 7. V-axis "1" input (left of vertical axis, at top level) - no unit
        self.v1_input = YellowInputBox(self)
        self.v1_input.setText("1")
        self.v1_input.setValidator(self._create_int_validator(0, 10))

    def _create_int_validator(self, min_val, max_val):
        from PyQt6.QtGui import QIntValidator
        return QIntValidator(min_val, max_val, self)
    
    def _create_unit_label(self, unit_text: str) -> QLabel:
        """Create a unit label to display outside the input field"""
        label = QLabel(unit_text, self)
        label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-weight: bold;
                font-size: 9pt;
                background-color: transparent;
            }
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.adjustSize()
        return label

    def get_params(self) -> dict:
        """Return current parameter values. Converts mA/s to A/s for internal use."""
        try:
            interval = int(self.interval_input.text() or "2")
            pre_time = int(self.pre_input.text() or "1")
            hold_time = int(self.hold_input.text() or "600")
            # Rates are displayed as integers (mA/s) but converted to A/s internally
            inc_rate = float(self.inc_input.text() or "1") / 1000.0  # Convert mA/s to A/s
            dec_rate = float(self.dec_input.text() or "1") / 1000.0  # Convert mA/s to A/s
        except (ValueError, AttributeError):
            # Fallback to defaults
            interval, pre_time, hold_time = 2, 1, 600
            inc_rate = dec_rate = 1.0 / 1000.0
        
        return {
            "interval": interval,
            "pre_time": pre_time,
            "hold_time": hold_time,
            "inc_rate": inc_rate,
            "dec_rate": dec_rate,
        }

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_controls()

    def _layout_controls(self) -> None:
        """Position input boxes at exact locations matching the image - scaled to widget size."""
        # Base diagram coordinates (reference size: 1000x200)
        base_width = 1000
        base_height = 200
        base_diagram_left = 50
        base_diagram_top = 50
        base_diagram_right = 950
        base_diagram_bottom = 160
        
        # Calculate scale factors based on actual widget size
        widget_width = max(400, self.width())  # Minimum 400px
        widget_height = max(150, self.height())  # Minimum 150px
        
        scale_x = (widget_width - 20) / (base_width - 20)  # Account for margins
        scale_y = (widget_height - 20) / (base_height - 20)
        
        # Use the smaller scale to maintain aspect ratio, or allow independent scaling
        # For better fit, use independent scaling
        scale_x = max(0.3, min(1.5, scale_x))  # Limit scaling range
        scale_y = max(0.3, min(1.5, scale_y))
        
        # Scaled diagram coordinates
        diagram_left = int(base_diagram_left * scale_x)
        diagram_top = int(base_diagram_top * scale_y)
        diagram_right = int(base_diagram_right * scale_x)
        diagram_bottom = int(base_diagram_bottom * scale_y)
        axis_x = diagram_left
        axis_y = diagram_bottom
        
        # Calculate profile segment positions (scaled)
        pre_end_x = int((base_diagram_left + 100) * scale_x)
        ramp_up_end_x = int((base_diagram_left + 400) * scale_x)
        hold_end_x = int((base_diagram_left + 700) * scale_x)
        ramp_down_end_x = int((base_diagram_left + 900) * scale_x)
        level_1_y = int((base_diagram_top + 30) * scale_y)
        
        # Position inputs and their unit labels (scaled)
        # 1. Measurement Interval input - top left, next to label
        interval_x = int(150 * scale_x)
        interval_y = int(5 * scale_y)
        self.interval_input.move(interval_x, interval_y)
        self.interval_unit.move(interval_x + 52, interval_y)  # Right next to input
        
        # 2. tPre input - below pre-time segment
        pre_x = axis_x + (pre_end_x - axis_x) // 2 - 30
        pre_y = axis_y + int(15 * scale_y)
        self.pre_input.move(pre_x, pre_y)
        self.pre_unit.move(pre_x + 52, pre_y)  # Right next to input
        
        # 3. tHold input - above hold segment
        hold_x = ramp_up_end_x + (hold_end_x - ramp_up_end_x) // 2 - 30
        hold_y = level_1_y - int(30 * scale_y)
        self.hold_input.move(hold_x, hold_y)
        self.hold_unit.move(hold_x + 52, hold_y)  # Right next to input
        
        # 4. Inc. Rate input - positioned on the ramp-up slanted line (green circle position)
        # Calculate midpoint of the ramp-up segment
        # level_0_y is axis_y (bottom level), level_1_y is the top level
        level_0_y = axis_y
        inc_mid_x = (pre_end_x + ramp_up_end_x) // 2
        inc_mid_y = (level_0_y + level_1_y) // 2
        # Position input box at midpoint, slightly offset for readability
        inc_x = inc_mid_x - 25  # Center the input box
        inc_y = inc_mid_y - 10  # Slightly above the line for visibility
        self.inc_input.move(inc_x, inc_y)
        self.inc_unit.move(inc_x + 52, inc_y)  # Right next to input
        
        # 5. Dec. Rate input - positioned on the ramp-down slanted line (green circle position)
        # Calculate midpoint of the ramp-down segment
        dec_mid_x = (hold_end_x + ramp_down_end_x) // 2
        dec_mid_y = (level_1_y + level_0_y) // 2
        # Position input box at midpoint, slightly offset for readability
        dec_x = dec_mid_x - 25  # Center the input box
        dec_y = dec_mid_y - 10  # Slightly above the line for visibility
        self.dec_input.move(dec_x, dec_y)
        self.dec_unit.move(dec_x + 52, dec_y)  # Right next to input
        
        # 6. V-axis "0" input - left of vertical axis, at bottom (no unit)
        self.v0_input.move(axis_x - 35, axis_y - 10)
        
        # 7. V-axis "1" input - left of vertical axis, at top level (no unit)
        self.v1_input.move(axis_x - 35, level_1_y - 10)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Sharp edges like VB

        # Colors matching the image
        bg_color = QColor(240, 240, 240)  # Light grey background
        border_color = QColor(128, 128, 128)  # Grey border
        black = QColor(0, 0, 0)
        red = QColor(255, 0, 0)

        # Base diagram coordinates (reference size: 1000x200)
        base_width = 1000
        base_height = 200
        base_diagram_left = 50
        base_diagram_top = 50
        base_diagram_right = 950
        base_diagram_bottom = 160
        
        # Calculate scale factors
        widget_width = max(400, self.width())
        widget_height = max(150, self.height())
        
        scale_x = (widget_width - 20) / (base_width - 20)
        scale_y = (widget_height - 20) / (base_height - 20)
        
        # Limit scaling range
        scale_x = max(0.3, min(1.5, scale_x))
        scale_y = max(0.3, min(1.5, scale_y))
        
        # Scaled diagram coordinates
        diagram_left = int(base_diagram_left * scale_x)
        diagram_top = int(base_diagram_top * scale_y)
        diagram_right = int(base_diagram_right * scale_x)
        diagram_bottom = int(base_diagram_bottom * scale_y)
        axis_x = diagram_left
        axis_y = diagram_bottom
        level_1_y = int((base_diagram_top + 30) * scale_y)
        
        # Draw grey background with dotted border
        p.fillRect(
            QRect(diagram_left, diagram_top, diagram_right - diagram_left, diagram_bottom - diagram_top),
            bg_color
        )
        
        # Draw dotted border
        pen = QPen(border_color, 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        p.drawRect(QRect(diagram_left, diagram_top, diagram_right - diagram_left, diagram_bottom - diagram_top))

        # Draw "Measurement Interval" label (top left) - scaled
        font_size = max(7, int(9 * min(scale_x, scale_y)))
        font = QFont("MS Shell Dlg 2", font_size, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(black)
        label_rect = QRect(int(10 * scale_x), int(5 * scale_y), int(140 * scale_x), int(20 * scale_y))
        p.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                   "Measurement Interval")

        # Draw axes with arrows - scaled
        pen_width = max(1, int(2 * min(scale_x, scale_y)))
        pen = QPen(black, pen_width)
        p.setPen(pen)
        
        # Time axis (horizontal arrow pointing right)
        p.drawLine(axis_x, axis_y, diagram_right, axis_y)
        # Arrow head - scaled
        arrow_size = max(4, int(8 * min(scale_x, scale_y)))
        p.drawLine(diagram_right, axis_y, diagram_right - arrow_size, axis_y - arrow_size // 2)
        p.drawLine(diagram_right, axis_y, diagram_right - arrow_size, axis_y + arrow_size // 2)
        # "t" label - scaled
        p.drawText(QRect(diagram_right + int(5 * scale_x), axis_y - int(10 * scale_y), 
                        int(20 * scale_x), int(20 * scale_y)), Qt.AlignmentFlag.AlignLeft, "t")

        # Voltage axis (vertical arrow pointing up) - labeled 'V'
        p.drawLine(axis_x, axis_y, axis_x, diagram_top)
        # Arrow head - scaled
        p.drawLine(axis_x, diagram_top, axis_x - arrow_size // 2, diagram_top + arrow_size)
        p.drawLine(axis_x, diagram_top, axis_x + arrow_size // 2, diagram_top + arrow_size)
        # "V" label at top - scaled
        p.drawText(QRect(axis_x - int(15 * scale_x), diagram_top - int(20 * scale_y), 
                        int(20 * scale_x), int(20 * scale_y)), Qt.AlignmentFlag.AlignCenter, "V")

        # Small black square at origin (intersection of axes) - scaled
        p.setBrush(QBrush(black))
        p.setPen(QPen(black))
        square_size = max(2, int(4 * min(scale_x, scale_y)))
        p.drawRect(QRect(axis_x - square_size // 2, axis_y - square_size // 2, square_size, square_size))

        # Draw dashed horizontal line from "1" level
        dash_pen = QPen(black, 1, Qt.PenStyle.DashLine)
        p.setPen(dash_pen)
        p.drawLine(axis_x, level_1_y, diagram_right, level_1_y)

        # Calculate profile segment positions (scaled)
        level_0_y = axis_y
        pre_end_x = int((base_diagram_left + 100) * scale_x)
        ramp_up_end_x = int((base_diagram_left + 400) * scale_x)
        hold_end_x = int((base_diagram_left + 700) * scale_x)
        ramp_down_end_x = int((base_diagram_left + 900) * scale_x)
        
        # Draw red measurement profile line - scaled
        red_pen_width = max(1, int(2 * min(scale_x, scale_y)))
        red_pen = QPen(red, red_pen_width)
        p.setPen(red_pen)
        
        # Pre-time: flat at 0
        p.drawLine(axis_x, level_0_y, pre_end_x, level_0_y)
        
        # Ramp-up: from 0 to 1
        p.drawLine(pre_end_x, level_0_y, ramp_up_end_x, level_1_y)
        
        # Hold: flat at 1
        p.drawLine(ramp_up_end_x, level_1_y, hold_end_x, level_1_y)
        
        # Ramp-down: from 1 to 0
        p.drawLine(hold_end_x, level_1_y, ramp_down_end_x, level_0_y)
        
        # Final flat segment at 0
        p.drawLine(ramp_down_end_x, level_0_y, diagram_right, level_0_y)

        # Draw vertical dotted lines from profile turning points to top - scaled
        dash_pen = QPen(black, 1, Qt.PenStyle.DotLine)
        p.setPen(dash_pen)
        p.drawLine(pre_end_x, diagram_top, pre_end_x, level_0_y)
        p.drawLine(ramp_up_end_x, diagram_top, ramp_up_end_x, level_1_y)
        p.drawLine(hold_end_x, diagram_top, hold_end_x, level_1_y)
        p.drawLine(ramp_down_end_x, diagram_top, ramp_down_end_x, level_0_y)

        # Draw labels for segments - scaled
        small_font_size = max(6, int(8 * min(scale_x, scale_y)))
        small_font = QFont("MS Shell Dlg 2", small_font_size)
        p.setFont(small_font)
        p.setPen(QPen(black, 1))
        
        # "tPre" label below pre-time segment
        p.drawText(QRect(axis_x, axis_y + int(5 * scale_y), pre_end_x - axis_x, int(15 * scale_y)), 
                   Qt.AlignmentFlag.AlignCenter, "tPre")
        
        # "Inc. Rate" label above ramp-up
        p.drawText(QRect(pre_end_x, diagram_top - int(20 * scale_y), ramp_up_end_x - pre_end_x, int(15 * scale_y)), 
                   Qt.AlignmentFlag.AlignCenter, "Inc. Rate")
        
        # "tHold" label above hold segment
        p.drawText(QRect(ramp_up_end_x, diagram_top - int(20 * scale_y), hold_end_x - ramp_up_end_x, int(15 * scale_y)), 
                   Qt.AlignmentFlag.AlignCenter, "tHold")
        
        # "Dec. Rate" label above ramp-down
        p.drawText(QRect(hold_end_x, diagram_top - int(20 * scale_y), ramp_down_end_x - hold_end_x, int(15 * scale_y)), 
                   Qt.AlignmentFlag.AlignCenter, "Dec. Rate")
