from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Workbook(Base):
    __tablename__ = "workbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    material_type = Column(String, nullable=True)
    sample_id_code = Column(String, nullable=True)
    date_received = Column(Date, nullable=True)
    researcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    researcher = relationship("User", back_populates="workbooks")
    measurements = relationship("Measurement", back_populates="workbook", cascade="all, delete-orphan")

