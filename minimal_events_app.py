#!/usr/bin/env python3
"""
Minimal Flask app to test events specifically
"""

from flask import Flask, render_template, jsonify
import mysql.connector
from datetime import datetime
import traceback
import os

# Create Flask app
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return '<h1>Test Server Running</h1><p><a href="/events">Go to Events Page</a></p><p><a href="/test">Test Database</a></p>'

@app.route('/test')
def test_db():
    """Test database connection and data"""
    conn = get_db_connection()
    if not conn:
        return "Database connection failed"
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM events WHERE status = 'upcoming'")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return f"Database connection successful! Found {result['count']} upcoming events."
    except Exception as e:
        return f"Database test failed: {str(e)}"

@app.route('/events')
def events_page():
    """Events page"""
    print("=== Events route called ===")
    
    conn = get_db_connection()
    events = []
    event_counts = {}
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("Querying upcoming events...")
            # Get upcoming events
            cursor.execute("""
                SELECT * FROM events e
                WHERE e.event_date >= CURDATE() AND e.status = 'upcoming'
                ORDER BY e.event_date ASC, e.event_time ASC
            """)
            events_raw = cursor.fetchall()
            print(f"Found {len(events_raw)} upcoming events")
            
            # Process events and get speakers for each
            for event in events_raw:
                print(f"Processing event: {event['title']}")
                
                # Get speakers for this event
                cursor.execute("""
                    SELECT name, role, bio, avatar 
                    FROM event_speakers 
                    WHERE event_id = %s
                    ORDER BY speaker_id
                """, (event['event_id'],))
                speakers_raw = cursor.fetchall()
                
                # Convert speakers to list of dictionaries
                speakers = []
                for speaker in speakers_raw:
                    speakers.append({
                        'name': speaker['name'],
                        'role': speaker['role'],
                        'bio': speaker['bio'] if speaker['bio'] else None,
                        'avatar': speaker['avatar'] if speaker['avatar'] else None
                    })
                
                event['speakers'] = speakers
                
                # Format time
                if event.get('event_time') and hasattr(event['event_time'], 'seconds'):
                    total_seconds = event['event_time'].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    event['event_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                elif event.get('event_time'):
                    event['event_time_formatted'] = str(event['event_time'])
                else:
                    event['event_time_formatted'] = "TBA"
                
                # Format end time
                if event.get('end_time') and hasattr(event['end_time'], 'seconds'):
                    total_seconds = event['end_time'].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    event['end_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                elif event.get('end_time'):
                    event['end_time_formatted'] = str(event['end_time'])
                else:
                    event['end_time_formatted'] = None
                
                events.append(event)
                print(f"  Added event with {len(speakers)} speakers")
            
            # Get event counts by category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM events
                WHERE event_date >= CURDATE() AND status = 'upcoming'
                GROUP BY category
            """)
            counts_raw = cursor.fetchall()
            for count_row in counts_raw:
                event_counts[count_row['category']] = count_row['count']
            
            cursor.close()
            conn.close()
            
            print(f"Final: Passing {len(events)} events to template")
            
        except Exception as e:
            print(f"Error fetching events: {e}")
            print(traceback.format_exc())
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return render_template('events.html', events=events, event_counts=event_counts)

@app.route('/api/events/<int:event_id>')
def get_event_details(event_id):
    """API endpoint to get detailed event information"""
    print(f"API request for event ID: {event_id}")
    
    conn = get_db_connection()
    
    if not conn:
        print("Database connection failed")
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get event details first
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': f'Event with ID {event_id} not found'}), 404
        
        # Get speakers separately
        cursor.execute("""
            SELECT name, role, bio, avatar 
            FROM event_speakers 
            WHERE event_id = %s
            ORDER BY speaker_id
        """, (event_id,))
        speakers_raw = cursor.fetchall()
        
        # Convert speakers to list of dictionaries
        speakers = []
        for speaker in speakers_raw:
            speakers.append({
                'name': speaker['name'],
                'role': speaker['role'],
                'bio': speaker['bio'] if speaker['bio'] else None,
                'avatar': speaker['avatar'] if speaker['avatar'] else None
            })
        
        event['speakers'] = speakers
        
        print(f"Query result: Event '{event['title']}' with {len(speakers)} speakers")
        
        # Format time fields
        if event.get('event_time'):
            if hasattr(event['event_time'], 'seconds'):
                total_seconds = event['event_time'].seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                event['event_time_formatted'] = f"{hours:02d}:{minutes:02d}"
            else:
                try:
                    event['event_time_formatted'] = str(event['event_time'])
                except:
                    event['event_time_formatted'] = "TBA"
        else:
            event['event_time_formatted'] = "TBA"
        
        if event.get('end_time'):
            if hasattr(event['end_time'], 'seconds'):
                total_seconds = event['end_time'].seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                event['end_time_formatted'] = f"{hours:02d}:{minutes:02d}"
            else:
                try:
                    event['end_time_formatted'] = str(event['end_time'])
                except:
                    event['end_time_formatted'] = None
        else:
            event['end_time_formatted'] = None
        
        # Format date
        if event.get('event_date'):
            try:
                if hasattr(event['event_date'], 'strftime'):
                    event['event_date_formatted'] = event['event_date'].strftime('%B %d, %Y')
                else:
                    event['event_date_formatted'] = str(event['event_date'])
            except:
                event['event_date_formatted'] = str(event['event_date'])
        else:
            event['event_date_formatted'] = "Date TBA"
        
        cursor.close()
        conn.close()
        
        print(f"Successfully returning event data for ID: {event_id}")
        return jsonify({'success': True, 'event': event})
        
    except Exception as e:
        print(f"Error loading event details for ID {event_id}: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'success': False, 'message': f'Error loading event details: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting minimal Flask app for events testing...")
    print("Visit http://127.0.0.1:5000/events to see the events page")
    print("Visit http://127.0.0.1:5000/test to test database connection")
    app.run(debug=True, host='127.0.0.1', port=5000)
