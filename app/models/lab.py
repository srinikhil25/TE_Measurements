from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Lab(Base):
    """
    Laboratory / Lab entity.
    Each non‑super-admin user belongs to exactly one lab.
    """

    __tablename__ = "labs"

    lab_id = Column(Integer, primary_key=True, index=True)
    lab_name = Column(String, nullable=False, unique=True, index=True)
    lab_code = Column(String, nullable=False, unique=True, index=True)
    lab_description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="lab")
    workbooks = relationship("Workbook", back_populates="lab")
    measurements = relationship("Measurement", back_populates="lab")


