from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class WorkbookBase(BaseModel):
    name: str
    description: Optional[str] = None
    material_type: Optional[str] = None
    sample_id_code: Optional[str] = None
    date_received: Optional[date] = None
    lab_id: int


class WorkbookCreate(WorkbookBase):
    pass


class WorkbookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    material_type: Optional[str] = None
    sample_id_code: Optional[str] = None
    date_received: Optional[date] = None
    is_active: Optional[bool] = None


class Workbook(WorkbookBase):
    id: int
    researcher_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

