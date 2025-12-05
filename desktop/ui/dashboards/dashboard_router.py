"""
Dashboard router - routes users to appropriate dashboard based on role.
"""
import sys
from pathlib import Path
from typing import Optional, Dict

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.ui.dashboards.super_admin_dashboard import SuperAdminDashboard
from desktop.ui.dashboards.lab_admin_dashboard import LabAdminDashboard
from desktop.ui.dashboards.researcher_dashboard import ResearcherDashboard
from desktop.core.security import decode_jwt_token


class DashboardRouter:
    """Routes users to the appropriate dashboard based on their role."""
    
    def __init__(self, page: ft.Page, token: str):
        self.page = page
        self.token = token
        self.user_info: Optional[Dict] = None
        
    def decode_token(self) -> Dict:
        """Decode JWT token to get user info."""
        if not self.user_info:
            self.user_info = decode_jwt_token(self.token)
        return self.user_info
    
    def route_to_dashboard(self):
        """Route to appropriate dashboard based on user role."""
        user_info = self.decode_token()
        role = user_info.get("role")
        lab_id = user_info.get("lab_id")
        
        # Preserve current window size and page settings before clearing
        current_width = self.page.window.width
        current_height = self.page.window.height
        current_min_width = self.page.window.min_width
        current_min_height = self.page.window.min_height
        
        # Preserve page alignment settings (these might affect window behavior)
        current_vertical_alignment = self.page.vertical_alignment
        current_horizontal_alignment = self.page.horizontal_alignment
        current_padding = self.page.padding
        
        # Clear page and route
        self.page.clean()
        
        # Restore window size after clean (in case clean() resets it)
        # Only restore if values exist (not None)
        if current_width is not None:
            self.page.window.width = current_width
        if current_height is not None:
            self.page.window.height = current_height
        if current_min_width is not None:
            self.page.window.min_width = current_min_width
        if current_min_height is not None:
            self.page.window.min_height = current_min_height
        
        # Restore page alignment settings
        if current_vertical_alignment is not None:
            self.page.vertical_alignment = current_vertical_alignment
        if current_horizontal_alignment is not None:
            self.page.horizontal_alignment = current_horizontal_alignment
        if current_padding is not None:
            self.page.padding = current_padding
        
        # For dashboards, we want top-left alignment, not centered
        # This prevents window from auto-resizing based on content
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.START
        
        if role == "super_admin":
            dashboard = SuperAdminDashboard(self.page, self.token, user_info)
        elif role == "lab_admin":
            dashboard = LabAdminDashboard(self.page, self.token, user_info, lab_id)
        elif role == "researcher":
            dashboard = ResearcherDashboard(self.page, self.token, user_info, lab_id)
        else:
            # Fallback - show error
            self.page.add(
                ft.Container(
                    content=ft.Text(f"Unknown role: {role}", color=ft.Colors.RED),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )
            self.page.update()
            return
        
        # Build and show dashboard
        self.page.add(dashboard.build())
        # Update both page content and window size
        self.page.update()

