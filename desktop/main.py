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
        # Store token (you can use secure storage later)
        page.client_storage.set("auth_token", token)
        
        # TODO: Navigate to dashboard
        # For now, just show success message
        page.clean()
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Login Successful!", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Token: {token[:20]}...", size=12),
                        ft.Text("Dashboard coming soon...", size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        page.update()
    
    # Show login screen
    login_screen = LoginScreen(page, on_login_success)
    page.add(login_screen.build())
    page.update()


if __name__ == "__main__":
    ft.app(target=main)

