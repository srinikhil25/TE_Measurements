from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Workbook association
    workbook_id = Column(Integer, ForeignKey("workbooks.id"), nullable=False)
    workbook = relationship("Workbook", back_populates="comments")
    
    # Author (lab admin or super admin)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="comments")
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Optional: Reference to specific measurement
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True)
    measurement = relationship("Measurement", foreign_keys=[measurement_id])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_edited = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Comment(id={self.id}, workbook_id={self.workbook_id}, author_id={self.author_id})>"

