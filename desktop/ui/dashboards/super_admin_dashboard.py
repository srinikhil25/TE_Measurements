"""
Super Admin Dashboard - Central admin can see and manage all labs.
"""
import sys
from pathlib import Path
from typing import Dict, Optional, Callable

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.api_client import APIClient


class SuperAdminDashboard:
    """Dashboard for super admin - can see all labs and manage everything."""
    
    def __init__(self, page: ft.Page, token: str, user_info: Dict, on_logout: Optional[Callable] = None):
        self.page = page
        self.token = token
        self.user_info = user_info
        self.api_client = APIClient()
        self.api_client.set_token(token)
        self.on_logout = on_logout
        
        # State
        self.current_tab = "overview"
        self.all_labs = []
        self.all_users = []
    
    def build(self) -> ft.Container:
        """Build the super admin dashboard UI."""
        # Header
        header = self._build_header()
        
        # Tabs
        tabs = self._build_tabs()
        
        # Content based on selected tab
        content = self._build_tab_content()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    tabs,
                    content,
                ],
                spacing=0,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
    
    def _build_header(self) -> ft.Container:
        """Build dashboard header with university logo."""
        # Load university logo
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "ShizuokaU-short.png"
        logo_image = None
        if logo_path.exists():
            logo_image = ft.Image(
                src=str(logo_path),
                height=50,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            logo_image = ft.Icon(ft.Icons.SCHOOL, size=40, color=ft.Colors.PURPLE)
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    # University logo
                    ft.Container(
                        content=logo_image,
                        padding=ft.padding.only(right=15),
                    ),
                    # Dashboard title
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Super Admin Dashboard",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "System-wide management",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Logout",
                        on_click=self._handle_logout,
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=15,
            bgcolor=ft.Colors.PURPLE_50,
            border_radius=5,
            margin=ft.margin.only(bottom=20),
        )
    
    def _build_tabs(self) -> ft.Container:
        """Build navigation tabs."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "Overview",
                        on_click=lambda e: self._switch_tab("overview"),
                        bgcolor=ft.Colors.PURPLE if self.current_tab == "overview" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.current_tab == "overview" else ft.Colors.BLACK,
                    ),
                    ft.ElevatedButton(
                        "Labs",
                        on_click=lambda e: self._switch_tab("labs"),
                        bgcolor=ft.Colors.PURPLE if self.current_tab == "labs" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.current_tab == "labs" else ft.Colors.BLACK,
                    ),
                    ft.ElevatedButton(
                        "All Users",
                        on_click=lambda e: self._switch_tab("users"),
                        bgcolor=ft.Colors.PURPLE if self.current_tab == "users" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.current_tab == "users" else ft.Colors.BLACK,
                    ),
                    ft.ElevatedButton(
                        "System Stats",
                        on_click=lambda e: self._switch_tab("stats"),
                        bgcolor=ft.Colors.PURPLE if self.current_tab == "stats" else ft.Colors.GREY_300,
                        color=ft.Colors.WHITE if self.current_tab == "stats" else ft.Colors.BLACK,
                    ),
                ],
                spacing=10,
            ),
            margin=ft.margin.only(bottom=20),
        )
    
    def _build_tab_content(self) -> ft.Container:
        """Build content for current tab."""
        if self.current_tab == "overview":
            return self._build_overview_tab()
        elif self.current_tab == "labs":
            return self._build_labs_tab()
        elif self.current_tab == "users":
            return self._build_users_tab()
        elif self.current_tab == "stats":
            return self._build_stats_tab()
        return ft.Container()
    
    def _build_overview_tab(self) -> ft.Container:
        """Build overview tab."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("System Overview", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    ft.Row(
                        controls=[
                            self._build_stat_card("Total Labs", "0"),
                            self._build_stat_card("Total Users", "0"),
                            self._build_stat_card("Total Workbooks", "0"),
                            self._build_stat_card("Total Measurements", "0"),
                        ],
                        spacing=20,
                    ),
                ],
            ),
            expand=True,
        )
    
    def _build_stat_card(self, title: str, value: str) -> ft.Container:
        """Build a statistics card."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(value, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=14, color=ft.Colors.GREY_700),
                ],
                spacing=5,
            ),
            width=200,
            height=120,
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )
    
    def _build_labs_tab(self) -> ft.Container:
        """Build labs management tab."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("All Labs", size=20, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "+ Add Lab",
                                on_click=self._handle_add_lab,
                                bgcolor=ft.Colors.PURPLE,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                    ),
                    ft.Container(height=20),
                    ft.Text("Labs management - Coming soon", size=14, color=ft.Colors.GREY_700),
                ],
            ),
            expand=True,
        )
    
    def _build_users_tab(self) -> ft.Container:
        """Build all users tab."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("All System Users", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    ft.Text("Users list - Coming soon", size=14, color=ft.Colors.GREY_700),
                ],
            ),
            expand=True,
        )
    
    def _build_stats_tab(self) -> ft.Container:
        """Build system statistics tab."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("System Statistics", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    ft.Text("Detailed statistics - Coming soon", size=14, color=ft.Colors.GREY_700),
                ],
            ),
            expand=True,
        )
    
    def _switch_tab(self, tab_name: str):
        """Switch to a different tab."""
        self.current_tab = tab_name
        self.page.clean()
        self.page.add(self.build())
        self.page.update()
    
    def _handle_add_lab(self, e):
        """Handle add lab button."""
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Add lab - Coming soon"))
        self.page.snack_bar.open = True
        self.page.update()
    
    def _handle_logout(self, e):
        """Handle logout."""
        # Clear token
        self.page.client_storage.remove("auth_token")
        self.api_client.clear_token()
        
        # Call logout callback if provided
        if self.on_logout:
            self.on_logout()
        else:
            # Fallback: use logout handler
            from desktop.ui.dashboards.logout_handler import handle_logout
            handle_logout(self.page)

