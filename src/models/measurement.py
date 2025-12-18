from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from src.database import Base


class MeasurementType(PyEnum):
    SEEBECK = "seebeck"
    RESISTIVITY = "resistivity"
    THERMAL_CONDUCTIVITY = "thermal_conductivity"


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    
    # Workbook association
    workbook_id = Column(Integer, ForeignKey("workbooks.id"), nullable=False)
    workbook = relationship("Workbook", back_populates="measurements")
    
    # Measurement type (determines which "page" it belongs to)
    measurement_type = Column(Enum(MeasurementType), nullable=False, index=True)
    
    # Raw data storage
    raw_data_path = Column(String(1000), nullable=False)  # Path to raw file on external drive
    raw_data_hash = Column(String(64), nullable=True)  # SHA256 hash for integrity verification
    
    # Parsed data (stored as JSON for flexibility)
    parsed_data = Column(JSON, nullable=True)  # Structured measurement data
    
    # Metadata
    measurement_date = Column(DateTime(timezone=True), server_default=func.now())
    instrument_settings = Column(JSON, nullable=True)  # Instrument configuration used
    temperature_range = Column(String(100), nullable=True)  # e.g., "300-800K"
    notes = Column(Text, nullable=True)
    
    # Data integrity (immutable)
    is_immutable = Column(Boolean, default=True)  # Instrument data cannot be edited
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Statistics (pre-calculated for performance)
    data_points_count = Column(Integer, default=0)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    avg_value = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Measurement(id={self.id}, type={self.measurement_type.value}, workbook_id={self.workbook_id})>"

