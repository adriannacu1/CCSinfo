#!/usr/bin/env python3
"""
Add more sample events with proper categories
"""

import mysql.connector
from datetime import datetime, timedelta

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def add_sample_events():
    """Add more sample events with different categories"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Update existing events to have proper categories
        updates = [
            (1, 'conference'),
            (2, 'workshop'),
            (3, 'workshop'),
            (4, 'seminar'),
            (5, 'hackathon'),
            (6, 'networking'),
            (7, 'seminar'),
            (8, 'conference')
        ]
        
        for event_id, category in updates:
            cursor.execute("UPDATE events SET category = %s WHERE event_id = %s", (category, event_id))
        
        print("Updated event categories")
        
        # Check if we need to add more events
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_date >= CURDATE() AND status = 'upcoming'")
        result = cursor.fetchone()
        upcoming_count = result[0]
        
        print(f"Current upcoming events: {upcoming_count}")
        
        if upcoming_count < 3:
            # Add more upcoming events
            future_date = datetime.now() + timedelta(days=30)
            
            new_events = [
                ("Python Programming Workshop", "Learn Python programming from basics to advanced concepts", 
                 future_date.strftime('%Y-%m-%d'), "10:00:00", "17:00:00", "CCS Lab 1", "workshop", "upcoming", 0),
                ("Industry Tech Talk", "Leading tech companies share their latest innovations", 
                 (future_date + timedelta(days=7)).strftime('%Y-%m-%d'), "14:00:00", "16:00:00", "CCS Auditorium", "seminar", "upcoming", 0),
            ]
            
            cursor.executemany("""
                INSERT INTO events (title, description, event_date, event_time, end_time, location, category, status, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, new_events)
            
            print(f"Added {len(new_events)} new events")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Sample events updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_sample_events()
