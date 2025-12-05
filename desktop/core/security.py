"""
Security utilities for desktop app - JWT token decoding.
"""
from typing import Optional, Dict
import base64
import json


def decode_jwt_token(token: str) -> Dict:
    """
    Decode JWT token (without verification for desktop app).
    In production, you should verify the token signature.
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        
        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        
        return {
            "user_id": data.get("user_id"),
            "username": data.get("sub"),
            "role": data.get("role"),
            "lab_id": data.get("lab_id"),
        }
    except Exception as e:
        print(f"Error decoding token: {e}")
        return {}

