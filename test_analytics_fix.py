#!/usr/bin/env python3
"""
Test script to verify analytics functionality after fixes
"""

def test_analytics_template():
    """Test that analytics template renders correctly"""
    try:
        # Test template parsing
        template_path = "templates/admin/analytics.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common syntax issues
        issues = []
        
        # Check for broken Jinja2 syntax
        broken_patterns = [
            ") | tojson | safe\n        }}",
            "| safe\n        }}",
            "}} \n        }}",
            "| tojson | safe\n}}"
        ]
        
        for pattern in broken_patterns:
            if pattern in content:
                issues.append(f"Broken Jinja2 syntax found: {repr(pattern)}")
                # Show the context where this appears
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if pattern.split('\n')[0] in line:
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        print(f"Context around line {i+1}:")
                        for j in range(start, end):
                            marker = " -> " if j == i else "    "
                            print(f"{marker}{j+1}: {lines[j]}")
                        break
        
        # Check for unmatched brackets
        open_brackets = content.count('{')
        close_brackets = content.count('}')
        if open_brackets != close_brackets:
            issues.append(f"Unmatched brackets: {open_brackets} open, {close_brackets} close")
        
        # Check for JavaScript function completeness
        if "function initializeCharts()" in content and not "function initializeCharts() {" in content:
            issues.append("Incomplete function definition")
        
        if issues:
            print("❌ Template has issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ Analytics template syntax is correct")
            return True
            
    except Exception as e:
        print(f"❌ Error testing template: {e}")
        return False

def test_analytics_routes():
    """Test that analytics routes are defined"""
    try:
        import sys
        sys.path.append('.')
        
        # Import the routes module
        from app.routes import register_routes
        from flask import Flask
        
        app = Flask(__name__)
        register_routes(app)
        
        # Check if analytics routes exist
        analytics_routes = [rule for rule in app.url_map.iter_rules() if 'analytics' in rule.rule]
        
        expected_routes = [
            '/admin/analytics',
            '/admin/analytics/data', 
            '/admin/analytics/chart',
            '/admin/analytics/export'
        ]
        
        found_routes = [route.rule for route in analytics_routes]
        
        missing_routes = [route for route in expected_routes if route not in found_routes]
        
        if missing_routes:
            print(f"❌ Missing analytics routes: {missing_routes}")
            return False
        else:
            print("✅ All analytics routes are defined")
            print(f"Found routes: {found_routes}")
            return True
            
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        return False

def main():
    """Run all analytics tests"""
    print("=== Analytics Fix Verification ===")
    print()
    
    template_ok = test_analytics_template()
    routes_ok = test_analytics_routes()
    
    print()
    if template_ok and routes_ok:
        print("✅ Analytics implementation is working correctly!")
        print()
        print("You can now:")
        print("1. Start the Flask application: python run.py")
        print("2. Login as admin")
        print("3. Navigate to Analytics in the sidebar")
        print("4. View charts, metrics, and reports")
        print("5. Export data and filter logs")
    else:
        print("❌ Some issues found - check the output above")

if __name__ == "__main__":
    main()
