"""
Main entry point for the desktop application.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.ui.login import LoginScreen
from desktop.ui.lab_selection import LabSelectionScreen


def main(page: ft.Page):
    """Main application entry point."""
    page.title = "TE Measurements"
    page.window.width = 500
    page.window.height = 600
    page.window.min_width = 400
    page.window.min_height = 500
    page.window.center()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    def on_login_success(token: str):
        """Handle successful login."""
        # Store token
        page.client_storage.set("auth_token", token)
        
        # Route to appropriate dashboard based on role
        from desktop.ui.dashboards.dashboard_router import DashboardRouter
        router = DashboardRouter(page, token, on_logout_callback=on_logout)
        router.route_to_dashboard()
    
    def on_logout():
        """Handle logout - navigate back to lab selection."""
        # Reset window size BEFORE clearing
        page.window.width = 500
        page.window.height = 600
        page.window.min_width = 400
        page.window.min_height = 500
        page.window.center()
        
        # Reset page alignment
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.padding = 0
        
        # Apply window changes immediately
        page.update()
        
        # Clear and show lab selection
        page.clean()
        
        # Restore window size after clean (in case clean() resets it)
        page.window.width = 500
        page.window.height = 600
        page.window.min_width = 400
        page.window.min_height = 500
        page.window.center()
        
        lab_selection = LabSelectionScreen(page, on_lab_selected=show_login_screen)
        page.add(lab_selection.build())
        page.update()
    
    def show_login_screen(selected_lab: dict):
        """Show login screen for selected lab."""
        page.clean()
        login_screen = LoginScreen(page, on_login_success, lab=selected_lab)
        page.add(login_screen.build())
        page.update()

    # Initial screen: lab selection
    lab_selection = LabSelectionScreen(page, on_lab_selected=show_login_screen)
    page.add(lab_selection.build())
    page.update()


if __name__ == "__main__":
    ft.app(target=main)

