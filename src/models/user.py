from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import bcrypt

from src.database import Base
from src.models.associations import user_lab_permissions


class UserRole(PyEnum):
    RESEARCHER = "researcher"
    LAB_ADMIN = "lab_admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RESEARCHER)
    preferred_language = Column(String(10), nullable=False, default="en")  # 'en' or 'ja'
    
    # Lab association (researchers belong to one primary lab)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)
    # Explicit foreign_keys avoids ambiguity with the association table
    lab = relationship("Lab", back_populates="members", foreign_keys=[lab_id])
    
    # Multi-lab permissions (for researchers with special access)
    additional_lab_permissions = relationship(
        "Lab",
        secondary="user_lab_permissions",
        back_populates="additional_members"
    )
    
    # Relationships
    workbooks = relationship("Workbook", back_populates="researcher", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    # Status
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def set_password(self, password: str):
        """Hash and set password"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def is_researcher(self) -> bool:
        return self.role == UserRole.RESEARCHER

    def is_lab_admin(self) -> bool:
        return self.role == UserRole.LAB_ADMIN

    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    def can_access_lab(self, lab_id: int) -> bool:
        """Check if user can access a specific lab"""
        if self.is_super_admin():
            return True
        if self.is_lab_admin():
            return self.lab_id == lab_id
        if self.is_researcher():
            return self.lab_id == lab_id or any(
                lab.id == lab_id for lab in self.additional_lab_permissions
            )
        return False

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"

