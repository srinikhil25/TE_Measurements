from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base
from src.models.associations import user_lab_permissions


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Lab admin (can be multiple, but typically one primary)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin = relationship("User", foreign_keys=[admin_id], backref="administered_labs")
    
    # Relationships
    members = relationship("User", foreign_keys="User.lab_id", back_populates="lab")
    additional_members = relationship(
        "User",
        secondary="user_lab_permissions",
        back_populates="additional_lab_permissions"
    )
    workbooks = relationship("Workbook", back_populates="lab", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Lab(id={self.id}, name={self.name})>"

