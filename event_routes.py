# Event Management API Routes
from flask import render_template, request, redirect, url_for, session, flash, jsonify

def register_event_routes(app, get_db_connection):
    """Register event management routes with the app"""
    
    @app.route('/api/events')
    def api_get_events():
        """API endpoint to get events with filtering and pagination"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            # Build the WHERE clause
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("(title LIKE %s OR description LIKE %s OR location LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if category:
                where_conditions.append("category = %s")
                params.append(category)
            
            if status:
                where_conditions.append("status = %s")
                params.append(status)
            
            if date_from:
                where_conditions.append("event_date >= %s")
                params.append(date_from)
            
            if date_to:
                where_conditions.append("event_date <= %s")
                params.append(date_to)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM events {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Get events with pagination
            offset = (page - 1) * per_page
            events_query = f"""
                SELECT e.*, a.full_name as created_by_name,
                       COALESCE(speaker_count.count, 0) as speaker_count
                FROM events e
                LEFT JOIN admin a ON e.created_by = a.admin_id
                LEFT JOIN (
                    SELECT event_id, COUNT(*) as count 
                    FROM event_speakers 
                    GROUP BY event_id
                ) speaker_count ON e.event_id = speaker_count.event_id
                {where_clause}
                ORDER BY e.event_date DESC, e.event_time DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(events_query, params + [per_page, offset])
            events = cursor.fetchall()
            
            # Format dates and times for display
            for event in events:
                if event['event_date']:
                    event['event_date'] = event['event_date'].strftime('%Y-%m-%d')
                if event['event_time']:
                    event['event_time'] = event['event_time'].strftime('%H:%M')
                if event['end_time']:
                    event['end_time'] = event['end_time'].strftime('%H:%M')
                if event['created_at']:
                    event['created_at'] = event['created_at'].strftime('%Y-%m-%d %H:%M')
            
            return jsonify({
                'events': events,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events/stats')
    def api_get_event_stats():
        """API endpoint to get event statistics"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get event statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_events,
                    SUM(CASE WHEN status = 'upcoming' THEN 1 ELSE 0 END) as upcoming_events,
                    SUM(CASE WHEN status = 'ongoing' THEN 1 ELSE 0 END) as ongoing_events,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_events,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_events,
                    SUM(current_attendees) as total_registrations,
                    SUM(price * current_attendees) as total_revenue
                FROM events
            """
            cursor.execute(stats_query)
            stats = cursor.fetchone()
            
            return jsonify(stats)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events', methods=['POST'])
    def api_create_event():
        """API endpoint to create a new event"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor()
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['title', 'description', 'category', 'event_date', 'event_time', 'location']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Insert event
            insert_query = """
                INSERT INTO events (title, description, category, event_date, event_time, end_time, 
                                  location, price, max_attendees, status, featured_image, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                data['title'],
                data['description'],
                data['category'],
                data['event_date'],
                data['event_time'],
                data.get('end_time'),
                data['location'],
                data.get('price', 0.00),
                data.get('max_attendees'),
                data.get('status', 'upcoming'),
                data.get('featured_image'),
                session['admin_id']
            ))
            
            event_id = cursor.lastrowid
            
            # Insert speakers if provided
            if data.get('speakers'):
                for speaker in data['speakers']:
                    speaker_query = """
                        INSERT INTO event_speakers (event_id, name, role, bio, avatar)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(speaker_query, (
                        event_id,
                        speaker['name'],
                        speaker['role'],
                        speaker.get('bio', ''),
                        speaker.get('avatar', '')
                    ))
            
            connection.commit()
            return jsonify({'success': True, 'event_id': event_id, 'message': 'Event created successfully'})
            
        except Exception as e:
            connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events/<int:event_id>', methods=['PUT'])
    def api_update_event(event_id):
        """API endpoint to update an event"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor()
            data = request.get_json()
            
            # Update event
            update_query = """
                UPDATE events SET title = %s, description = %s, category = %s, event_date = %s,
                                event_time = %s, end_time = %s, location = %s, price = %s,
                                max_attendees = %s, status = %s, featured_image = %s,
                                updated_at = CURRENT_TIMESTAMP
                WHERE event_id = %s
            """
            cursor.execute(update_query, (
                data['title'],
                data['description'],
                data['category'],
                data['event_date'],
                data['event_time'],
                data.get('end_time'),
                data['location'],
                data.get('price', 0.00),
                data.get('max_attendees'),
                data.get('status', 'upcoming'),
                data.get('featured_image'),
                event_id
            ))
            
            # Update speakers if provided
            if 'speakers' in data:
                # Delete existing speakers
                cursor.execute("DELETE FROM event_speakers WHERE event_id = %s", (event_id,))
                
                # Insert new speakers
                for speaker in data['speakers']:
                    speaker_query = """
                        INSERT INTO event_speakers (event_id, name, role, bio, avatar)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(speaker_query, (
                        event_id,
                        speaker['name'],
                        speaker['role'],
                        speaker.get('bio', ''),
                        speaker.get('avatar', '')
                    ))
            
            connection.commit()
            return jsonify({'success': True, 'message': 'Event updated successfully'})
            
        except Exception as e:
            connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events/<int:event_id>', methods=['DELETE'])
    def api_delete_event(event_id):
        """API endpoint to delete an event"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor()
            
            # Delete speakers first (foreign key constraint)
            cursor.execute("DELETE FROM event_speakers WHERE event_id = %s", (event_id,))
            
            # Delete event
            cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Event not found'}), 404
            
            connection.commit()
            return jsonify({'success': True, 'message': 'Event deleted successfully'})
            
        except Exception as e:
            connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events/<int:event_id>')
    def api_get_event(event_id):
        """API endpoint to get a single event with speakers"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get event details
            event_query = """
                SELECT e.*, a.full_name as created_by_name
                FROM events e
                LEFT JOIN admin a ON e.created_by = a.admin_id
                WHERE e.event_id = %s
            """
            cursor.execute(event_query, (event_id,))
            event = cursor.fetchone()
            
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
            # Get event speakers
            cursor.execute("SELECT * FROM event_speakers WHERE event_id = %s", (event_id,))
            speakers = cursor.fetchall()
            
            # Format dates and times
            if event['event_date']:
                event['event_date'] = event['event_date'].strftime('%Y-%m-%d')
            if event['event_time']:
                event['event_time'] = event['event_time'].strftime('%H:%M')
            if event['end_time']:
                event['end_time'] = event['end_time'].strftime('%H:%M')
            if event['created_at']:
                event['created_at'] = event['created_at'].strftime('%Y-%m-%d %H:%M')
            
            event['speakers'] = speakers
            
            return jsonify(event)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events/bulk-action', methods=['POST'])
    def api_bulk_event_action():
        """API endpoint for bulk actions on events"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            cursor = connection.cursor()
            data = request.get_json()
            
            action = data.get('action')
            event_ids = data.get('event_ids', [])
            
            if not action or not event_ids:
                return jsonify({'error': 'Action and event IDs are required'}), 400
            
            # Convert to list of integers
            event_ids = [int(id) for id in event_ids]
            placeholders = ','.join(['%s'] * len(event_ids))
            
            if action == 'delete':
                # Delete speakers first
                cursor.execute(f"DELETE FROM event_speakers WHERE event_id IN ({placeholders})", event_ids)
                # Delete events
                cursor.execute(f"DELETE FROM events WHERE event_id IN ({placeholders})", event_ids)
                message = f'{cursor.rowcount} events deleted successfully'
                
            elif action == 'change_status':
                new_status = data.get('new_status')
                if not new_status:
                    return jsonify({'error': 'New status is required'}), 400
                
                cursor.execute(f"UPDATE events SET status = %s WHERE event_id IN ({placeholders})", 
                             [new_status] + event_ids)
                message = f'{cursor.rowcount} events updated successfully'
                
            else:
                return jsonify({'error': 'Invalid action'}), 400
            
            connection.commit()
            return jsonify({'success': True, 'message': message})
            
        except Exception as e:
            connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    
    @app.route('/api/events/export')
    def api_export_events():
        """API endpoint to export events as CSV"""
        if 'admin_logged_in' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection error'}), 500
        
        try:
            from flask import make_response
            import csv
            import io
            
            cursor = connection.cursor(dictionary=True)
            
            # Get query parameters for filtering
            search = request.args.get('search', '')
            category = request.args.get('category', '')
            status = request.args.get('status', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            
            # Build the WHERE clause
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("(title LIKE %s OR description LIKE %s OR location LIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if category:
                where_conditions.append("category = %s")
                params.append(category)
            
            if status:
                where_conditions.append("status = %s")
                params.append(status)
            
            if date_from:
                where_conditions.append("event_date >= %s")
                params.append(date_from)
            
            if date_to:
                where_conditions.append("event_date <= %s")
                params.append(date_to)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get events for export
            export_query = f"""
                SELECT e.title, e.description, e.category, e.event_date, e.event_time, e.end_time,
                       e.location, e.price, e.max_attendees, e.current_attendees, e.status,
                       a.full_name as created_by, e.created_at
                FROM events e
                LEFT JOIN admin a ON e.created_by = a.admin_id
                {where_clause}
                ORDER BY e.event_date DESC, e.event_time DESC
            """
            cursor.execute(export_query, params)
            events = cursor.fetchall()
            
            # Create CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'title', 'description', 'category', 'event_date', 'event_time', 'end_time',
                'location', 'price', 'max_attendees', 'current_attendees', 'status',
                'created_by', 'created_at'
            ])
            
            writer.writeheader()
            for event in events:
                # Format dates for CSV
                if event['event_date']:
                    event['event_date'] = event['event_date'].strftime('%Y-%m-%d')
                if event['event_time']:
                    event['event_time'] = event['event_time'].strftime('%H:%M')
                if event['end_time']:
                    event['end_time'] = event['end_time'].strftime('%H:%M')
                if event['created_at']:
                    event['created_at'] = event['created_at'].strftime('%Y-%m-%d %H:%M')
                writer.writerow(event)
            
            # Create response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=events_export.csv'
            
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
