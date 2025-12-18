"""
Dashboard Factory
Creates appropriate dashboard based on user role
"""

from src.models import UserRole
from src.gui.base_dashboard import BaseDashboard
from src.gui.researcher_dashboard import ResearcherDashboard
from src.gui.lab_admin_dashboard import LabAdminDashboard
from src.gui.super_admin_dashboard import SuperAdminDashboard


class DashboardFactory:
    """Factory for creating role-based dashboards"""
    
    @staticmethod
    def create_dashboard(role: UserRole, parent=None) -> BaseDashboard:
        """
        Create appropriate dashboard based on user role
        
        Args:
            role: UserRole enum value
            parent: Parent widget
            
        Returns:
            Appropriate dashboard instance
        """
        if role == UserRole.RESEARCHER:
            return ResearcherDashboard(parent)
        elif role == UserRole.LAB_ADMIN:
            return LabAdminDashboard(parent)
        elif role == UserRole.SUPER_ADMIN:
            return SuperAdminDashboard(parent)
        else:
            raise ValueError(f"Unknown role: {role}")
    
    @staticmethod
    def get_dashboard_class(role: UserRole):
        """Get dashboard class for a role (without instantiating)"""
        role_map = {
            UserRole.RESEARCHER: ResearcherDashboard,
            UserRole.LAB_ADMIN: LabAdminDashboard,
            UserRole.SUPER_ADMIN: SuperAdminDashboard
        }
        return role_map.get(role)

