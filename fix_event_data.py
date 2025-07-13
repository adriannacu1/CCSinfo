#!/usr/bin/env python3
"""
Check and fix event data in database
"""

import mysql.connector

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def check_and_fix_data():
    """Check and fix data corruption"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Check event 1 specifically
        cursor.execute("SELECT * FROM events WHERE event_id = 1")
        event = cursor.fetchone()
        
        print("Event 1 data:")
        print(f"Title: {event['title']}")
        print(f"Description: {repr(event['description'])}")
        print(f"Location: {event['location']}")
        print(f"Event time: {event['event_time']}")
        print()
        
        # Check speakers for event 1
        cursor.execute("SELECT * FROM event_speakers WHERE event_id = 1")
        speakers = cursor.fetchall()
        
        print("Speakers for event 1:")
        for speaker in speakers:
            print(f"ID: {speaker['speaker_id']}, Name: {repr(speaker['name'])}, Role: {repr(speaker['role'])}")
        print()
        
        # Let's update event 1 with clean data
        clean_description = "Join industry leaders as we explore the latest advances in artificial intelligence and machine learning technologies. Learn from top researchers and practitioners about cutting-edge applications in healthcare, finance, and autonomous systems."
        
        cursor.execute("""
            UPDATE events 
            SET description = %s 
            WHERE event_id = 1
        """, (clean_description,))
        
        # Clean up speakers data
        cursor.execute("DELETE FROM event_speakers WHERE event_id = 1")
        
        # Insert clean speaker data
        speakers_data = [
            (1, 'Dr. Sarah Chen', 'AI Research Director at TechCorp', 'Leading researcher in machine learning with 15+ years of experience.', None),
            (1, 'Prof. Michael Rodriguez', 'Stanford University', 'Professor of Computer Science specializing in AI ethics.', None),
            (1, 'Emma Watson', 'ML Engineer at Google', 'Senior machine learning engineer working on Google AI projects.', None)
        ]
        
        cursor.executemany("""
            INSERT INTO event_speakers (event_id, name, role, bio, avatar)
            VALUES (%s, %s, %s, %s, %s)
        """, speakers_data)
        
        connection.commit()
        print("Data cleaned up successfully!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_and_fix_data()
