from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from src.database import Base


class AuditActionType(PyEnum):
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    
    # User Management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    
    # Lab Management
    LAB_CREATED = "lab_created"
    LAB_UPDATED = "lab_updated"
    LAB_DELETED = "lab_deleted"
    
    # Workbook Management
    WORKBOOK_CREATED = "workbook_created"
    WORKBOOK_UPDATED = "workbook_updated"
    WORKBOOK_DELETED = "workbook_deleted"
    
    # Measurement
    MEASUREMENT_CREATED = "measurement_created"
    MEASUREMENT_VIEWED = "measurement_viewed"
    
    # Instrument
    INSTRUMENT_CONNECTED = "instrument_connected"
    INSTRUMENT_DISCONNECTED = "instrument_disconnected"
    INSTRUMENT_MEASUREMENT_STARTED = "instrument_measurement_started"
    INSTRUMENT_MEASUREMENT_COMPLETED = "instrument_measurement_completed"
    
    # Comments
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    
    # Permissions
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    user = relationship("User", back_populates="audit_logs")
    
    # Action details
    action_type = Column(Enum(AuditActionType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Context
    entity_type = Column(String(50), nullable=True)  # e.g., "workbook", "measurement", "user"
    entity_id = Column(Integer, nullable=True)  # ID of the affected entity
    
    # Additional metadata
    additional_metadata = Column(JSON, nullable=True)  # Additional context data
    
    # IP address and user agent (for security)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action_type.value}, user_id={self.user_id})>"

