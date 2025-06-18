#!/usr/bin/env python3
"""
Test the admin student profile API to check if check_out_time is being returned
"""
import requests
import json

# Test the API endpoint
url = "http://127.0.0.1:5000/admin/students/1/profile-simple"

try:
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            student = data.get('student', {})
            activity_log = student.get('activity_log', [])
            
            print("Student Profile API Test Results:")
            print("=" * 50)
            print(f"Student: {student.get('name')}")
            print(f"Student Number: {student.get('student_number')}")
            print("\nActivity Log Records:")
            
            for i, log in enumerate(activity_log):
                print(f"\nRecord {i+1}:")
                print(f"  PC Number: {log.get('pc_number')}")
                print(f"  Check-in Time: {log.get('check_in_time')}")
                print(f"  Check-out Time: {log.get('check_out_time')}")
                print(f"  Room: {log.get('room_name')}")
                print(f"  Session ID: {log.get('session_id')}")
                
            print(f"\nTotal activity records: {len(activity_log)}")
            
        else:
            print(f"API Error: {data.get('message', 'Unknown error')}")
    else:
        print(f"HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("Cannot connect to the Flask application. Make sure it's running on http://127.0.0.1:5000")
except Exception as e:
    print(f"Error: {e}")
