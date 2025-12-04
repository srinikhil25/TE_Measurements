from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.measurement import MeasurementType, MeasurementStatus


class MeasurementBase(BaseModel):
    measurement_type: MeasurementType
    measurement_params: Optional[Dict[str, Any]] = None


class MeasurementCreate(MeasurementBase):
    workbook_id: int


class MeasurementUpdate(BaseModel):
    status: Optional[MeasurementStatus] = None
    measurement_params: Optional[Dict[str, Any]] = None
    data_file_path: Optional[str] = None
    completed_at: Optional[datetime] = None


class Measurement(MeasurementBase):
    id: int
    workbook_id: int
    researcher_id: int
    status: MeasurementStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    data_file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

