"""
Google OAuth and Calendar integration for MCP Server.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleAuthManager:
    """Manages Google OAuth authentication and token storage."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ]
    
    def __init__(self, credentials_file: str = 'config/google_credentials.json', 
                 token_dir: str = 'data/tokens'):
        """
        Initialize Google Auth Manager.
        
        Args:
            credentials_file: Path to Google OAuth client credentials JSON
            token_dir: Directory to store user tokens
        """
        self.credentials_file = credentials_file
        self.token_dir = Path(token_dir)
        self.token_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if credentials file exists
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(
                f"Google credentials file not found: {credentials_file}\n"
                "Please download OAuth 2.0 credentials from Google Cloud Console"
            )
    
    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> tuple:
        """
        Get Google OAuth authorization URL.

        Args:
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection (user_id)

        Returns:
            Tuple of (authorization_url, state)
        """
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )

        # Pass state to authorization_url if provided
        auth_params = {
            'access_type': 'offline',
            'include_granted_scopes': 'true',
            'prompt': 'consent'  # Force consent to get refresh token
        }

        if state:
            auth_params['state'] = state

        authorization_url, generated_state = flow.authorization_url(**auth_params)

        # Return both URL and the actual state that will be used
        return authorization_url, (state if state else generated_state)
    
    def exchange_code_for_token(self, code: str, redirect_uri: str, user_id: str = 'default') -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth redirect URI (must match authorization request)
            user_id: User identifier for token storage
            
        Returns:
            Token information dictionary
        """
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save credentials
        self._save_credentials(user_id, credentials)
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def get_credentials(self, user_id: str = 'default') -> Optional[Credentials]:
        """
        Get stored credentials for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Credentials object or None if not found
        """
        token_file = self.token_dir / f'{user_id}_token.json'
        
        if not token_file.exists():
            return None
        
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        credentials = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            self._save_credentials(user_id, credentials)
        
        return credentials
    
    def _save_credentials(self, user_id: str, credentials: Credentials):
        """Save credentials to file."""
        token_file = self.token_dir / f'{user_id}_token.json'
        
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)

