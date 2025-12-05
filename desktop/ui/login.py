"""
Login screen with logo, centered user ID and password fields.
"""
import sys
from pathlib import Path
from typing import Callable, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.api_client import APIClient


class LoginScreen:
    def __init__(self, page: ft.Page, on_login_success: Callable, lab: Optional[dict] = None):
        self.page = page
        self.on_login_success = on_login_success
        self.api_client = APIClient()
        self.lab = lab
        if self.lab and "lab_id" in self.lab:
            self.api_client.set_lab(self.lab["lab_id"])
        
        # UI Components
        self.username_field = ft.TextField(
            label="User ID",
            width=300,
            autofocus=True,
            text_align=ft.TextAlign.LEFT,
        )
        
        self.password_field = ft.TextField(
            label="Password",
            width=300,
            password=True,
            can_reveal_password=True,
            text_align=ft.TextAlign.LEFT,
        )
        
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            visible=False,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.login_button = ft.ElevatedButton(
            "Login",
            on_click=self._handle_login,
            width=300,
            height=40,
        )
        
        self.loading_indicator = ft.ProgressRing(visible=False)
    
    def _handle_login(self, e):
        """Handle login button click."""
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self._show_error("Please enter both username and password")
            return
        
        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()
        
        # Perform login synchronously (fast, local API)
        try:
            result = self.api_client.login(username, password)
            self._login_success(result["access_token"])
        except Exception as ex:
            error_msg = "Login failed. Please check your credentials."
            if hasattr(ex, "response") and hasattr(ex.response, "status_code"):
                if ex.response.status_code == 401:
                    error_msg = "Invalid username or password"
            self._login_failed(error_msg)
    
    def _login_success(self, token: str):
        """Handle successful login on main thread."""
        self._set_loading(False)
        self.on_login_success(token)
    
    def _login_failed(self, error_msg: str):
        """Handle failed login on main thread."""
        self._set_loading(False)
        self._show_error(error_msg)
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()
    
    def _set_loading(self, loading: bool):
        """Show/hide loading indicator."""
        self.loading_indicator.visible = loading
        self.login_button.disabled = loading
        self.username_field.disabled = loading
        self.password_field.disabled = loading
        self.page.update()
    
    def build(self) -> ft.Container:
        """Build the login screen UI."""
        # Logo - try to load from assets, fallback to icon if not found
        logo_path = Path(__file__).parent.parent.parent / "assets" / "ShizuokaU_loginscreen.png"
        logo_image = None
        
        if logo_path.exists():
            # Use actual logo image - make it bigger
            logo_image = ft.Container(
                content=ft.Image(
                    src=str(logo_path),
                    width=350,
                    height=100,
                    fit=ft.ImageFit.CONTAIN,
                ),
                margin=ft.margin.only(bottom=5),  # Reduce bottom margin
            )
        else:
            # Fallback to icon if logo not found
            logo_image = ft.Icon(
                ft.Icons.SCIENCE,
                size=80,
                color=ft.Colors.BLUE,
            )
        
        subtitle_lab = self.lab["lab_name"] if self.lab and "lab_name" in self.lab else "Ikeda-Hamasaki Laboratory"

        logo = ft.Container(
            content=ft.Column(
                controls=[
                    logo_image,
                    ft.Text(
                        "TE Measurements",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        subtitle_lab,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=3,  
            ),
            padding=20,
        )
        
        # Login form
        login_form = ft.Container(
            content=ft.Column(
                controls=[
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    self.login_button,
                    self.loading_indicator,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=20,
        )
        
        # Main container - centered
        return ft.Container(
            content=ft.Column(
                controls=[
                    logo,
                    login_form,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=30,
            ),
            alignment=ft.alignment.center,
            expand=True,
            padding=20,
        )

