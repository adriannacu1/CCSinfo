#!/usr/bin/env python3
"""
Create a simple HTML file to show what our data looks like
"""

import mysql.connector
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def create_test_html():
    """Create a test HTML file showing our events data"""
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get upcoming events using our exact query
        cursor.execute("""
            SELECT * FROM events e
            WHERE e.event_date >= CURDATE() AND e.status = 'upcoming'
            ORDER BY e.event_date ASC, e.event_time ASC
        """)
        events = cursor.fetchall()
        
        # Start building HTML
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>CCS Events Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .event { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .event-title { color: #333; margin: 0 0 10px 0; }
        .event-meta { color: #666; font-size: 14px; }
        .speakers { margin-top: 10px; }
        .speaker { background: #f5f5f5; padding: 5px; margin: 2px 0; border-radius: 3px; }
        .no-events { text-align: center; color: #999; padding: 50px; }
    </style>
</head>
<body>
    <h1>CCS Events Test Page</h1>
    <p>This page shows what events are found in the database</p>
    <hr>
"""
        
        if events:
            html_content += f"<h2>Found {len(events)} Upcoming Events:</h2>\n"
            
            for event in events:
                # Get speakers for this event
                cursor.execute("""
                    SELECT name, role FROM event_speakers 
                    WHERE event_id = %s
                    ORDER BY speaker_id
                """, (event['event_id'],))
                speakers = cursor.fetchall()
                
                # Format time
                time_str = "TBA"
                if event.get('event_time'):
                    if hasattr(event['event_time'], 'seconds'):
                        total_seconds = event['event_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        time_str = f"{hours:02d}:{minutes:02d}"
                    else:
                        time_str = str(event['event_time'])
                
                html_content += f"""
    <div class="event">
        <h3 class="event-title">{event['title']}</h3>
        <div class="event-meta">
            <strong>Date:</strong> {event['event_date']}<br>
            <strong>Time:</strong> {time_str}<br>
            <strong>Location:</strong> {event.get('location', 'TBA')}<br>
            <strong>Category:</strong> {event.get('category', 'General')}<br>
            <strong>Status:</strong> {event.get('status', 'Unknown')}
        </div>
        <p><strong>Description:</strong> {event.get('description', 'No description available')}</p>
"""
                
                if speakers:
                    html_content += "        <div class='speakers'><strong>Speakers:</strong><br>\n"
                    for speaker in speakers:
                        html_content += f"            <div class='speaker'>{speaker['name']} - {speaker['role']}</div>\n"
                    html_content += "        </div>\n"
                
                html_content += "    </div>\n"
        
        else:
            html_content += """
    <div class="no-events">
        <h2>No Upcoming Events Found</h2>
        <p>The database query returned no results.</p>
        <p>This is why the events page shows "No Events Found".</p>
    </div>
"""
        
        html_content += """
    <hr>
    <h2>Debug Information:</h2>
    <p><strong>Current Date:</strong> """ + str(datetime.now().date()) + """</p>
    <p><strong>Query Used:</strong> SELECT * FROM events WHERE event_date >= CURDATE() AND status = 'upcoming'</p>
</body>
</html>
"""
        
        # Save the HTML file
        with open('events_test.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        cursor.close()
        conn.close()
        
        print(f"✅ Created events_test.html with {len(events) if events else 0} events")
        print("📁 Open events_test.html in your browser to see the results")
        
        return len(events) if events else 0
        
    except Exception as e:
        print(f"❌ Error creating test HTML: {e}")
        import traceback
        print(traceback.format_exc())
        return -1

if __name__ == '__main__':
    create_test_html()
