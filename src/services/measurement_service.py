from sqlalchemy.orm import Session
from datetime import datetime
import hashlib
import os
import json

from src.models import Measurement, MeasurementType, Workbook, User
from src.auth import AuthManager
from src.utils import Config


class MeasurementService:
    """Service for measurement operations"""
    
    def __init__(self):
        self.auth_manager = AuthManager()
        self.config = Config()
    
    def create_measurement(self, db: Session, workbook_id: int, user: User,
                          measurement_type: MeasurementType, raw_data_path: str,
                          parsed_data: dict = None, instrument_settings: dict = None,
                          temperature_range: str = None, notes: str = None) -> Measurement:
        """Create a new measurement (immutable instrument data)"""
        # Verify workbook access
        if not self.auth_manager.can_access_workbook(user, workbook_id, db):
            raise PermissionError("Access denied to this workbook")
        
        # Verify workbook ownership for researchers
        workbook = db.query(Workbook).filter(Workbook.id == workbook_id).first()
        if user.is_researcher() and workbook.researcher_id != user.id:
            raise PermissionError("Only the workbook owner can add measurements")
        
        # Calculate hash of raw data file
        raw_data_hash = self._calculate_file_hash(raw_data_path)
        
        # Calculate statistics from parsed data
        stats = self._calculate_statistics(parsed_data) if parsed_data else {}
        
        measurement = Measurement(
            workbook_id=workbook_id,
            measurement_type=measurement_type,
            raw_data_path=raw_data_path,
            raw_data_hash=raw_data_hash,
            parsed_data=parsed_data,
            instrument_settings=instrument_settings,
            temperature_range=temperature_range,
            notes=notes,
            data_points_count=stats.get('count', 0),
            min_value=stats.get('min'),
            max_value=stats.get('max'),
            avg_value=stats.get('avg')
        )
        
        db.add(measurement)
        
        # Update workbook's last measurement time
        workbook.last_measurement_at = datetime.utcnow()
        
        db.commit()
        db.refresh(measurement)
        
        return measurement
    
    def get_measurements(self, db: Session, workbook_id: int, user: User,
                        measurement_type: MeasurementType = None) -> list[Measurement]:
        """Get measurements for a workbook"""
        if not self.auth_manager.can_access_workbook(user, workbook_id, db):
            raise PermissionError("Access denied to this workbook")
        
        query = db.query(Measurement).filter(Measurement.workbook_id == workbook_id)
        
        if measurement_type:
            query = query.filter(Measurement.measurement_type == measurement_type)
        
        return query.order_by(Measurement.measurement_date.desc()).all()
    
    def get_measurement(self, db: Session, measurement_id: int, user: User) -> Measurement:
        """Get a specific measurement"""
        measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
        
        if not measurement:
            raise ValueError("Measurement not found")
        
        if not self.auth_manager.can_access_workbook(user, measurement.workbook_id, db):
            raise PermissionError("Access denied to this measurement")
        
        return measurement
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return ""
    
    def _calculate_statistics(self, parsed_data: dict) -> dict:
        """Calculate basic statistics from parsed measurement data"""
        # This is a placeholder - actual implementation depends on data structure
        # Assuming parsed_data contains a 'values' array or similar
        stats = {'count': 0, 'min': None, 'max': None, 'avg': None}
        
        if isinstance(parsed_data, dict) and 'values' in parsed_data:
            values = parsed_data['values']
            if values and len(values) > 0:
                stats['count'] = len(values)
                stats['min'] = min(values)
                stats['max'] = max(values)
                stats['avg'] = sum(values) / len(values)
        
        return stats

