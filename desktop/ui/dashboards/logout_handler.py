"""
Logout handler utility for dashboards (fallback).
This is used as a fallback if no logout callback is provided.
"""
import sys
from pathlib import Path
from typing import Callable, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.ui.lab_selection import LabSelectionScreen
from desktop.ui.login import LoginScreen


def handle_logout(page: ft.Page, on_login_success_callback: Optional[Callable] = None):
    """
    Handle logout: clear token, reset window, navigate to lab selection.
    This is a fallback handler used when no callback is provided from main app.
    
    Args:
        page: Flet page object
        on_login_success_callback: Optional callback function for successful login
    """
    # Clear authentication token
    page.client_storage.remove("auth_token")
    
    # Reset window size to login screen size BEFORE clearing
    page.window.width = 500
    page.window.height = 600
    page.window.min_width = 400
    page.window.min_height = 500
    page.window.center()
    
    # Reset page alignment to center (for login screens)
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    
    # Apply window changes immediately
    page.update()
    
    # Clear page
    page.clean()
    
    # Restore window size after clean (in case clean() resets it)
    page.window.width = 500
    page.window.height = 600
    page.window.min_width = 400
    page.window.min_height = 500
    page.window.center()
    
    # Define login screen handler
    def show_login_screen(selected_lab: dict):
        """Show login screen for selected lab."""
        page.clean()
        if on_login_success_callback:
            login_screen = LoginScreen(page, on_login_success_callback, lab=selected_lab)
        else:
            # Fallback: create a simple callback
            def default_on_login_success(token: str):
                from desktop.ui.dashboards.dashboard_router import DashboardRouter
                router = DashboardRouter(page, token)
                router.route_to_dashboard()
            login_screen = LoginScreen(page, default_on_login_success, lab=selected_lab)
        page.add(login_screen.build())
        page.update()
    
    # Show lab selection screen
    lab_selection = LabSelectionScreen(page, on_lab_selected=show_login_screen)
    page.add(lab_selection.build())
    page.update()

