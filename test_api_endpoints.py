#!/usr/bin/env python3
"""
Test script to verify Flask app is running and API endpoints work
"""

import requests
import json
from datetime import datetime

def test_flask_app():
    """Test if Flask app is running and API works"""
    print("=== Flask App API Test ===\n")
    
    base_url = "http://127.0.0.1:5000"
    
    # Test 1: Check if main app is running
    try:
        print("1. Testing main page...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print(f"❌ Main page returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Flask app: {e}")
        print("💡 Make sure to run: python run.py")
        return False
    
    # Test 2: Check events page
    try:
        print("\n2. Testing events page...")
        response = requests.get(f"{base_url}/events", timeout=5)
        if response.status_code == 200:
            print("✅ Events page accessible")
            if "No Events Found" in response.text:
                print("⚠️  Events page shows 'No Events Found'")
            elif "AI & Machine Learning" in response.text:
                print("✅ Events are displaying on the page")
        else:
            print(f"❌ Events page returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Events page error: {e}")
    
    # Test 3: Test API endpoint for event details
    try:
        print("\n3. Testing API endpoint...")
        # Try event ID 1 (AI & Machine Learning Summit)
        response = requests.get(f"{base_url}/api/events/1", timeout=5)
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint accessible")
            print(f"API Response Success: {data.get('success', False)}")
            
            if data.get('success'):
                event = data.get('event', {})
                print(f"Event Title: {event.get('title', 'N/A')}")
                print(f"Event Date: {event.get('event_date', 'N/A')}")
                print(f"Speakers Count: {len(event.get('speakers', []))}")
                print("✅ API returning proper event data")
            else:
                print(f"❌ API returned error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ API returned status: {response.status_code}")
            print(f"Response content: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API endpoint error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ API returned invalid JSON: {e}")
    
    # Test 4: Test event profile page
    try:
        print("\n4. Testing event profile page...")
        response = requests.get(f"{base_url}/events/1", timeout=5)
        if response.status_code == 200:
            print("✅ Event profile page accessible")
            if "AI & Machine Learning Summit" in response.text:
                print("✅ Event profile showing correct data")
        else:
            print(f"❌ Event profile returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Event profile error: {e}")
    
    print(f"\n=== Test completed at {datetime.now()} ===")
    return True

if __name__ == '__main__':
    test_flask_app()
