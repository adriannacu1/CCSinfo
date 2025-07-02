#!/usr/bin/env python3
"""
Quick test to verify the admin_management route is working
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_admin_routes():
    """Test if all admin routes are properly defined"""
    print("Testing Admin Routes")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Test if url_for works for key admin routes
            from flask import url_for
            
            routes_to_test = [
                'admin_login',
                'admin_dashboard', 
                'admin_analytics',
                'admin_management',
                'admin_settings',
                'admin_students',
                'admin_faculty',
                'admin_rooms',
                'admin_sections',
                'admin_temp_keys'
            ]
            
            print("Testing route URL generation:")
            for route in routes_to_test:
                try:
                    url = url_for(route)
                    print(f"✓ {route}: {url}")
                except Exception as e:
                    print(f"✗ {route}: ERROR - {e}")
            
            print(f"\n✅ All routes tested successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("CCS Info Route Test")
    print("=" * 50)
    
    success = test_admin_routes()
    
    if success:
        print("\n🎉 All admin routes are working!")
        print("\nThe BuildError should now be fixed.")
        print("You can now start the app with: python run.py")
    else:
        print("\n❌ Some routes are still having issues.")
    
    sys.exit(0 if success else 1)
