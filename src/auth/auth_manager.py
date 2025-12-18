from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models import User, UserRole, AuditLog, AuditActionType
from src.database import get_db
from configparser import ConfigParser
import os


class AuthManager:
    """Handles authentication and authorization"""
    
    def __init__(self):
        self.config = ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'config.ini')
        self.config.read(config_path)
        self.max_login_attempts = self.config.getint('security', 'max_login_attempts', fallback=5)
        self.lockout_duration = timedelta(
            minutes=self.config.getint('security', 'lockout_duration_minutes', fallback=15)
        )
    
    def authenticate(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> tuple[User | None, str]:
        """
        Authenticate user with username and password.
        Returns (User object or None, error message)
        """
        db = next(get_db())
        try:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                self._log_audit(None, AuditActionType.LOGIN_FAILED, f"Failed login attempt for username: {username}", ip_address, user_agent)
                return None, "Invalid username or password"
            
            if not user.is_active:
                return None, "Account is deactivated"
            
            if user.is_locked:
                # Check if lockout period has expired
                # For simplicity, we'll unlock after lockout_duration
                # In production, you might want to track lockout time
                return None, "Account is locked. Please contact administrator."
            
            if not user.check_password(password):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= self.max_login_attempts:
                    user.is_locked = True
                    self._log_audit(user.id, AuditActionType.USER_LOCKED, "Account locked due to failed login attempts", ip_address, user_agent)
                db.commit()
                
                self._log_audit(user.id, AuditActionType.LOGIN_FAILED, "Invalid password", ip_address, user_agent)
                return None, "Invalid username or password"
            
            # Successful login
            user.failed_login_attempts = 0
            user.is_locked = False
            user.last_login = datetime.utcnow()
            db.commit()
            
            self._log_audit(user.id, AuditActionType.LOGIN, "User logged in successfully", ip_address, user_agent)
            return user, None
            
        except Exception as e:
            db.rollback()
            return None, f"Authentication error: {str(e)}"
        finally:
            db.close()
    
    def can_access_workbook(self, user: User, workbook_id: int, db: Session) -> bool:
        """Check if user can access a specific workbook"""
        from src.models import Workbook
        
        workbook = db.query(Workbook).filter(Workbook.id == workbook_id).first()
        if not workbook:
            return False
        
        # Super admin can access everything
        if user.is_super_admin():
            return True
        
        # Lab admin can access workbooks from their lab
        if user.is_lab_admin():
            return workbook.lab_id == user.lab_id
        
        # Researcher can only access their own workbooks
        if user.is_researcher():
            return workbook.researcher_id == user.id
        
        return False
    
    def can_edit_workbook(self, user: User, workbook_id: int, db: Session) -> bool:
        """Check if user can edit a workbook (only researcher who owns it)"""
        from src.models import Workbook
        
        if not user.is_researcher():
            return False
        
        workbook = db.query(Workbook).filter(Workbook.id == workbook_id).first()
        if not workbook:
            return False
        
        return workbook.researcher_id == user.id
    
    def can_view_lab_data(self, user: User, lab_id: int) -> bool:
        """Check if user can view data from a specific lab"""
        return user.can_access_lab(lab_id)
    
    def can_comment(self, user: User) -> bool:
        """Check if user can comment (lab admin or super admin)"""
        return user.is_lab_admin() or user.is_super_admin()
    
    def can_manage_users(self, user: User) -> bool:
        """Check if user can manage users (super admin only)"""
        return user.is_super_admin()
    
    def can_manage_labs(self, user: User) -> bool:
        """Check if user can manage labs (super admin only)"""
        return user.is_super_admin()
    
    def _log_audit(self, user_id: int | None, action: AuditActionType, description: str, ip_address: str = None, user_agent: str = None):
        """Log an audit event"""
        db = next(get_db())
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action_type=action,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to log audit: {e}")
        finally:
            db.close()

