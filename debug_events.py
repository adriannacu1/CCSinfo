#!/usr/bin/env python3
"""
Debug script to check events in the database
"""

import mysql.connector
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Your MySQL password
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def check_events():
    """Check events in the database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Check all events
        print("=== ALL EVENTS ===")
        cursor.execute("SELECT event_id, title, event_date, status FROM events ORDER BY event_id")
        all_events = cursor.fetchall()
        
        if not all_events:
            print("No events found in database!")
            return
        
        for event in all_events:
            print(f"ID: {event['event_id']}, Title: {event['title']}, Date: {event['event_date']}, Status: {event['status']}")
        
        print(f"\nTotal events: {len(all_events)}")
        
        # Check upcoming events only
        print("\n=== UPCOMING EVENTS ===")
        cursor.execute("""
            SELECT event_id, title, event_date, status 
            FROM events 
            WHERE event_date >= CURDATE() AND status = 'upcoming'
            ORDER BY event_date ASC
        """)
        upcoming_events = cursor.fetchall()
        
        if not upcoming_events:
            print("No upcoming events found!")
        else:
            for event in upcoming_events:
                print(f"ID: {event['event_id']}, Title: {event['title']}, Date: {event['event_date']}, Status: {event['status']}")
            print(f"\nTotal upcoming events: {len(upcoming_events)}")
        
        # Check event speakers
        print("\n=== EVENT SPEAKERS ===")
        cursor.execute("SELECT event_id, name, role FROM event_speakers ORDER BY event_id")
        speakers = cursor.fetchall()
        
        if not speakers:
            print("No event speakers found!")
        else:
            print(f"Total speakers: {len(speakers)}")
            for speaker in speakers:
                print(f"Event ID: {speaker['event_id']}, Speaker: {speaker['name']}, Role: {speaker['role']}")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_events()
