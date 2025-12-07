"""
Researcher Dashboard - Shows researcher's own workbooks and measurements.
"""
import sys
from pathlib import Path
from typing import Dict, Optional, Callable

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.api_client import APIClient


class ResearcherDashboard:
    """Dashboard for researchers - can only see their own work."""
    
    def __init__(self, page: ft.Page, token: str, user_info: Dict, lab_id: int, on_logout: Optional[Callable] = None):
        self.page = page
        self.token = token
        self.user_info = user_info
        self.lab_id = lab_id
        self.api_client = APIClient()
        self.api_client.set_token(token)
        self.on_logout = on_logout
        
        # State
        self.workbooks = []
        self.recent_measurements = []
        
    def build(self) -> ft.Container:
        """Build the researcher dashboard UI."""
        # Load data
        self._load_data()
        
        # Header
        header = self._build_header()
        
        # Main content
        content = self._build_content()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
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
            logo_image = ft.Icon(ft.Icons.SCHOOL, size=40, color=ft.Colors.BLUE)
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    # University logo
                    ft.Container(
                        content=logo_image,
                        padding=ft.padding.only(right=15),
                    ),
                    # Welcome text
                    ft.Column(
                        controls=[
                            ft.Text(
                                f"Welcome, {self.user_info.get('username', 'Researcher')}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "TE Measurements Dashboard",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Container(expand=True),  # Spacer
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
            bgcolor=ft.Colors.BLUE_50,
            border_radius=5,
            margin=ft.margin.only(bottom=20),
        )
    
    def _build_content(self) -> ft.Container:
        """Build main dashboard content."""
        # If no workbooks, show empty state with create button
        if not self.workbooks:
            return self._build_empty_state()
        
        # Show workbooks list
        return self._build_workbooks_view()
    
    def _build_empty_state(self) -> ft.Container:
        """Build empty state when no workbooks exist."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "No workbooks yet",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Create your first workbook to start measurements",
                        size=14,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    ft.ElevatedButton(
                        "+ Create New Workbook",
                        on_click=self._handle_create_workbook,
                        width=250,
                        height=50,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    def _build_workbooks_view(self) -> ft.Container:
        """Build workbooks list view."""
        workbook_cards = []
        for wb in self.workbooks:
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(wb.get("name", "Unnamed"), size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Created: {wb.get('created_at', 'N/A')}", size=12, color=ft.Colors.GREY_700),
                    ],
                    spacing=5,
                ),
                width=300,
                height=120,
                padding=15,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                bgcolor=ft.Colors.WHITE,
                on_click=lambda e, wb=wb: self._handle_open_workbook(wb),
            )
            workbook_cards.append(card)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("My Workbooks", size=20, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                "+ New Workbook",
                                on_click=self._handle_create_workbook,
                                bgcolor=ft.Colors.BLUE,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                    ),
                    ft.Container(height=20),
                    # Layout cards in rows
                    ft.Column(
                        controls=self._create_card_rows(workbook_cards),
                        spacing=15,
                    ),
                ],
            ),
            expand=True,
        )
    
    def _create_card_rows(self, cards: list, cards_per_row: int = 3) -> list:
        """Create rows of cards."""
        rows = []
        for i in range(0, len(cards), cards_per_row):
            row_cards = cards[i:i + cards_per_row]
            rows.append(
                ft.Row(
                    controls=row_cards,
                    spacing=15,
                )
            )
        return rows
    
    def _load_data(self):
        """Load workbooks and recent measurements."""
        # TODO: Implement API calls to load workbooks
        # For now, empty list
        self.workbooks = []
        self.recent_measurements = []
    
    def _handle_create_workbook(self, e):
        """Handle create workbook button click."""
        # TODO: Open workbook creation dialog
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Create workbook - Coming soon"))
        self.page.snack_bar.open = True
        self.page.update()
    
    def _handle_open_workbook(self, workbook: Dict):
        """Handle opening a workbook."""
        # TODO: Navigate to workbook detail view
        self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Opening {workbook.get('name')} - Coming soon"))
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

