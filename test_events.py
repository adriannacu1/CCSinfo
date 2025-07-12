#!/usr/bin/env python3
"""
Test script to verify events functionality
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    print("✓ App import successful")
    
    app = create_app()
    print("✓ App creation successful")
    
    with app.test_client() as client:
        # Test events page
        response = client.get('/events')
        print(f"✓ Events page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Events page loads successfully")
        else:
            print(f"✗ Events page failed with status {response.status_code}")
            print(response.data.decode('utf-8')[:500] + "...")
            
        # Test API endpoint
        response = client.get('/api/events/1')
        print(f"✓ API events endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            import json
            data = json.loads(response.data)
            print(f"✓ API response success: {data.get('success', False)}")
        else:
            print(f"✗ API endpoint failed with status {response.status_code}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
