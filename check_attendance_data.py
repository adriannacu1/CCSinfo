#!/usr/bin/env python3
"""
Script to check sample attendance records and their check-out times
"""
import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Your MySQL password
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def check_attendance_data():
    """Check attendance records and their check-out times"""
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Get recent attendance records
            cursor.execute("""
                SELECT id, student_number, pc_number, 
                       check_in_time, check_out_time, 
                       room_number, class_session_id
                FROM student_attendance 
                ORDER BY check_in_time DESC 
                LIMIT 10
            """)
            
            records = cursor.fetchall()
            
            print("Recent attendance records:")
            print("=" * 100)
            
            for record in records:
                checkout_status = "✓ Checked out" if record['check_out_time'] else "× Not checked out"
                print(f"ID: {record['id']}")
                print(f"  Student: {record['student_number']}")
                print(f"  PC: {record['pc_number']}")
                print(f"  Check-in: {record['check_in_time']}")
                print(f"  Check-out: {record['check_out_time']} ({checkout_status})")
                print(f"  Room: {record['room_number']}")
                print(f"  Session: {record['class_session_id']}")
                print("-" * 50)
                
            # Count records without check-out time
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM student_attendance 
                WHERE check_out_time IS NULL
            """)
            
            no_checkout = cursor.fetchone()
            print(f"\nTotal records without check-out time: {no_checkout['count']}")
                
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nMySQL connection is closed")

if __name__ == "__main__":
    check_attendance_data()
