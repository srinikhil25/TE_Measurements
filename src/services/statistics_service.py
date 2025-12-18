from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from src.models import User, Workbook, Measurement, MeasurementType, AuditLog, AuditActionType, UserRole


class StatisticsService:
    """Service for generating statistics and reports"""
    
    def get_researcher_statistics(self, db: Session, researcher_id: int, 
                                  start_date: datetime = None, end_date: datetime = None) -> dict:
        """Get statistics for a specific researcher"""
        query = db.query(Workbook).filter(Workbook.researcher_id == researcher_id)
        
        if start_date:
            query = query.filter(Workbook.created_at >= start_date)
        if end_date:
            query = query.filter(Workbook.created_at <= end_date)
        
        workbooks = query.all()
        
        # Count measurements by type
        measurement_counts = {}
        for mtype in MeasurementType:
            count = db.query(Measurement).join(Workbook).filter(
                Workbook.researcher_id == researcher_id,
                Measurement.measurement_type == mtype
            ).count()
            measurement_counts[mtype.value] = count
        
        # Instrument usage count
        usage_count = db.query(AuditLog).filter(
            AuditLog.user_id == researcher_id,
            AuditLog.action_type == AuditActionType.INSTRUMENT_MEASUREMENT_COMPLETED
        ).count()
        
        return {
            'total_workbooks': len(workbooks),
            'total_measurements': sum(measurement_counts.values()),
            'measurement_counts': measurement_counts,
            'instrument_usage_count': usage_count,
            'samples_measured': len(set(wb.sample_name for wb in workbooks if wb.sample_name))
        }
    
    def get_lab_statistics(self, db: Session, lab_id: int,
                          start_date: datetime = None, end_date: datetime = None) -> dict:
        """Get statistics for a lab"""
        researchers = db.query(User).filter(
            User.lab_id == lab_id,
            User.role == UserRole.RESEARCHER
        ).all()
        
        lab_stats = {
            'total_researchers': len(researchers),
            'researcher_stats': {}
        }
        
        for researcher in researchers:
            lab_stats['researcher_stats'][researcher.id] = self.get_researcher_statistics(
                db, researcher.id, start_date, end_date
            )
        
        return lab_stats
    
    def get_system_statistics(self, db: Session) -> dict:
        """Get system-wide statistics"""
        total_users = db.query(User).filter(User.is_active == True).count()
        total_researchers = db.query(User).filter(
            User.role == UserRole.RESEARCHER,
            User.is_active == True
        ).count()
        total_labs = db.query(User).filter(User.is_active == True).count()
        total_workbooks = db.query(Workbook).filter(Workbook.is_active == True).count()
        total_measurements = db.query(Measurement).count()
        
        # Instrument usage (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_usage = db.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.INSTRUMENT_MEASUREMENT_COMPLETED,
            AuditLog.created_at >= thirty_days_ago
        ).count()
        
        return {
            'total_users': total_users,
            'total_researchers': total_researchers,
            'total_labs': total_labs,
            'total_workbooks': total_workbooks,
            'total_measurements': total_measurements,
            'recent_instrument_usage': recent_usage
        }
    
    def get_instrument_usage_logs(self, db: Session, limit: int = 100) -> list:
        """Get recent instrument usage logs"""
        logs = db.query(AuditLog).filter(
            AuditLog.action_type.in_([
                AuditActionType.INSTRUMENT_CONNECTED,
                AuditActionType.INSTRUMENT_DISCONNECTED,
                AuditActionType.INSTRUMENT_MEASUREMENT_STARTED,
                AuditActionType.INSTRUMENT_MEASUREMENT_COMPLETED
            ])
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return logs

