"""
IR Camera Widget for Optris 450 Series
Displays live thermal imaging feed with temperature statistics
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt6.QtGui import QImage, QPixmap, QPainter, QFont
import base64
import json
import logging
import os
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class IRCameraThread(QThread):
    """Background thread for IR camera capture"""
    
    frame_ready = pyqtSignal(bytes, float, float, float, list)  # frame, avg, min, max, temps_2d
    
    def __init__(self, parent=None, dll_path=None, config_path=None):
        super().__init__(parent)
        self.running = False
        self.mutex = QMutex()
        self.camera_manager = None
        self.dll_path = dll_path
        self.config_path = config_path
        
    def start_capture(self):
        """Start camera capture"""
        with QMutexLocker(self.mutex):
            if self.running:
                return
            self.running = True
        self.start()
    
    def stop_capture(self):
        """Stop camera capture"""
        with QMutexLocker(self.mutex):
            self.running = False
        self.wait(2000)  # Wait up to 2 seconds
    
    def run(self):
        """Main capture loop"""
        try:
            # Try to import pyOptris and cv2
            try:
                import pyOptris
                import cv2
            except ImportError as e:
                logger.error(f"Failed to import pyOptris or cv2: {e}")
                logger.error("Please install: pip install opencv-python")
                logger.error("For Optris camera support, install pyOptris SDK")
                self.frame_ready.emit(b"", 0.0, 0.0, 0.0, [])
                return
            
            # Initialize camera
            try:
                # Use provided paths or fallback to defaults
                dll_paths = []
                if self.dll_path:
                    dll_paths.append(self.dll_path)
                dll_paths.extend([
                    "C:/IrDirectSDK/sdk/x64/libirimager.dll",
                    "C:/lib/IrDirectSDK/sdk/x64/libirimager.dll",
                    "C:/Program Files/optris/libirimager.dll",
                    "libirimager.dll",  # System PATH
                ])
                
                dll_loaded = False
                loaded_dll_path = None
                for dll_path in dll_paths:
                    try:
                        if os.path.exists(dll_path):
                            pyOptris.load_DLL(dll_path)
                            dll_loaded = True
                            loaded_dll_path = dll_path
                            logger.info(f"Loaded Optris DLL from: {dll_path}")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to load DLL from {dll_path}: {e}")
                        continue
                
                if not dll_loaded:
                    raise Exception(f"Could not load Optris DLL. Tried: {dll_paths}")
                
                # Use provided config path or fallback to defaults
                config_paths = []
                if self.config_path:
                    config_paths.append(self.config_path)
                config_paths.extend([
                    'C:/IrDirectSDK/generic.xml',
                    'C:/lib/IrDirectSDK/generic.xml',
                    'C:/Program Files/optris/generic.xml',
                    'generic.xml',
                ])
                
                config_loaded = False
                loaded_config_path = None
                for config_path in config_paths:
                    try:
                        if os.path.exists(config_path):
                            pyOptris.usb_init(config_path)
                            config_loaded = True
                            loaded_config_path = config_path
                            logger.info(f"Loaded Optris config from: {config_path}")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to load config from {config_path}: {e}")
                        continue
                
                if not config_loaded:
                    raise Exception(f"Could not load Optris config. Tried: {config_paths}")
                
                pyOptris.set_palette(pyOptris.ColouringPalette.IRON)
                w, h = pyOptris.get_palette_image_size()
                
                last_min = None
                last_max = None
                
                while self.running:
                    try:
                        thermal = pyOptris.get_thermal_image(w, h)
                        temps = ((thermal.astype(np.float32) - 1000.0) / 10.0)
                        avg = float(np.mean(temps))
                        tmin = float(np.min(temps))
                        tmax = float(np.max(temps))
                        temps_2d = np.round(temps, 1).tolist()
                        
                        # Enhanced image processing for maximum clarity
                        # 1. Adaptive temperature range smoothing (reduced alpha for faster response)
                        alpha = 0.15  # Faster adaptation for better clarity
                        if last_min is None:
                            last_min = tmin
                            last_max = tmax
                        else:
                            last_min = alpha * tmin + (1 - alpha) * last_min
                            last_max = alpha * tmax + (1 - alpha) * last_max
                        
                        # 2. Enhanced dynamic normalization with better contrast
                        temp_range = last_max - last_min
                        if temp_range < 1e-6:
                            temp_range = 1.0  # Avoid division by zero
                        
                        # Normalize with slight expansion for better contrast
                        norm = np.clip(
                            ((temps - last_min) / temp_range) * 255.0,
                            0, 255
                        ).astype(np.uint8)
                        
                        # 3. Enhanced CLAHE for better local contrast
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                        norm = clahe.apply(norm)
                        
                        # 4. Apply high-quality colormap (INFERNO for best thermal visualization)
                        frame = cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO)
                        
                        # 5. Advanced denoising (reduced for better detail preservation)
                        frame = cv2.fastNlMeansDenoisingColored(
                            frame, None, 
                            h=8,  # Reduced from 10 for less smoothing
                            hColor=8,  # Reduced from 10
                            templateWindowSize=7,
                            searchWindowSize=21
                        )
                        
                        # 6. High-quality upscaling with Lanczos interpolation
                        upscale_factor = 2.0  # Increased from 1.5 for better clarity
                        new_width = int(frame.shape[1] * upscale_factor)
                        new_height = int(frame.shape[0] * upscale_factor)
                        frame = cv2.resize(
                            frame,
                            (new_width, new_height),
                            interpolation=cv2.INTER_LANCZOS4  # Best quality interpolation
                        )
                        
                        # 7. Enhanced sharpening for maximum clarity
                        # Unsharp masking for better edge definition
                        gaussian = cv2.GaussianBlur(frame, (0, 0), 2.0)
                        frame = cv2.addWeighted(frame, 1.5, gaussian, -0.5, 0)
                        
                        # Additional sharpening kernel
                        kernel = np.array([
                            [0, -0.5, 0],
                            [-0.5, 3, -0.5],
                            [0, -0.5, 0]
                        ])
                        frame = cv2.filter2D(frame, -1, kernel)
                        
                        # 8. Gamma correction for better visibility
                        gamma = 0.9  # Slight brightening
                        inv_gamma = 1.0 / gamma
                        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                                         for i in np.arange(0, 256)]).astype("uint8")
                        frame = cv2.LUT(frame, table)
                        
                        # 9. High-quality JPEG encoding
                        _, jpeg = cv2.imencode('.jpg', frame, [
                            int(cv2.IMWRITE_JPEG_QUALITY), 98  # Higher quality
                        ])
                        
                        self.frame_ready.emit(jpeg.tobytes(), avg, tmin, tmax, temps_2d)
                        self.msleep(33)  # ~30 FPS for smoother streaming
                        
                    except Exception as e:
                        logger.error(f"Error capturing frame: {e}")
                        self.msleep(100)
                        
            except Exception as e:
                logger.error(f"Failed to initialize IR camera: {e}")
                self.frame_ready.emit(b"", 0.0, 0.0, 0.0, [])
                
        except Exception as e:
            logger.error(f"IR camera thread error: {e}")
        finally:
            try:
                if self.camera_manager:
                    pyOptris.terminate()
            except:
                pass


class IRCameraWidget(QWidget):
    """
    IR Camera live feed widget with temperature display
    Shows thermal image with hover temperature tooltip
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_thread = None
        self.current_temps = None
        self.hover_temp = None
        self.hover_pos = None
        
        # Get paths from config
        from src.utils import Config
        self.config = Config()
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("IR Camera Live Stream / IRカメラライブストリーム")
        title_font = title.font()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)
        
        header.addStretch()
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect Camera")
        self.connect_btn.setFixedHeight(24)
        self.connect_btn.setStyleSheet("""
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
        self.connect_btn.clicked.connect(self._toggle_camera)
        header.addWidget(self.connect_btn)
        
        layout.addLayout(header)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fafafa;
            }
        """)
        self.image_label.setMinimumHeight(300)
        self.image_label.setText("No IR stream available\nClick 'Connect Camera' to start")
        self.image_label.setWordWrap(True)
        self.image_label.mouseMoveEvent = self._on_mouse_move
        self.image_label.leaveEvent = self._on_mouse_leave
        layout.addWidget(self.image_label)
        
        # Temperature stats
        self.stats_label = QLabel("Avg: --°C  |  Min: --°C  |  Max: --°C")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("color: #444; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.stats_label)
        
        # Tooltip label (overlay)
        self.tooltip_label = QLabel(self)
        self.tooltip_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.75);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.tooltip_label.hide()
        self.tooltip_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    
    def _toggle_camera(self):
        """Toggle camera connection"""
        if self.camera_thread and self.camera_thread.isRunning():
            self._disconnect_camera()
        else:
            self._connect_camera()
    
    def _connect_camera(self):
        """Start camera capture"""
        if self.camera_thread and self.camera_thread.isRunning():
            return
        
        # Pass configured paths to camera thread
        self.camera_thread = IRCameraThread(
            self,
            dll_path=self.config.ir_camera_dll_path,
            config_path=self.config.ir_camera_config_path
        )
        self.camera_thread.frame_ready.connect(self._on_frame_ready)
        self.camera_thread.start_capture()
        
        self.connect_btn.setText("Disconnect Camera")
        self.image_label.setText("Connecting to IR camera...")
    
    def _disconnect_camera(self):
        """Stop camera capture"""
        if self.camera_thread:
            self.camera_thread.stop_capture()
            self.camera_thread = None
        
        self.connect_btn.setText("Connect Camera")
        self.image_label.setText("No IR stream available\nClick 'Connect Camera' to start")
        self.stats_label.setText("Avg: --°C  |  Min: --°C  |  Max: --°C")
        self.current_temps = None
    
    def _on_frame_ready(self, frame_data: bytes, avg: float, tmin: float, tmax: float, temps_2d: list):
        """Update display with new frame"""
        if not frame_data:
            return
        
        try:
            # Convert JPEG bytes to QPixmap
            image = QImage.fromData(frame_data, "JPEG")
            if image.isNull():
                return
            
            pixmap = QPixmap.fromImage(image)
            # Use best quality scaling for maximum clarity
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
            # Update stats
            self.stats_label.setText(
                f"Avg: {avg:.1f}°C  |  Min: {tmin:.1f}°C  |  Max: {tmax:.1f}°C"
            )
            
            # Store temperature array for hover tooltip
            self.current_temps = temps_2d
            
        except Exception as e:
            logger.error(f"Error displaying frame: {e}")
    
    def _on_mouse_move(self, event):
        """Handle mouse move for temperature tooltip"""
        if not self.current_temps or not self.image_label.pixmap():
            return
        
        pixmap = self.image_label.pixmap()
        label_rect = self.image_label.rect()
        pixmap_rect = pixmap.rect()
        
        # Calculate scaled pixmap position within label
        scaled_width = pixmap_rect.width()
        scaled_height = pixmap_rect.height()
        if pixmap_rect.width() > 0 and pixmap_rect.height() > 0:
            scale_x = scaled_width / pixmap_rect.width()
            scale_y = scaled_height / pixmap_rect.height()
        else:
            return
        
        # Get mouse position relative to pixmap
        x = event.pos().x() - (label_rect.width() - scaled_width) / 2
        y = event.pos().y() - (label_rect.height() - scaled_height) / 2
        
        if x < 0 or y < 0 or x >= scaled_width or y >= scaled_height:
            self._hide_tooltip()
            return
        
        # Map to temperature array coordinates
        arr_height = len(self.current_temps)
        arr_width = len(self.current_temps[0]) if arr_height > 0 else 0
        
        if arr_width > 0 and arr_height > 0:
            arr_x = int(x / scale_x * arr_width / pixmap_rect.width())
            arr_y = int(y / scale_y * arr_height / pixmap_rect.height())
            
            if 0 <= arr_y < arr_height and 0 <= arr_x < arr_width:
                temp = self.current_temps[arr_y][arr_x]
                self._show_tooltip(event.pos(), f"{temp:.1f}°C")
                return
        
        self._hide_tooltip()
    
    def _on_mouse_leave(self, event):
        """Hide tooltip when mouse leaves"""
        self._hide_tooltip()
    
    def _show_tooltip(self, pos, text):
        """Show temperature tooltip"""
        self.tooltip_label.setText(text)
        self.tooltip_label.adjustSize()
        
        # Position tooltip above cursor
        tooltip_x = pos.x() - self.tooltip_label.width() // 2
        tooltip_y = pos.y() - self.tooltip_label.height() - 10
        
        # Keep within widget bounds
        tooltip_x = max(0, min(tooltip_x, self.width() - self.tooltip_label.width()))
        tooltip_y = max(0, min(tooltip_y, self.height() - self.tooltip_label.height()))
        
        self.tooltip_label.move(tooltip_x, tooltip_y)
        self.tooltip_label.show()
    
    def _hide_tooltip(self):
        """Hide temperature tooltip"""
        self.tooltip_label.hide()
    
    def closeEvent(self, event):
        """Clean up on close"""
        self._disconnect_camera()
        super().closeEvent(event)

