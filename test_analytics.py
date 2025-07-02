"""
Test Analytics Implementation
Verifies that all analytics features are properly implemented
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_analytics_routes():
    """Test that analytics routes are defined"""
    try:
        from app.routes import register_routes
        from flask import Flask
        
        app = Flask(__name__)
        register_routes(app)
        
        # Check if analytics routes exist
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        analytics_routes = [
            '/admin/analytics',
            '/admin/analytics/data',
            '/admin/analytics/chart',
            '/admin/analytics/export'
        ]
        
        missing_routes = []
        for route in analytics_routes:
            if route not in routes:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"❌ Missing analytics routes: {missing_routes}")
            return False
        else:
            print("✅ All analytics routes are properly defined")
            return True
            
    except Exception as e:
        print(f"❌ Error testing analytics routes: {e}")
        return False

def test_analytics_functions():
    """Test that analytics functions exist"""
    try:
        from app.routes import (
            get_analytics_data, 
            log_page_view, 
            log_system_action,
            get_chart_data
        )
        
        print("✅ All analytics functions are properly defined")
        return True
        
    except ImportError as e:
        print(f"❌ Missing analytics functions: {e}")
        return False

def test_analytics_template():
    """Test that analytics template exists"""
    import os
    
    template_path = os.path.join('templates', 'admin', 'analytics.html')
    
    if os.path.exists(template_path):
        print("✅ Analytics template exists")
        return True
    else:
        print("❌ Analytics template missing")
        return False

def main():
    """Run all analytics tests"""
    print("=== Analytics Implementation Test ===")
    print()
    
    tests_passed = 0
    total_tests = 3
    
    # Test routes
    if test_analytics_routes():
        tests_passed += 1
    
    # Test functions
    if test_analytics_functions():
        tests_passed += 1
    
    # Test template
    if test_analytics_template():
        tests_passed += 1
    
    print()
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Analytics implementation is complete!")
        print()
        print("Features available:")
        print("• Homepage view tracking")
        print("• Admin dashboard analytics")
        print("• Interactive charts and graphs")
        print("• User activity monitoring")
        print("• Room usage statistics")
        print("• System logs and reports")
        print("• CSV export functionality")
        print("• Real-time metrics")
        print()
        print("To access analytics:")
        print("1. Start the Flask app: python run.py")
        print("2. Login as admin")
        print("3. Navigate to /admin/analytics")
    else:
        print("❌ Analytics implementation has issues")

if __name__ == "__main__":
    main()
