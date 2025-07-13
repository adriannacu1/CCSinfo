#!/usr/bin/env python3

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

# Simple test
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("=== EVENTS TEST RESULTS ===")
    print(f"Today's date: {date.today()}")
    
    # Test 1: Count all events
    cursor.execute("SELECT COUNT(*) as count FROM events")
    total = cursor.fetchone()['count']
    print(f"Total events in database: {total}")
    
    # Test 2: Count upcoming events
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE status = 'upcoming'")
    upcoming_status = cursor.fetchone()['count']
    print(f"Events with 'upcoming' status: {upcoming_status}")
    
    # Test 3: Count future events
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_date >= CURDATE()")
    future_date = cursor.fetchone()['count']
    print(f"Events with future dates: {future_date}")
    
    # Test 4: Our exact query
    cursor.execute("""
        SELECT COUNT(*) as count FROM events 
        WHERE event_date >= CURDATE() AND status = 'upcoming'
    """)
    exact_match = cursor.fetchone()['count']
    print(f"Events matching our exact criteria: {exact_match}")
    
    # Test 5: List all events with their dates and status
    cursor.execute("SELECT event_id, title, event_date, status FROM events ORDER BY event_date")
    all_events = cursor.fetchall()
    
    print("\nAll events in database:")
    for event in all_events:
        is_future = event['event_date'] >= date.today() if event['event_date'] else False
        is_upcoming = event['status'] == 'upcoming'
        matches = is_future and is_upcoming
        
        print(f"  ID {event['event_id']}: {event['title']}")
        print(f"    Date: {event['event_date']} (Future: {is_future})")
        print(f"    Status: {event['status']} (Upcoming: {is_upcoming})")
        print(f"    Matches criteria: {matches}")
        print()
    
    cursor.close()
    conn.close()
    
    # Write results to a file
    with open('debug_results.txt', 'w') as f:
        f.write(f"Events Test Results - {datetime.now()}\n")
        f.write("="*50 + "\n")
        f.write(f"Today's date: {date.today()}\n")
        f.write(f"Total events: {total}\n")
        f.write(f"Events with 'upcoming' status: {upcoming_status}\n")
        f.write(f"Events with future dates: {future_date}\n")
        f.write(f"Events matching exact criteria: {exact_match}\n\n")
        
        f.write("All events:\n")
        for event in all_events:
            is_future = event['event_date'] >= date.today() if event['event_date'] else False
            is_upcoming = event['status'] == 'upcoming'
            matches = is_future and is_upcoming
            
            f.write(f"ID {event['event_id']}: {event['title']}\n")
            f.write(f"  Date: {event['event_date']} (Future: {is_future})\n")
            f.write(f"  Status: {event['status']} (Upcoming: {is_upcoming})\n")
            f.write(f"  Matches: {matches}\n\n")
        
        if exact_match == 0:
            f.write("\nCONCLUSION: No events match the criteria!\n")
            f.write("This is why the events page shows 'No Events Found'.\n")
        else:
            f.write(f"\nCONCLUSION: {exact_match} events should be showing.\n")
    
    print(f"\nResults saved to debug_results.txt")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    print(traceback.format_exc())
