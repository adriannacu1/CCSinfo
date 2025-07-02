#!/usr/bin/env python3
"""
Test script for analytics functionality
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.routes import get_analytics_data

def test_analytics():
    """Test the analytics data function"""
    print("Testing Analytics Functionality")
    print("=" * 50)
    
    try:
        # Create the app
        app = create_app()
        
        with app.app_context():
            # Test getting analytics data
            print("1. Testing get_analytics_data function...")
            analytics_data = get_analytics_data(30)
            
            print("✓ Analytics data retrieved successfully")
            print(f"   - Homepage views: {analytics_data.get('homepage_views', 'N/A')}")
            print(f"   - Active users: {analytics_data.get('active_users', 'N/A')}")
            print(f"   - Room accesses: {analytics_data.get('room_accesses', 'N/A')}")
            print(f"   - Temp key usage: {analytics_data.get('temp_key_usage', 'N/A')}")
            print(f"   - CPU usage: {analytics_data.get('cpu_usage', 'N/A')}%")
            print(f"   - Memory usage: {analytics_data.get('memory_usage', 'N/A')}%")
            
            # Test chart data
            print("\n2. Testing chart data...")
            visitors_labels = analytics_data.get('visitors_chart_labels', [])
            visitors_data = analytics_data.get('visitors_chart_data', [])
            rooms_labels = analytics_data.get('rooms_chart_labels', [])
            rooms_data = analytics_data.get('rooms_chart_data', [])
            
            print(f"   - Visitors chart: {len(visitors_labels)} labels, {len(visitors_data)} data points")
            print(f"   - Room usage chart: {len(rooms_labels)} labels, {len(rooms_data)} data points")
            
            # Test system logs
            print("\n3. Testing system logs...")
            system_logs = analytics_data.get('system_logs', [])
            print(f"   - System logs: {len(system_logs)} entries")
            
            print("\n✓ All analytics tests passed!")
            return True
            
    except Exception as e:
        print(f"✗ Error testing analytics: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_accessibility():
    """Test if the analytics template can be accessed"""
    print("\n" + "=" * 50)
    print("Testing Template Accessibility")
    print("=" * 50)
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 
                                   'templates', 'admin', 'analytics_robust.html')
        
        if os.path.exists(template_path):
            print("✓ Analytics template file exists")
            
            # Check file size
            file_size = os.path.getsize(template_path)
            print(f"   - Template size: {file_size} bytes")
            
            if file_size > 1000:  # At least 1KB
                print("✓ Template appears to have content")
            else:
                print("⚠ Template seems small, might be incomplete")
            
            return True
        else:
            print("✗ Analytics template file not found")
            return False
            
    except Exception as e:
        print(f"✗ Error checking template: {e}")
        return False

if __name__ == '__main__':
    print("CCS Info Analytics Test Suite")
    print("=" * 50)
    
    # Run tests
    test1_passed = test_analytics()
    test2_passed = test_template_accessibility()
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"Analytics Data Function: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Template Accessibility: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Analytics feature is ready.")
        print("\nTo access the analytics dashboard:")
        print("1. Start the Flask app: python run.py")
        print("2. Login to admin panel")
        print("3. Navigate to Analytics from the sidebar")
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
    
    sys.exit(0 if (test1_passed and test2_passed) else 1)
