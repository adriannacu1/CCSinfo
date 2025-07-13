#!/usr/bin/env python3
"""
Comprehensive test to understand what's happening with events
"""

import mysql.connector
from datetime import datetime, date

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def main():
    print("=== Comprehensive Events Test ===\n")
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("✅ Database connection successful\n")
        
        # 1. Check current date
        print("1. Current Date Information:")
        print(f"   Today: {date.today()}")
        print(f"   Now: {datetime.now()}")
        
        # 2. Check all events in database
        print("\n2. All Events in Database:")
        cursor.execute("SELECT event_id, title, event_date, status FROM events ORDER BY event_id")
        all_events = cursor.fetchall()
        print(f"   Total events in database: {len(all_events)}")
        
        for event in all_events:
            print(f"   - ID {event['event_id']}: {event['title']}")
            print(f"     Date: {event['event_date']}, Status: {event['status']}")
        
        # 3. Check CURDATE() function
        print("\n3. Database Current Date:")
        cursor.execute("SELECT CURDATE() as current_date, NOW() as current_datetime")
        db_dates = cursor.fetchone()
        print(f"   CURDATE(): {db_dates['current_date']}")
        print(f"   NOW(): {db_dates['current_datetime']}")
        
        # 4. Test our exact query
        print("\n4. Testing Our Exact Query:")
        query = """
            SELECT * FROM events e
            WHERE e.event_date >= CURDATE() AND e.status = 'upcoming'
            ORDER BY e.event_date ASC, e.event_time ASC
        """
        print(f"   Query: {query}")
        
        cursor.execute(query)
        upcoming_events = cursor.fetchall()
        print(f"   Results: {len(upcoming_events)} upcoming events")
        
        for event in upcoming_events:
            print(f"   - Event ID {event['event_id']}: {event['title']}")
            print(f"     Date: {event['event_date']}")
            print(f"     Time: {event['event_time']}")
            print(f"     Status: {event['status']}")
            print(f"     Category: {event['category']}")
            
            # Check speakers
            cursor.execute("SELECT COUNT(*) as count FROM event_speakers WHERE event_id = %s", (event['event_id'],))
            speaker_count = cursor.fetchone()['count']
            print(f"     Speakers: {speaker_count}")
            print()
        
        # 5. Test different date comparisons
        print("5. Testing Date Comparisons:")
        
        # Test >= CURDATE()
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_date >= CURDATE()")
        future_count = cursor.fetchone()['count']
        print(f"   Events with date >= CURDATE(): {future_count}")
        
        # Test status = 'upcoming'
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE status = 'upcoming'")
        upcoming_count = cursor.fetchone()['count']
        print(f"   Events with status = 'upcoming': {upcoming_count}")
        
        # Combined
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_date >= CURDATE() AND status = 'upcoming'")
        combined_count = cursor.fetchone()['count']
        print(f"   Events matching both conditions: {combined_count}")
        
        # 6. Check event categories
        print("\n6. Event Categories:")
        cursor.execute("SELECT DISTINCT category FROM events")
        categories = cursor.fetchall()
        for cat in categories:
            print(f"   - {cat['category']}")
        
        # 7. Final diagnosis
        print("\n7. Diagnosis:")
        if len(upcoming_events) == 0:
            print("   ❌ No upcoming events found - this explains the empty events page!")
            print("   📋 Possible reasons:")
            print("      - All events have dates in the past")
            print("      - Events don't have status 'upcoming'")
            print("      - Events exist but don't match the filter criteria")
        else:
            print(f"   ✅ Found {len(upcoming_events)} upcoming events")
            print("   📋 Events should be displaying properly")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    main()
