#!/usr/bin/env python3
"""
Test script for MCP Server
Tests all endpoints and functionality
"""

import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint."""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_models():
    """Test models listing endpoint."""
    print("\n=== Testing Models Listing ===")
    try:
        response = requests.get(f"{API_URL}/models")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available models: {len(data['models'])}")
        for model in data['models']:
            print(f"  - {model['name']}: {model['description']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_request_types():
    """Test request types listing endpoint."""
    print("\n=== Testing Request Types Listing ===")
    try:
        response = requests.get(f"{API_URL}/request-types")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available request types: {len(data['request_types'])}")
        for req_type in data['request_types']:
            print(f"  - {req_type['name']}: {req_type['description']}")
            print(f"    Default params: {req_type['default_parameters']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_upload():
    """Test file upload endpoint."""
    print("\n=== Testing File Upload ===")
    
    # Use the sample PDF
    test_file = Path("data/sample_lecture.pdf")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False, None
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/pdf')}
            response = requests.post(f"{API_URL}/upload", files=files)
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            return True, data['file_id']
        return False, None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_process(file_id, request_type='summary'):
    """Test document processing endpoint."""
    print(f"\n=== Testing Processing ({request_type}) ===")
    
    if not file_id:
        print("❌ No file_id provided")
        return False
    
    try:
        payload = {
            'file_id': file_id,
            'request_type': request_type,
            'model': 'default',
            'parameters': {}
        }
        
        print(f"Processing {request_type}... (this may take a few minutes)")
        response = requests.post(
            f"{API_URL}/process",
            json=payload,
            timeout=600  # 10 minute timeout
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {request_type.capitalize()} generated successfully!")
            
            # Show preview of results
            if request_type == 'summary':
                summary = data['result']['summary']
                print(f"Summary preview: {summary[:200]}...")
            elif request_type == 'flashcards':
                count = data['result']['count']
                print(f"Generated {count} flashcards")
                if count > 0:
                    print(f"First card: {data['result']['flashcards'][0]}")
            elif request_type == 'quiz':
                count = data['result']['count']
                print(f"Generated {count} quiz questions")
                if count > 0:
                    print(f"First question: {data['result']['questions'][0]['question']}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_batch_process(file_id):
    """Test batch processing endpoint."""
    print(f"\n=== Testing Batch Processing ===")
    
    if not file_id:
        print("❌ No file_id provided")
        return False
    
    try:
        payload = {
            'file_id': file_id,
            'requests': [
                {'type': 'summary', 'parameters': {'scale': 'paragraph'}},
                {'type': 'flashcards', 'parameters': {'max_cards': 5}},
                {'type': 'quiz', 'parameters': {'num_questions': 3}}
            ],
            'model': 'default'
        }
        
        print("Processing all request types... (this may take several minutes)")
        response = requests.post(
            f"{API_URL}/batch-process",
            json=payload,
            timeout=900  # 15 minute timeout
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Batch processing completed!")
            
            for req_type, result in data['results'].items():
                if result['success']:
                    print(f"  ✓ {req_type}: Success")
                else:
                    print(f"  ❌ {req_type}: {result.get('error', 'Unknown error')}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test basic endpoints
    results['health'] = test_health()
    results['models'] = test_models()
    results['request_types'] = test_request_types()
    
    # Test upload
    upload_success, file_id = test_upload()
    results['upload'] = upload_success
    
    if upload_success and file_id:
        # Test individual processing (only summary for speed)
        results['process_summary'] = test_process(file_id, 'summary')
        
        # Optionally test batch processing (commented out for speed)
        # results['batch_process'] = test_batch_process(file_id)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, success in results.items():
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)

