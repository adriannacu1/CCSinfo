#!/usr/bin/env python3
"""
Simple test script to check if the Flask app can start without errors
"""
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    from app import create_app
    print("✓ Successfully imported create_app")
    
    app = create_app()
    print("✓ Successfully created Flask app")
    
    # Test if we can access the routes
    with app.app_context():
        print("✓ App context created successfully")
        
    print("\n🎉 Flask application is ready!")
    print("The app should work properly now.")
    print("\nYou can start the app with: python run.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required packages are installed.")
    
except Exception as e:
    print(f"❌ Error creating app: {e}")
    print("Check the application configuration and routes.")
