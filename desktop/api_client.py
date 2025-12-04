"""
API client for communicating with the FastAPI backend.
"""
import httpx
from typing import Optional
import os


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token
    
    def clear_token(self):
        """Clear authentication token."""
        self.token = None
    
    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, username: str, password: str) -> dict:
        """Login and get JWT token (synchronous)."""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password},
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            self.set_token(data["access_token"])
            return data
    
    def get_current_user(self) -> dict:
        """Get current authenticated user info (synchronous)."""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/api/users/me",
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

