"""
Lab selection screen shown before login.
"""
import sys
from pathlib import Path
from typing import Callable, Optional, List, Dict

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import flet as ft
from desktop.api_client import APIClient


class LabSelectionScreen:
    def __init__(self, page: ft.Page, on_lab_selected: Callable[[dict], None]):
        self.page = page
        self.on_lab_selected = on_lab_selected
        self.api_client = APIClient()

        self.labs: List[Dict] = []
        self.selected_lab: Optional[Dict] = None
        self.error_text = ft.Text("", color=ft.Colors.RED, visible=False)
        self.search_text = ""

    def load_labs(self):
        """Load labs from backend."""
        try:
            self.labs = self.api_client.get_labs()
        except Exception as ex:
            self.error_text.value = "Failed to load labs. Please check backend."
            self.error_text.visible = True
            self.page.update()

    def _on_search_change(self, e: ft.ControlEvent):
        self.search_text = (e.control.value or "").strip().lower()
        self.page.update()

    def _on_lab_card_click(self, lab: Dict):
        self.selected_lab = lab
        # Immediate continue on click
        self._handle_continue(None)

    def _handle_continue(self, e):
        if not self.selected_lab:
            self.error_text.value = "Please select a lab to continue."
            self.error_text.visible = True
            self.page.update()
            return

        # Store lab in client and notify main
        self.api_client.set_lab(self.selected_lab["lab_id"])
        self.on_lab_selected(self.selected_lab)

    def build(self) -> ft.Container:
        """Build the lab selection UI."""
        # Load labs once
        if not self.labs:
            self.load_labs()

        # Filter labs by search text
        if self.search_text:
            filtered_labs = [
                lab
                for lab in self.labs
                if self.search_text in lab["lab_name"].lower()
                or (lab.get("lab_description") or "").lower().find(self.search_text) != -1
            ]
        else:
            filtered_labs = self.labs[:]

        # Build lab cards and arrange them as rows (up to 4 cards per row)
        rows: list[ft.Row] = []
        row_cards: list[ft.Control] = []

        for idx, lab in enumerate(filtered_labs):
            card = ft.Container(
                content=ft.Container(
                    content=ft.Text(
                        lab["lab_name"],
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                ),
                width=220,
                height=100,  # Fixed height for all cards
                padding=10,
                margin=5,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                bgcolor=ft.Colors.WHITE,
                ink=True,
                on_click=lambda e, lab=lab: self._on_lab_card_click(lab),
            )
            row_cards.append(card)

            # When we have 4 cards, or this is the last card, push a row
            if len(row_cards) == 4 or idx == len(filtered_labs) - 1:
                rows.append(
                    ft.Row(
                        controls=row_cards,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
                row_cards = []

        labs_grid = ft.Column(
            controls=rows,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # University logo (reuse same asset as login)
        logo_path = Path(__file__).parent.parent.parent / "assets" / "ShizuokaU_loginscreen.png"
        if logo_path.exists():
            logo_control = ft.Image(
                src=str(logo_path),
                width=300,
                height=80,
                fit=ft.ImageFit.CONTAIN,
            )
        else:
            logo_control = ft.Text("Shizuoka University", size=24, weight=ft.FontWeight.BOLD)

        content = ft.Column(
            controls=[
                logo_control,
                ft.Text("TE Measurements", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Select your laboratory", size=14, color=ft.Colors.GREY_700),
                ft.TextField(
                    label="Search laboratories",
                    width=320,
                    on_change=self._on_search_change,
                ),
                labs_grid,
                self.error_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

        return ft.Container(
            content=content,
            alignment=ft.alignment.center,
            expand=True,
            padding=20,
        )


