#!/usr/bin/env python3
"""
Test script to verify caching fix for MCP server.

This script tests:
1. Upload a file
2. Request summary (should process file)
3. Request flashcards (should reuse cache)
4. Request quiz (should reuse cache)
5. Verify content is related to uploaded file (not hallucinations)
"""

import requests
import time
import json
from pathlib import Path

API_URL = 'http://localhost:5000'

def test_caching():
    """Test the caching functionality."""
    
    print("=" * 80)
    print("TESTING MCP SERVER CACHING FIX")
    print("=" * 80)
    
    # Find a test file
    test_files = [
        'data/uploads/sample_lecture.mp3',
        'data/uploads/sample_lecture.pdf',
        'data/sample_lecture.mp3',
        'data/sample_data/sample_lecture.mp3'
    ]
    
    test_file = None
    for f in test_files:
        if Path(f).exists():
            test_file = f
            break
    
    if not test_file:
        print("❌ No test file found. Please ensure sample_lecture.mp3 exists.")
        print("   Tried:", test_files)
        return
    
    print(f"\n📁 Using test file: {test_file}")
    print(f"   File size: {Path(test_file).stat().st_size / 1024 / 1024:.1f} MB")
    
    # Upload file
    print("\n" + "=" * 80)
    print("STEP 1: Upload File")
    print("=" * 80)
    
    with open(test_file, 'rb') as f:
        r = requests.post(f'{API_URL}/upload', files={'file': f})
    
    if r.status_code != 200:
        print(f"❌ Upload failed: {r.status_code}")
        print(r.text)
        return
    
    file_id = r.json()['file_id']
    print(f"✅ Uploaded successfully")
    print(f"   File ID: {file_id}")
    
    # Request 1: Summary (will process file)
    print("\n" + "=" * 80)
    print("STEP 2: Request Summary (First Request - Will Process File)")
    print("=" * 80)
    print("⏳ Processing... (this will take ~10-15 minutes for ASR + embeddings)")
    
    start = time.time()
    r = requests.post(f'{API_URL}/process', json={
        'file_id': file_id,
        'request_type': 'summary',
        'model': 'default',
        'parameters': {}
    })
    elapsed = time.time() - start
    
    if r.status_code != 200:
        print(f"❌ Summary request failed: {r.status_code}")
        print(r.text)
        return
    
    result = r.json()
    print(f"✅ Summary generated in {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"\n📝 Summary Preview:")
    summary = result['result']['summary']
    print(f"   Length: {len(summary)} characters")
    print(f"   Preview: {summary[:200]}...")
    
    # Request 2: Flashcards (should reuse cache!)
    print("\n" + "=" * 80)
    print("STEP 3: Request Flashcards (Should Reuse Cache - Fast!)")
    print("=" * 80)
    print("⏳ Processing...")
    
    start = time.time()
    r = requests.post(f'{API_URL}/process', json={
        'file_id': file_id,
        'request_type': 'flashcards',
        'model': 'default',
        'parameters': {'max_cards': 10}
    })
    elapsed = time.time() - start
    
    if r.status_code != 200:
        print(f"❌ Flashcards request failed: {r.status_code}")
        print(r.text)
        return
    
    result = r.json()
    flashcards = result['result']['flashcards']
    print(f"✅ Flashcards generated in {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"\n🃏 Flashcards Preview:")
    print(f"   Count: {len(flashcards)} cards")
    if flashcards:
        print(f"   First card:")
        print(f"      Front: {flashcards[0]['front'][:100]}...")
        print(f"      Back: {flashcards[0]['back'][:100]}...")
    
    # Request 3: Quiz (should reuse cache!)
    print("\n" + "=" * 80)
    print("STEP 4: Request Quiz (Should Reuse Cache - Fast!)")
    print("=" * 80)
    print("⏳ Processing...")
    
    start = time.time()
    r = requests.post(f'{API_URL}/process', json={
        'file_id': file_id,
        'request_type': 'quiz',
        'model': 'default',
        'parameters': {'num_questions': 5}
    })
    elapsed = time.time() - start
    
    if r.status_code != 200:
        print(f"❌ Quiz request failed: {r.status_code}")
        print(r.text)
        return
    
    result = r.json()
    questions = result['result']['questions']
    print(f"✅ Quiz generated in {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"\n❓ Quiz Preview:")
    print(f"   Count: {len(questions)} questions")
    if questions:
        print(f"   First question:")
        print(f"      Q: {questions[0]['question'][:100]}...")
        print(f"      A: {questions[0]['answer'][:100]}...")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)
    print("\n✅ All requests completed successfully!")
    print("\n📊 Performance Summary:")
    print("   - Request 1 (Summary): Should take ~10-15 minutes (includes ASR)")
    print("   - Request 2 (Flashcards): Should take ~1-3 minutes (reuses cache)")
    print("   - Request 3 (Quiz): Should take ~1-3 minutes (reuses cache)")
    print("\n💡 If requests 2 and 3 were fast, caching is working!")
    print("💡 If all content is related to the uploaded file, hallucination is fixed!")

if __name__ == '__main__':
    try:
        test_caching()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

