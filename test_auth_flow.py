#!/usr/bin/env python3
"""
Test script to verify Google Calendar authentication flow.
"""

import os
import json
from pathlib import Path

def check_credentials():
    """Check if Google credentials file exists."""
    creds_file = Path('config/google_credentials.json')
    if not creds_file.exists():
        print("❌ Google credentials file not found!")
        print(f"   Expected: {creds_file.absolute()}")
        return False
    
    print("✅ Google credentials file found")
    
    # Check if it's valid JSON
    try:
        with open(creds_file) as f:
            data = json.load(f)
            if 'web' in data:
                print(f"   Client ID: {data['web'].get('client_id', 'N/A')[:50]}...")
                print(f"   Project ID: {data['web'].get('project_id', 'N/A')}")
                redirect_uris = data['web'].get('redirect_uris', [])
                print(f"   Redirect URIs: {redirect_uris}")
                
                # Check if localhost:5000 is in redirect URIs
                expected_uri = 'http://localhost:5000/auth/google/callback'
                if expected_uri in redirect_uris:
                    print(f"   ✅ Correct redirect URI configured")
                else:
                    print(f"   ⚠️  Expected redirect URI not found: {expected_uri}")
                    print(f"   Current URIs: {redirect_uris}")
                
                return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def check_token_directory():
    """Check token directory."""
    token_dir = Path('data/tokens')
    if not token_dir.exists():
        print("⚠️  Token directory does not exist (will be created on first auth)")
        return True
    
    print("✅ Token directory exists")
    
    # List tokens
    tokens = list(token_dir.glob('*_token.json'))
    if not tokens:
        print("   No tokens found (expected before first authentication)")
    else:
        print(f"   Found {len(tokens)} token(s):")
        for token_file in tokens:
            print(f"   - {token_file.name}")
            
            # Check if it's the default token
            if token_file.name == 'default_token.json':
                print("     ✅ Default token found!")
                
                # Check token validity
                try:
                    with open(token_file) as f:
                        token_data = json.load(f)
                        has_access = 'token' in token_data
                        has_refresh = 'refresh_token' in token_data
                        print(f"     Access token: {'✅' if has_access else '❌'}")
                        print(f"     Refresh token: {'✅' if has_refresh else '❌'}")
                except Exception as e:
                    print(f"     ❌ Error reading token: {e}")
    
    return True

def check_server_running():
    """Check if MCP server is running."""
    import requests
    try:
        response = requests.get('http://localhost:5000/health', timeout=2)
        if response.status_code == 200:
            print("✅ MCP server is running")
            return True
        else:
            print(f"⚠️  MCP server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ MCP server is not running")
        print("   Start it with: ./start_mcp_server.sh")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def main():
    print("=" * 60)
    print("Google Calendar Authentication Flow Test")
    print("=" * 60)
    print()
    
    print("1. Checking Google credentials...")
    creds_ok = check_credentials()
    print()
    
    print("2. Checking token directory...")
    token_ok = check_token_directory()
    print()
    
    print("3. Checking MCP server...")
    server_ok = check_server_running()
    print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if creds_ok and server_ok:
        print("✅ Ready for authentication!")
        print()
        print("Next steps:")
        print("1. Open http://localhost:8080 in your browser")
        print("2. Click 'Calendar' button")
        print("3. Click 'Sign in with Google'")
        print("4. Authorize the app")
        print("5. You should be redirected back with calendar events")
        print()
        print("After authentication, run this script again to verify token was saved.")
    else:
        print("❌ Setup incomplete")
        if not creds_ok:
            print("   - Fix Google credentials")
        if not server_ok:
            print("   - Start MCP server")

if __name__ == '__main__':
    main()

