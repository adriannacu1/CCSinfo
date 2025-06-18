#!/usr/bin/env python3
"""
Script to add check_out_time column to student_attendance table if it doesn't exist
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

def check_and_add_checkout_column():
    """Check if check_out_time column exists and add it if not"""
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Check if column exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'ccs_info' 
                AND TABLE_NAME = 'student_attendance' 
                AND COLUMN_NAME = 'check_out_time'
            """)
            
            result = cursor.fetchone()
            
            if result:
                print("✓ check_out_time column already exists in student_attendance table")
            else:
                print("× check_out_time column does not exist. Adding it now...")
                
                # Add the column
                cursor.execute("""
                    ALTER TABLE student_attendance 
                    ADD COLUMN check_out_time DATETIME NULL DEFAULT NULL 
                    AFTER check_in_time
                """)
                
                connection.commit()
                print("✓ check_out_time column added successfully!")
            
            # Show the table structure
            cursor.execute("DESCRIBE student_attendance")
            columns = cursor.fetchall()
            
            print("\nCurrent student_attendance table structure:")
            for column in columns:
                print(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]} - {column[5]}")
                
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nMySQL connection is closed")

if __name__ == "__main__":
    check_and_add_checkout_column()
