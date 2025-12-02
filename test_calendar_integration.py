#!/usr/bin/env python3
"""
Test script for Google Calendar integration.
Tests the calendar functionality without requiring actual Google credentials.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all calendar modules can be imported."""
    print("Testing imports...")
    
    try:
        from mcp_server.google_auth import GoogleAuthManager
        print("✅ google_auth module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google_auth: {e}")
        return False
    
    try:
        from mcp_server.google_calendar import GoogleCalendarService
        print("✅ google_calendar module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google_calendar: {e}")
        return False
    
    return True


def test_auth_manager_without_credentials():
    """Test GoogleAuthManager behavior without credentials file."""
    print("\nTesting GoogleAuthManager without credentials...")
    
    from mcp_server.google_auth import GoogleAuthManager
    
    try:
        # This should raise FileNotFoundError
        auth = GoogleAuthManager(credentials_file='nonexistent.json')
        print("❌ Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✅ Correctly raised FileNotFoundError: {e}")
        return True


def test_server_endpoints():
    """Test that server has calendar endpoints defined."""
    print("\nTesting server endpoints...")
    
    from mcp_server.server import app
    
    # Get all routes
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    
    expected_endpoints = [
        '/auth/google',
        '/auth/google/callback',
        '/calendar/events'
    ]
    
    all_found = True
    for endpoint in expected_endpoints:
        if endpoint in routes:
            print(f"✅ Endpoint {endpoint} found")
        else:
            print(f"❌ Endpoint {endpoint} NOT found")
            all_found = False
    
    return all_found


def test_frontend_files():
    """Test that frontend files have calendar integration."""
    print("\nTesting frontend files...")
    
    # Check index.html
    html_file = Path('frontend/index.html')
    if not html_file.exists():
        print("❌ frontend/index.html not found")
        return False
    
    html_content = html_file.read_text()
    if 'data-mode="calendar"' in html_content:
        print("✅ Calendar mode found in index.html")
    else:
        print("❌ Calendar mode NOT found in index.html")
        return False
    
    # Check app.js
    js_file = Path('frontend/app.js')
    if not js_file.exists():
        print("❌ frontend/app.js not found")
        return False
    
    js_content = js_file.read_text()
    
    required_functions = [
        'showCalendar',
        'checkAuthAndShowCalendar',
        'displayCalendar',
        'renderCalendarEvents'
    ]
    
    all_found = True
    for func in required_functions:
        if f'function {func}' in js_content or f'async function {func}' in js_content:
            print(f"✅ Function {func}() found in app.js")
        else:
            print(f"❌ Function {func}() NOT found in app.js")
            all_found = False
    
    return all_found


def test_requirements():
    """Test that requirements.txt has Google API dependencies."""
    print("\nTesting requirements.txt...")
    
    req_file = Path('requirements.txt')
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    req_content = req_file.read_text()
    
    required_packages = [
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client'
    ]
    
    all_found = True
    for package in required_packages:
        if package in req_content:
            print(f"✅ Package {package} found in requirements.txt")
        else:
            print(f"❌ Package {package} NOT found in requirements.txt")
            all_found = False
    
    return all_found


def test_gitignore():
    """Test that .gitignore has calendar-related entries."""
    print("\nTesting .gitignore...")
    
    gitignore_file = Path('.gitignore')
    if not gitignore_file.exists():
        print("❌ .gitignore not found")
        return False
    
    gitignore_content = gitignore_file.read_text()
    
    required_entries = [
        'google_credentials.json',
        'data/tokens/'
    ]
    
    all_found = True
    for entry in required_entries:
        if entry in gitignore_content:
            print(f"✅ Entry '{entry}' found in .gitignore")
        else:
            print(f"❌ Entry '{entry}' NOT found in .gitignore")
            all_found = False
    
    return all_found


def test_documentation():
    """Test that documentation files exist."""
    print("\nTesting documentation...")
    
    doc_files = [
        'GOOGLE_CALENDAR_SETUP.md',
        'CALENDAR_INTEGRATION_SUMMARY.md',
        'config/google_credentials.json.template'
    ]
    
    all_found = True
    for doc_file in doc_files:
        if Path(doc_file).exists():
            print(f"✅ Documentation file {doc_file} exists")
        else:
            print(f"❌ Documentation file {doc_file} NOT found")
            all_found = False
    
    return all_found


def main():
    """Run all tests."""
    print("=" * 70)
    print("Google Calendar Integration Test Suite")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Auth Manager", test_auth_manager_without_credentials),
        ("Server Endpoints", test_server_endpoints),
        ("Frontend Files", test_frontend_files),
        ("Requirements", test_requirements),
        ("Gitignore", test_gitignore),
        ("Documentation", test_documentation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Calendar integration is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

