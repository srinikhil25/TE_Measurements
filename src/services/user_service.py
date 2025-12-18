from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models import User, UserRole, Lab
from src.auth import AuthManager


class UserService:
    """Service for user management operations (super admin only)"""
    
    def __init__(self):
        self.auth_manager = AuthManager()
    
    def create_user(self, db: Session, creator: User, username: str, email: str,
                   full_name: str, password: str, role: UserRole, lab_id: int = None) -> User:
        """Create a new user (super admin only)"""
        if not creator.is_super_admin():
            raise PermissionError("Only super admins can create users")
        
        # Validate username uniqueness
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")
        
        # Validate email uniqueness
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError(f"Email '{email}' is already registered")
        
        # Validate lab assignment
        if role in [UserRole.RESEARCHER, UserRole.LAB_ADMIN]:
            if not lab_id:
                raise ValueError("Lab is required for researchers and lab admins")
            
            lab = db.query(Lab).filter(Lab.id == lab_id).first()
            if not lab:
                raise ValueError("Invalid lab ID")
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            lab_id=lab_id if role != UserRole.SUPER_ADMIN else None,
            is_active=True
        )
        new_user.set_password(password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    def update_user(self, db: Session, user_id: int, updater: User, **kwargs) -> User:
        """Update user (super admin only)"""
        if not updater.is_super_admin():
            raise PermissionError("Only super admins can update users")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Allow updating certain fields
        allowed_fields = ['full_name', 'email', 'lab_id', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def delete_user(self, db: Session, user_id: int, deleter: User):
        """Soft delete user (super admin only)"""
        if not deleter.is_super_admin():
            raise PermissionError("Only super admins can delete users")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Prevent deleting yourself
        if user.id == deleter.id:
            raise ValueError("Cannot delete your own account")
        
        user.is_active = False
        db.commit()
    
    def reset_password(self, db: Session, user_id: int, new_password: str, admin: User):
        """Reset user password (super admin only)"""
        if not admin.is_super_admin():
            raise PermissionError("Only super admins can reset passwords")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        user.set_password(new_password)
        db.commit()

