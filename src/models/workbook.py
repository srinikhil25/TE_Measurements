from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class Workbook(Base):
    __tablename__ = "workbooks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sample_name = Column(String(255), nullable=True)
    sample_id = Column(String(100), nullable=True)
    
    # Ownership
    researcher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    researcher = relationship("User", back_populates="workbooks")
    
    # Lab association (for access control)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False)
    lab = relationship("Lab", back_populates="workbooks")
    
    # Relationships
    measurements = relationship("Measurement", back_populates="workbook", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="workbook", cascade="all, delete-orphan")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_measurement_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Workbook(id={self.id}, title={self.title}, researcher_id={self.researcher_id})>"

