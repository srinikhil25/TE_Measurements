from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class MeasurementType(str, enum.Enum):
    SEEBECK = "seebeck"
    ELECTRICAL_CONDUCTIVITY = "electrical_conductivity"
    RESISTANCE_CONDUCTIVITY = "resistance_conductivity"


class MeasurementStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    workbook_id = Column(Integer, ForeignKey("workbooks.id"), nullable=False)
    researcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    measurement_type = Column(Enum(MeasurementType), nullable=False)
    measurement_params = Column(JSON, nullable=True)
    status = Column(Enum(MeasurementStatus), default=MeasurementStatus.RUNNING, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    data_file_path = Column(String, nullable=True)  # Path to CSV/JSON file
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workbook = relationship("Workbook", back_populates="measurements")
    researcher = relationship("User", back_populates="measurements")

