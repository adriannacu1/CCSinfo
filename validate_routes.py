#!/usr/bin/env python3
"""
Validate Flask routes for duplicates and syntax
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_routes():
    """Validate Flask routes"""
    print("Validating Flask Routes")
    print("=" * 50)
    
    try:
        from app import create_app
        
        # Try to create the app
        app = create_app()
        
        print("✓ App created successfully")
        
        # List all routes
        with app.app_context():
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'url': str(rule)
                })
            
            # Check for admin routes specifically
            admin_routes = [r for r in routes if 'admin' in r['endpoint']]
            
            print(f"\nFound {len(admin_routes)} admin routes:")
            for route in sorted(admin_routes, key=lambda x: x['endpoint']):
                print(f"  - {route['endpoint']}: {route['url']}")
            
            # Check for duplicates
            endpoints = [r['endpoint'] for r in routes]
            duplicates = set([x for x in endpoints if endpoints.count(x) > 1])
            
            if duplicates:
                print(f"\n❌ Duplicate endpoints found: {duplicates}")
                return False
            else:
                print(f"\n✓ No duplicate endpoints found")
                return True
                
    except Exception as e:
        print(f"❌ Error validating routes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("CCS Info Route Validation")
    print("=" * 50)
    
    success = validate_routes()
    
    if success:
        print("\n🎉 All routes are valid!")
        print("You can now start the app with: python run.py")
    else:
        print("\n❌ Route validation failed.")
    
    sys.exit(0 if success else 1)
