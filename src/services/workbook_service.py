from sqlalchemy.orm import Session
from datetime import datetime

from src.models import Workbook, User
from src.auth import AuthManager


class WorkbookService:
    """Service for workbook operations"""
    
    def __init__(self):
        self.auth_manager = AuthManager()
    
    def create_workbook(self, db: Session, user: User, title: str, sample_name: str = None, 
                       sample_id: str = None, description: str = None) -> Workbook:
        """Create a new workbook for a researcher"""
        if not user.is_researcher():
            raise ValueError("Only researchers can create workbooks")
        
        workbook = Workbook(
            title=title,
            sample_name=sample_name,
            sample_id=sample_id,
            description=description,
            researcher_id=user.id,
            lab_id=user.lab_id
        )
        
        db.add(workbook)
        db.commit()
        db.refresh(workbook)
        
        return workbook
    
    def get_workbook(self, db: Session, workbook_id: int, user: User) -> Workbook:
        """Get a workbook with access control"""
        workbook = db.query(Workbook).filter(Workbook.id == workbook_id).first()
        
        if not workbook:
            raise ValueError("Workbook not found")
        
        if not self.auth_manager.can_access_workbook(user, workbook_id, db):
            raise PermissionError("Access denied to this workbook")
        
        return workbook
    
    def get_user_workbooks(self, db: Session, user: User) -> list[Workbook]:
        """Get all workbooks for a user"""
        if user.is_researcher():
            return db.query(Workbook).filter(
                Workbook.researcher_id == user.id,
                Workbook.is_active == True
            ).order_by(Workbook.created_at.desc()).all()
        elif user.is_lab_admin():
            return db.query(Workbook).filter(
                Workbook.lab_id == user.lab_id,
                Workbook.is_active == True
            ).order_by(Workbook.created_at.desc()).all()
        elif user.is_super_admin():
            return db.query(Workbook).filter(
                Workbook.is_active == True
            ).order_by(Workbook.created_at.desc()).all()
        
        return []
    
    def update_workbook(self, db: Session, workbook_id: int, user: User, **kwargs) -> Workbook:
        """Update workbook (only metadata, not measurements)"""
        workbook = self.get_workbook(db, workbook_id, user)
        
        if not self.auth_manager.can_edit_workbook(user, workbook_id, db):
            raise PermissionError("Only the workbook owner can edit it")
        
        # Only allow updating certain fields
        allowed_fields = ['title', 'description', 'sample_name', 'sample_id']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(workbook, field, value)
        
        workbook.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workbook)
        
        return workbook
    
    def delete_workbook(self, db: Session, workbook_id: int, user: User):
        """Soft delete a workbook"""
        workbook = self.get_workbook(db, workbook_id, user)
        
        if not self.auth_manager.can_edit_workbook(user, workbook_id, db):
            raise PermissionError("Only the workbook owner can delete it")
        
        workbook.is_active = False
        db.commit()

