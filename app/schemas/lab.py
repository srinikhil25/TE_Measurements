from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LabBase(BaseModel):
    lab_name: str
    lab_code: str
    lab_description: Optional[str] = None


class LabCreate(LabBase):
    pass


class LabUpdate(BaseModel):
    lab_name: Optional[str] = None
    lab_code: Optional[str] = None
    lab_description: Optional[str] = None


class Lab(LabBase):
    lab_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


