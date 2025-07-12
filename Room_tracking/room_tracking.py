from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
import pymysql
import time
from datetime import datetime
import datetime as dt

app = Flask(__name__)
app.secret_key = 'CCS-2025-SecretKey'
CORS(app)

room_status = {
    'in_use': False,
    'faculty_id': None,
    'faculty_name': None,
    'start_time': None
}

def get_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='ccs_info',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    room_id = request.args.get('room_id')
    
    if not room_id:
        return render_template('select_room.html')

    connection = get_db_connection()
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM room_controllers WHERE room_id = %s", (room_id,))
            if not cursor.fetchone():
                return render_template('select_room.html', error=f"Room {room_id} not found")
        connection.close()
        
    return render_template('rfid_dashboard.html', room_id=room_id)

@app.route('/room_in_use')
def room_in_use():
    room_id = session.get('current_room_id')

    if not room_status['in_use']:
        return redirect(url_for('index', room_id=room_id))
    
    has_class = session.get('has_class', False)
    class_status = session.get('class_status')
        
    return render_template('room_in_use.html', 
                          faculty_name=room_status['faculty_name'],
                          start_time=room_status['start_time'],
                          room_id=room_id,
                          has_class=has_class,
                          class_status=class_status)

@app.route('/api/validate_rfid', methods=['POST'])
def validate_rfid():
    rfid_code = request.form.get('rfid_code') 
    room_id = int(request.form.get('room_id', 0))
    
    session['current_room_id'] = room_id
    
    if not rfid_code:
        return jsonify({'status': 'error', 'message': 'No RFID code provided'})
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM room_controllers WHERE room_id = %s", (room_id,))
            room = cursor.fetchone()
            
            if not room:
                print(f"Room {room_id} not found in database")
                return jsonify({
                    'status': 'error',
                    'message': f'Room {room_id} does not exist'
                })
            
            sql = "SELECT * FROM faculty WHERE rfid_code = %s"
            cursor.execute(sql, (rfid_code,))
            faculty = cursor.fetchone()
            
            if faculty:
                room_status['in_use'] = True
                room_status['faculty_id'] = faculty['faculty_id']
                room_status['faculty_name'] = faculty['name']
                room_status['start_time'] = datetime.now()
                
                schedule_status = check_faculty_schedule(faculty['faculty_id'], room_id)
                
                if schedule_status in ["scheduled_now", "scheduled_soon"]:
                    status_message = "TEACHING"
                    access_status = "In Class Session"
                else:
                    status_message = "CURRENTLY IN ROOM"
                    access_status = "Room Access"
                
                # Update faculty status
                update_sql = "UPDATE faculty SET status_state = %s WHERE faculty_id = %s"
                cursor.execute(update_sql, (status_message, faculty['faculty_id']))
                
                # Create a new access log with time_in set and time_out as NULL
                log_sql = """
                    INSERT INTO access_logs 
                    (faculty_id, room_id, time_in, status) 
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(log_sql, (
                    faculty['faculty_id'], 
                    room_id,
                    datetime.now(),
                    access_status
                ))

                # Store the log_id in session for later use
                log_id = cursor.lastrowid
                session['current_log_id'] = log_id
                print(f"Created access log: ID={log_id} for faculty {faculty['faculty_id']} in room {room_id}")

                connection.commit()
                
                esp32_success = send_command_to_esp32(room_id, "ON")

                if esp32_success:
                    if schedule_status:
                        session['has_class'] = True
                        session['class_status'] = "now" if schedule_status == "scheduled_now" else "soon"
                    else:
                        session['has_class'] = False
                    
                    return jsonify({
                        'status': 'success',
                        'faculty_id': faculty['faculty_id'],
                        'faculty_name': faculty['name'],
                        'has_class': bool(schedule_status),
                        'message': 'Access granted'
                    })
                else:
                    cursor.execute("UPDATE faculty SET status_state = 'AVAILABLE' WHERE faculty_id = %s", 
                                   (faculty['faculty_id'],))
                    connection.commit()
                    
                    return jsonify({
                        'status': 'error',
                        'message': 'Door communication error. Please try again or contact support.'
                    })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid RFID code'
                })
    except Exception as e:
        print(f"Error validating RFID: {e}")
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})
    finally:
        if connection:
            connection.close()

@app.route('/reset_room', methods=['POST'])
def reset_room():
    faculty_id = room_status.get('faculty_id')
    room_id = request.json.get('room_id')
    log_id = session.get('current_log_id')
    
    if not room_id:
        return jsonify({'status': 'error', 'message': 'No room_id provided'})
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM room_controllers WHERE room_id = %s", (room_id,))
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': f'Room {room_id} does not exist'})
            
            if faculty_id and log_id:
                update_sql = "UPDATE faculty SET status_state = 'AVAILABLE' WHERE faculty_id = %s"
                cursor.execute(update_sql, (faculty_id,))

                log_sql = """
                    UPDATE access_logs 
                    SET time_out = %s, status = %s
                    WHERE log_id = %s
                """
                cursor.execute(log_sql, (datetime.now(), "Available", log_id))
                
                connection.commit()
                print(f"Updated log {log_id} with exit time for faculty {faculty_id}")
                
        room_status['in_use'] = False
        room_status['faculty_id'] = None
        room_status['faculty_name'] = None
        room_status['start_time'] = None
        
        session.pop('has_class', None)
        session.pop('class_status', None)

        send_command_to_esp32(room_id, "OFF")
        print(f"Door lock command sent to room {room_id}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Room status reset', 
            'redirect': f'/?room_id={room_id}'
        })
        
    except Exception as e:
        print(f"Error in reset_room: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})
    finally:
        if connection:
            connection.close()

@app.route('/api/esp32/test', methods=['GET', 'POST'])
def test_esp32_connection():
    if request.method == 'POST':
        data = request.get_json() or {}
        return jsonify({'status': 'success', 'message': 'Flask received ESP32 POST!', 'data': data})
    else:
        return jsonify({
            'status': 'success', 
            'message': 'Flask server is running and accessible from ESP32!',
            'timestamp': time.time(),
            'server_ip': '192.168.1.9'
        })

@app.route('/api/lock/control', methods=['POST'])
def control_lock():
    data = request.get_json()
    action = data.get('action')
    room_id = data.get('room_id', 1)
    
    if not action or action not in ['lock', 'unlock']:
        return jsonify({'status': 'error', 'message': 'Invalid action'})
    
    try:
        print(f"Lock control: {action} for room {room_id}")
        
        command = "ON" if action == 'lock' else "OFF"
        
        response = send_command_to_esp32(room_id, command)
        
        if response:
            return jsonify({'status': 'success', 'message': f'Lock {action}ed successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to communicate with ESP32'})
            
    except Exception as e:
        print(f"Error controlling lock: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})

@app.route('/api/rooms')
def get_rooms():
    connection = get_db_connection()
    rooms = []
    
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT room_id, room_name, status FROM room_controllers ORDER BY room_name")
            rooms = cursor.fetchall()
        connection.close()
    
    return jsonify(rooms)

@app.route('/api/student_count')
def get_student_count():
    room_id = request.args.get('room_id')
    class_id = session.get('current_log_id')
    
    if not class_id:
        return jsonify({'status': 'error', 'message': 'No active class', 'count': 0})
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed', 'count': 0})
            
        with connection.cursor() as cursor:
            # Updated query to use new table structure
            sql = """
                SELECT COUNT(*) as count 
                FROM student_attendance_new
                WHERE class_id = %s
            """
            cursor.execute(sql, (class_id,))
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            return jsonify({
                'status': 'success',
                'count': count
            })
    except Exception as e:
        print(f"Error getting student count: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'count': 0})
    finally:
        if connection:
            connection.close()

def send_command_to_esp32(room_id, command):
    try:
        connection = get_db_connection()
        if not connection:
            print(f"Database connection failed when looking up ESP32 for room {room_id}")
            return False
            
        with connection.cursor() as cursor:
            cursor.execute("SELECT ip_address FROM room_controllers WHERE room_id = %s", (room_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"Error: Room {room_id} not found in database")
                return False
                
            esp32_ip = result['ip_address']
            print(f"Found ESP32 at {esp32_ip} for room {room_id}")
            
        connection.close()
        
        import requests
        
        endpoint = "on" if command == "ON" else "off"
        url = f"http://{esp32_ip}/{endpoint}"
        
        print(f"Sending {command} command to Room {room_id} (ESP32 at {url})")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            update_controller_status(room_id, 'online')
            print(f"ESP32 command successful: {response.text}")
            return True
        else:
            print(f"ESP32 returned error: {response.status_code}")
            update_controller_status(room_id, 'error')
            return False
    except Exception as e:
        print(f"Failed to connect to ESP32: {e}")
        update_controller_status(room_id, 'offline')
        return False

def update_controller_status(room_id, status):
    """Update the last_seen and status of a room controller"""
    try:
        connection = get_db_connection()
        if connection:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE room_controllers 
                    SET last_seen = %s, status = %s 
                    WHERE room_id = %s
                """
                cursor.execute(sql, (datetime.now(), status, room_id))
                connection.commit()
            connection.close()
    except Exception as e:
        print(f"Error updating controller status: {e}")

def check_faculty_schedule(faculty_id, room_id):
    """
    Check if faculty has a scheduled class in the current time slot,
    regardless of which room they're physically accessing.
    """
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        now = datetime.now()
        current_day = now.strftime("%A").upper()
        
        print(f"SYSTEM TIME CHECK: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"LOOKING FOR SCHEDULE: Faculty {faculty_id} on {current_day} (any room)")
        
        with connection.cursor() as cursor:
            sql = """
                SELECT * FROM schedule 
                WHERE faculty_id = %s 
                AND day = %s
                ORDER BY time
            """
            cursor.execute(sql, (faculty_id, current_day))
            schedules = cursor.fetchall()
            
            if not schedules:
                print(f"No schedule found for faculty {faculty_id} on {current_day}")
                return None
                
            for idx, schedule in enumerate(schedules):
                print(f"FOUND SCHEDULE #{idx+1}: {schedule['subject']} at {schedule['time']} in room {schedule['room_id']}")
            
            now_minutes = now.hour * 60 + now.minute
            
            for schedule in schedules:
                time_range = schedule['time']
                print(f"PROCESSING: {schedule['subject']}, time: {time_range}, room: {schedule['room_id']}")
                
                try:
                    start_str, end_str = time_range.split('-')
                    
                    start_hour, start_minute = map(int, start_str.strip().split(':'))
                    end_hour, end_minute = map(int, end_str.strip().split(':'))
                    
                    start_minutes = start_hour * 60 + start_minute
                    end_minutes = end_hour * 60 + end_minute
                    
                    early_start_minutes = start_minutes - 15
                    
                    print(f"TIME COMPARISON (in minutes since midnight):")
                    print(f"  Class start: {start_minutes} ({start_hour}:{start_minute:02d})")
                    print(f"  Class end: {end_minutes} ({end_hour}:{end_minute:02d})")
                    print(f"  Current time: {now_minutes} ({now.hour}:{now.minute:02d})")

                    if early_start_minutes <= now_minutes <= end_minutes:
                        print(f"✅ MATCH: Currently in class time window for {schedule['subject']}")
                        return "scheduled_now"
                    
                    minutes_until_class = start_minutes - now_minutes
                    print(f"Minutes until class: {minutes_until_class}")
                    
                    if 0 < minutes_until_class <= 30:
                        print(f"✅ MATCH: Class starting soon ({minutes_until_class} minutes) for {schedule['subject']}")
                        return "scheduled_soon"
                        
                except Exception as e:
                    print(f"ERROR parsing schedule time: {e}")
                    continue
            
            print("❌ NO MATCHING SCHEDULE FOUND for current time window")
            return None
    except Exception as e:
        print(f"Error checking faculty schedule: {e}")
        return None
    finally:
        if connection:
            connection.close()

def convert_schedule_time_to_datetime(time_str, reference_date):
    """
    Convert a schedule time string like "14:00" to a datetime object
    using the reference_date for year, month, day
    """
    hour, minute = map(int, time_str.split(':'))
    
    return datetime(
        reference_date.year, 
        reference_date.month, 
        reference_date.day,
        hour, 
        minute, 
        0
    )

@app.route('/api/validate_student_rfid', methods=['POST'])
def validate_student_rfid():
    rfid_code = request.form.get('rfid_code')
    room_id = int(request.form.get('room_id', 0))
    class_id = session.get('current_log_id')
    
    print(f"Student RFID request: code={rfid_code}, room={room_id}, class_id={class_id}")
    
    if not rfid_code:
        return jsonify({'status': 'error', 'message': 'No RFID code provided'})
        
    if not class_id:
        print(f"ERROR: No active class_id in session")
        return jsonify({'status': 'error', 'message': 'No active class session'})
        
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
            
        with connection.cursor() as cursor:
            # Check room status
            if not room_status['in_use'] or not room_status['faculty_id']:
                return jsonify({'status': 'error', 'message': 'No active class in this room'})
                
            # Check if student exists with this RFID code
            sql = "SELECT * FROM students WHERE rfid_code_student = %s"
            cursor.execute(sql, (rfid_code,))
            student = cursor.fetchone()
            
            if not student:
                print(f"Invalid student RFID: {rfid_code}")
                return jsonify({'status': 'error', 'message': 'Invalid student RFID'})
                
            print(f"Found student: {student['name']} (#{student['student_number']})")
            
            # Get the current class schedule
            faculty_id = room_status['faculty_id']
            now = datetime.now()
            current_day = now.strftime("%A").upper()
            
            schedule_sql = """
                SELECT * FROM schedule 
                WHERE faculty_id = %s 
                AND day = %s
            """
            cursor.execute(schedule_sql, (faculty_id, current_day))
            schedule = cursor.fetchone()
            
            if not schedule:
                print(f"No schedule found for faculty {faculty_id} on {current_day}")
                return jsonify({
                    'status': 'error', 
                    'message': 'No active schedule found for current class'
                })
                
            # Verify student is in the correct section
            if student['section_id'] != schedule['section_id']:
                print(f"Section mismatch: student={student['section_id']}, schedule={schedule['section_id']}")
                return jsonify({
                    'status': 'error',
                    'message': f"Student not enrolled in this section ({schedule['section_id']})"
                })
                
            # Check if student already checked in for this class
            attendance_sql = """
                SELECT * FROM student_attendance_new
                WHERE student_number = %s 
                AND class_id = %s
            """
            cursor.execute(attendance_sql, (student['student_number'], class_id))
            existing_attendance = cursor.fetchone()
            
            if existing_attendance:
                print(f"Student {student['name']} already checked in with PC #{existing_attendance['pc_number']}")
                return jsonify({
                    'status': 'info',
                    'message': 'Student already checked in for this class',
                    'student_name': student['name'],
                    'student_number': student['student_number'],
                    'pc_number': existing_attendance['pc_number']
                })
            
            # Get next available PC number
            pc_sql = """
                SELECT MAX(SUBSTRING(pc_number, 3)) as max_pc 
                FROM student_attendance_new
                WHERE class_id = %s
            """
            cursor.execute(pc_sql, (class_id,))
            result = cursor.fetchone()
            
            next_pc_num = 1
            if result and result['max_pc'] is not None and result['max_pc'].isdigit():
                next_pc_num = int(result['max_pc']) + 1
                
            pc_number = f"PC#{next_pc_num:02d}"
            print(f"Assigning PC #{pc_number} to student {student['name']}")

            # Insert the attendance record
            try:
                insert_sql = """
                    INSERT INTO student_attendance_new
                    (student_number, class_id, pc_number)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    student['student_number'],
                    class_id,
                    pc_number
                ))
                connection.commit()
                print(f"SUCCESS: Attendance recorded for student {student['name']} with PC #{pc_number}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Attendance recorded',
                    'student_name': student['name'],
                    'student_number': student['student_number'],
                    'pc_number': pc_number
                })
            except Exception as db_error:
                print(f"Database error during insert: {db_error}")
                connection.rollback()
                return jsonify({'status': 'error', 'message': f'Database error: {str(db_error)}'})
            
    except Exception as e:
        print(f"Error validating student RFID: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})
    finally:
        if connection:
            connection.close()

@app.route('/api/debug/session')
def debug_session():
    """Debug endpoint to check session variables and room status"""
    debug_info = {
        'session': {
            'current_log_id': session.get('current_log_id'),
            'current_room_id': session.get('current_room_id'),
            'has_class': session.get('has_class'),
            'class_status': session.get('class_status')
        },
        'room_status': {
            'in_use': room_status.get('in_use'),
            'faculty_id': room_status.get('faculty_id'),
            'faculty_name': room_status.get('faculty_name'),
            'start_time': str(room_status.get('start_time')) if room_status.get('start_time') else None
        }
    }
    return jsonify(debug_info)

@app.route('/api/check_faculty_rfid', methods=['POST'])
def check_faculty_rfid():
    rfid_code = request.form.get('rfid_code')
    
    if not rfid_code:
        return jsonify({'status': 'error', 'message': 'No RFID code provided', 'is_current_faculty': False})
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed', 'is_current_faculty': False})
            
        with connection.cursor() as cursor:
            sql = "SELECT * FROM faculty WHERE rfid_code = %s"
            cursor.execute(sql, (rfid_code,))
            faculty = cursor.fetchone()
            
            if faculty and faculty['faculty_id'] == room_status['faculty_id']:
                return jsonify({
                    'status': 'success',
                    'message': 'Faculty RFID matched current session',
                    'is_current_faculty': True,
                    'faculty_id': faculty['faculty_id']
                })
            else:
                return jsonify({
                    'status': 'info',
                    'message': 'Not current faculty RFID',
                    'is_current_faculty': False
                })
                
    except Exception as e:
        print(f"Error checking faculty RFID: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'is_current_faculty': False})
    finally:
        if connection:
            connection.close()
            
if __name__ == '__main__':
    print("🚀 Starting RFID Room Tracking Server...")
    print("📡 Server accessible at:")
    print("   - Local: http://127.0.0.1:6969")
    print("   - Network: http://192.168.1.9:6969")
    
    app.run(host='0.0.0.0', port=6969, debug=True)