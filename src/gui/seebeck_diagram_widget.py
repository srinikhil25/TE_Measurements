from PyQt6.QtWidgets import (
    QWidget,
    QLineEdit,
    QLabel,
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QFont, QColor, QBrush


class YellowInputBox(QLineEdit):
    """
    Custom input box styled like VB TextBox with yellow background.
    Behaves like a native Windows control but with yellow background.
    """
    def __init__(self, parent=None, suffix=""):
        super().__init__(parent)
        self.suffix = suffix
        self.setStyleSheet("""
            QLineEdit {
                background-color: #ffffcc;
                border: 1px solid #000000;
                border-radius: 0px;
                padding: 2px 4px;
                color: #000000;
                font-weight: bold;
                selection-background-color: #316ac5;
                selection-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #000000;
            }
        """)
        # Width adjusted to show suffix
        self.setFixedSize(85 if suffix else 70, 22)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw suffix after text (like VB TextBox with label)
        if self.suffix:
            p = QPainter(self)
            p.setPen(QColor(0, 0, 0))
            font = self.font()
            font.setBold(True)
            p.setFont(font)
            text_rect = self.rect()
            text = self.text() or ""
            if text:
                text_width = p.fontMetrics().horizontalAdvance(text)
            else:
                text_width = 0
            suffix_x = text_rect.left() + text_width + 4
            p.drawText(QRect(suffix_x, text_rect.top(), text_rect.width() - suffix_x, text_rect.height()),
                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                      self.suffix)


class SeebeckDiagramWidget(QWidget):
    """
    VB-style Seebeck phase diagram with native Windows feel.
    
    Uses:
    - Native Windows styling (no Fusion theme)
    - Custom yellow input boxes (like VB TextBox)
    - Native Windows colors and fonts
    - Classic Windows control appearance
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setMinimumWidth(1000)
        
        # Use native Windows font
        font = QFont("MS Shell Dlg 2", 9)  # Classic Windows dialog font
        self.setFont(font)

        # Create yellow input boxes (like VB TextBox controls)
        # Format matching OG: "2 s", "1-s", "600 s", "1 mA/s", "1 mA/s"
        self.interval_input = YellowInputBox(self, suffix=" s")
        self.interval_input.setText("2")
        self.interval_input.setValidator(self._create_int_validator(1, 3600))

        self.pre_input = YellowInputBox(self, suffix="-s")  # OG format: "1-s"
        self.pre_input.setText("1")
        self.pre_input.setValidator(self._create_int_validator(0, 3600))

        self.hold_input = YellowInputBox(self, suffix=" s")
        self.hold_input.setText("600")
        self.hold_input.setValidator(self._create_int_validator(0, 7200))

        self.inc_input = YellowInputBox(self, suffix=" mA/s")
        self.inc_input.setText("1")  # OG format: "1 mA/s" (no decimals)
        self.inc_input.setValidator(self._create_int_validator(1, 1000))  # Integer for display

        self.dec_input = YellowInputBox(self, suffix=" mA/s")
        self.dec_input.setText("1")  # OG format: "1 mA/s" (no decimals)
        self.dec_input.setValidator(self._create_int_validator(1, 1000))  # Integer for display

    def _create_int_validator(self, min_val, max_val):
        from PyQt6.QtGui import QIntValidator
        return QIntValidator(min_val, max_val, self)

    def _create_double_validator(self, min_val, max_val):
        from PyQt6.QtGui import QDoubleValidator
        validator = QDoubleValidator(min_val, max_val, 3, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        return validator

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

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._layout_controls()

    def _layout_controls(self) -> None:
        """Position input boxes at exact locations matching VB form."""
        # Fixed positions relative to diagram area
        # "Measurement Interval" box at top
        self.interval_input.move(150, 5)
        
        # Diagram area geometry (fixed layout)
        diagram_top = 50
        diagram_bottom = 160
        left = 50
        
        # tPre box below first flat segment
        self.pre_input.move(120, diagram_bottom + 15)
        
        # tHold box above hold segment
        self.hold_input.move(550, diagram_top - 30)
        
        # Inc. Rate box above ramp-up
        self.inc_input.move(300, diagram_top - 5)
        
        # Dec. Rate box above ramp-down
        self.dec_input.move(750, diagram_top - 5)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Sharp edges like VB

        # Use native Windows colors
        bg_color = QColor(240, 240, 240)  # Light grey background
        border_color = QColor(128, 128, 128)  # Grey border
        black = QColor(0, 0, 0)
        red = QColor(255, 0, 0)
        yellow = QColor(255, 255, 204)

        # Grey background with dotted border (diagram area) - like VB Frame
        diagram_left = 50
        diagram_top = 50
        diagram_right = 950
        diagram_bottom = 160
        
        # Draw grey background
        p.fillRect(
            QRect(diagram_left, diagram_top, diagram_right - diagram_left, diagram_bottom - diagram_top),
            bg_color
        )
        
        # Draw dotted border (VB Frame style)
        pen = QPen(border_color, 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        p.drawRect(QRect(diagram_left, diagram_top, diagram_right - diagram_left, diagram_bottom - diagram_top))

        # Draw "Measurement Interval" label (VB Label style)
        font = QFont("MS Shell Dlg 2", 9, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(black)
        p.drawText(QRect(10, 5, 140, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                   "Measurement Interval")

        # Draw axes with arrows (VB Line controls style)
        pen = QPen(black, 2)
        p.setPen(pen)
        
        # Time axis (horizontal arrow pointing right)
        axis_y = diagram_bottom
        p.drawLine(diagram_left, axis_y, diagram_right, axis_y)
        # Arrow head
        arrow_size = 8
        p.drawLine(diagram_right, axis_y, diagram_right - arrow_size, axis_y - arrow_size // 2)
        p.drawLine(diagram_right, axis_y, diagram_right - arrow_size, axis_y + arrow_size // 2)
        # "t" label
        p.drawText(QRect(diagram_right + 5, axis_y - 10, 20, 20), Qt.AlignmentFlag.AlignLeft, "t")

        # Current axis (vertical arrow pointing up)
        axis_x = diagram_left
        p.drawLine(axis_x, diagram_bottom, axis_x, diagram_top)
        # Arrow head
        p.drawLine(axis_x, diagram_top, axis_x - arrow_size // 2, diagram_top + arrow_size)
        p.drawLine(axis_x, diagram_top, axis_x + arrow_size // 2, diagram_top + arrow_size)

        # Draw yellow boxes for "0" and "1" on vertical axis (VB Label with yellow background)
        box_width = 25
        box_height = 20
        yellow_brush = QBrush(yellow)
        black_pen = QPen(black, 1)
        p.setBrush(yellow_brush)
        p.setPen(black_pen)
        
        # "0" box at bottom
        box0_rect = QRect(axis_x - box_width - 5, axis_y - box_height // 2, box_width, box_height)
        p.drawRect(box0_rect)
        p.setPen(black)
        p.drawText(box0_rect, Qt.AlignmentFlag.AlignCenter, "0")
        
        # "1" box at top
        level_1_y = diagram_top + 30  # Position of "1" level
        box1_rect = QRect(axis_x - box_width - 5, level_1_y - box_height // 2, box_width, box_height)
        p.setBrush(yellow_brush)
        p.setPen(black_pen)
        p.drawRect(box1_rect)
        p.setPen(black)
        p.drawText(box1_rect, Qt.AlignmentFlag.AlignCenter, "1")
        
        # Small black square at top-left of vertical axis
        p.setBrush(QBrush(black))
        p.setPen(QPen(black))
        square_size = 4
        p.drawRect(QRect(axis_x - square_size // 2, diagram_top - 5, square_size, square_size))

        # Draw red measurement profile line (VB Shape control style)
        red_pen = QPen(red, 2)
        p.setPen(red_pen)
        
        # Calculate profile points (matching screenshot proportions)
        level_0_y = axis_y
        level_1_y = diagram_top + 30
        
        # Pre-time: flat at 0
        pre_end_x = diagram_left + 100
        p.drawLine(axis_x, level_0_y, pre_end_x, level_0_y)
        
        # Ramp-up: from 0 to 1
        ramp_up_end_x = diagram_left + 400
        p.drawLine(pre_end_x, level_0_y, ramp_up_end_x, level_1_y)
        
        # Hold: flat at 1
        hold_end_x = diagram_left + 700
        p.drawLine(ramp_up_end_x, level_1_y, hold_end_x, level_1_y)
        
        # Ramp-down: from 1 to 0
        ramp_down_end_x = diagram_left + 900
        p.drawLine(hold_end_x, level_1_y, ramp_down_end_x, level_0_y)
        
        # Final flat segment at 0
        p.drawLine(ramp_down_end_x, level_0_y, diagram_right, level_0_y)

        # Draw dashed horizontal line from "1" level to start of ramp-up
        dash_pen = QPen(black, 1, Qt.PenStyle.DashLine)
        p.setPen(dash_pen)
        p.drawLine(axis_x + box_width, level_1_y, pre_end_x, level_1_y)

        # Draw double-headed arrows and labels (VB Line + Label controls)
        small_font = QFont("MS Shell Dlg 2", 8)
        p.setFont(small_font)
        p.setPen(QPen(black, 1))
        
        # tPre double-headed arrow below first flat segment
        arrow_y = level_0_y + 10
        arrow_start_x = axis_x
        arrow_end_x = pre_end_x
        arrow_mid_x = (arrow_start_x + arrow_end_x) // 2
        # Horizontal line
        p.drawLine(arrow_start_x, arrow_y, arrow_end_x, arrow_y)
        # Left arrow head
        p.drawLine(arrow_start_x, arrow_y, arrow_start_x + 5, arrow_y - 3)
        p.drawLine(arrow_start_x, arrow_y, arrow_start_x + 5, arrow_y + 3)
        # Right arrow head
        p.drawLine(arrow_end_x, arrow_y, arrow_end_x - 5, arrow_y - 3)
        p.drawLine(arrow_end_x, arrow_y, arrow_end_x - 5, arrow_y + 3)
        # "tPre" label
        p.drawText(QRect(arrow_mid_x - 20, arrow_y - 15, 40, 12), Qt.AlignmentFlag.AlignCenter, "tPre")
        
        # tHold double-headed arrow above hold segment
        arrow_y = level_1_y - 10
        arrow_start_x = ramp_up_end_x
        arrow_end_x = hold_end_x
        arrow_mid_x = (arrow_start_x + arrow_end_x) // 2
        # Horizontal line
        p.drawLine(arrow_start_x, arrow_y, arrow_end_x, arrow_y)
        # Left arrow head
        p.drawLine(arrow_start_x, arrow_y, arrow_start_x + 5, arrow_y - 3)
        p.drawLine(arrow_start_x, arrow_y, arrow_start_x + 5, arrow_y + 3)
        # Right arrow head
        p.drawLine(arrow_end_x, arrow_y, arrow_end_x - 5, arrow_y - 3)
        p.drawLine(arrow_end_x, arrow_y, arrow_end_x - 5, arrow_y + 3)
        # "tHold" label
        p.drawText(QRect(arrow_mid_x - 20, arrow_y - 15, 40, 12), Qt.AlignmentFlag.AlignCenter, "tHold")

        # Draw "Inc. Rate" and "Dec. Rate" labels (VB Label controls)
        p.drawText(QRect(pre_end_x, diagram_top - 25, ramp_up_end_x - pre_end_x, 15), 
                   Qt.AlignmentFlag.AlignCenter, "Inc. Rate")
        p.drawText(QRect(hold_end_x, diagram_top - 25, ramp_down_end_x - hold_end_x, 15), 
                   Qt.AlignmentFlag.AlignCenter, "Dec. Rate")
