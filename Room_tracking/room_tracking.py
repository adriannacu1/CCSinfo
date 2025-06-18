from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
import os
import pymysql
import time
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'CCS-2025-SecretKey'
CORS(app)

room_status = {
    'locked': True,
    'authenticated': False,
    'last_sensor_trigger': None,
    'access_log': [],
    'timer_started': False,
    'timer_start_time': None,
    'timer_duration': 300, 
    'mayoral_active': False,
    'mayoral_timer_start': None,
    'mayoral_timer_duration': 300,
    'professor_logged_in': False,
    'maintenance_active': False,
    'sensors_disabled': False,
    'five_minute_active': False, 
    'five_minute_start_time': None,
    'esp32_sensor_data': {'sensor_blocked': False, 'last_update': None}
}

#db connection
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

def safe_strftime(datetime_obj, format_str='%H:%M:%S'):
    """Safely format datetime objects or strings to the specified format"""
    if not datetime_obj:
        return None
    
    # If it's already a string, try to parse it first
    if isinstance(datetime_obj, str):
        try:
            # Try to parse as datetime
            parsed_dt = datetime.strptime(datetime_obj, '%Y-%m-%d %H:%M:%S')
            return parsed_dt.strftime(format_str)
        except ValueError:
            try:
                # If that fails, try to extract time part if it contains space
                if ' ' in datetime_obj:
                    time_part = datetime_obj.split(' ')[1]
                    return time_part[:8]  # Return HH:MM:SS
                else:
                    return datetime_obj[:8]  # Assume it's already time format
            except:
                return str(datetime_obj)
    
    # If it's a datetime object, format it normally
    try:
        return datetime_obj.strftime(format_str)
    except AttributeError:
        return str(datetime_obj)

def check_authentication():
    return 'faculty_id' in session and room_status['authenticated']

def get_timer_status():
    if not room_status['timer_started'] or check_authentication():
        return {'active': False, 'time_left': 0, 'expired': False}
    
    if room_status['timer_start_time']:
        elapsed = time.time() - room_status['timer_start_time']
        time_left = max(0, room_status['timer_duration'] - elapsed)
        
        # Check if timer has expired
        if time_left <= 0:
            print("⏰ Timer expired! Resetting timer state...")
            room_status['timer_started'] = False
            room_status['timer_start_time'] = None
            room_status['last_sensor_trigger'] = None
            return {'active': False, 'time_left': 0, 'expired': True}
        
        return {'active': True, 'time_left': int(time_left), 'expired': False}
    
    return {'active': False, 'time_left': 0, 'expired': False}

def get_mayoral_timer_status():
    if not room_status.get('mayoral_active', False) or room_status.get('professor_logged_in', False):
        return {'active': False, 'time_left': 0}
    
    if room_status['mayoral_timer_start']:
        elapsed = time.time() - room_status['mayoral_timer_start']
        time_left = max(0, room_status['mayoral_timer_duration'] - elapsed)
        
        if time_left <= 0:
            return {'active': True, 'time_left': 0}
        else:
            return {'active': True, 'time_left': int(time_left)}
    
    return {'active': False, 'time_left': 0}

# ESP32 sensor data endpoint
@app.route('/api/esp32/sensor-data', methods=['POST', 'OPTIONS'])
def receive_esp32_sensor_data():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        print("=== ESP32 Data Received ===")
        
        data = request.get_json()
        if not data:
            print("❌ No JSON data received")
            return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400
        
        print(f"📊 Data: {data}")
        
        sensor_blocked = data.get('sensor_blocked', False)
        sensor0 = data.get('sensor0', 0)
        sensor1 = data.get('sensor1', 0)
        threshold0 = data.get('threshold0', 0)
        threshold1 = data.get('threshold1', 0)
        
        # Update room status
        room_status['esp32_sensor_data'] = {
            'sensor_blocked': sensor_blocked,
            'sensor0': sensor0,
            'sensor1': sensor1,
            'threshold0': threshold0,
            'threshold1': threshold1,
            'last_update': time.time()
        }
        
        # Only trigger alarm if sensor is blocked AND no timer is currently active AND not authenticated
        if (sensor_blocked and 
            not room_status['timer_started'] and 
            not check_authentication() and 
            not room_status.get('sensors_disabled', False)):
            
            print(f"🚨 ESP32 Sensor triggered NEW ALARM! S0:{sensor0} S1:{sensor1}")
            room_status['last_sensor_trigger'] = True
            room_status['timer_started'] = True
            room_status['timer_start_time'] = time.time()
            room_status['access_log'].append({
                'type': 'esp32_sensor_triggered',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sensor_data': {
                    'sensor0': sensor0,
                    'sensor1': sensor1,
                    'threshold0': threshold0,
                    'threshold1': threshold1
                }
            })
        elif sensor_blocked and room_status['timer_started']:
            print(f"🔄 Sensor blocked but timer already active - no new trigger")
        
        return jsonify({'status': 'success', 'message': 'Data received successfully'})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ESP32 status endpoint
@app.route('/api/esp32/status')
def get_esp32_status():
    data = room_status['esp32_sensor_data']
    print(f"📤 Status request: {data}")
    return jsonify(data)

# ESP32 test endpoint
@app.route('/api/esp32/test', methods=['GET', 'POST'])
def test_esp32_connection():
    if request.method == 'POST':
        data = request.get_json() or {}
        print(f"✅ ESP32 POST test: {data}")
        return jsonify({'status': 'success', 'message': 'Flask received ESP32 POST!', 'data': data})
    else:
        print("✅ ESP32 GET test received")
        return jsonify({
            'status': 'success', 
            'message': 'Flask server is running and accessible from ESP32!',
            'timestamp': time.time(),
            'server_ip': '192.168.1.9'
        })

# Manual trigger for testing
@app.route('/trigger_sensor', methods=['POST'])
def trigger_sensor():
    manual_trigger = request.get_json().get('manual', False) if request.is_json else True
    
    if manual_trigger:
        # Only trigger if no timer is currently active and not authenticated
        if not room_status['timer_started'] and not check_authentication():
            print("🔧 Manual trigger activated")
            room_status['last_sensor_trigger'] = True
            room_status['timer_started'] = True
            room_status['timer_start_time'] = time.time()
            room_status['access_log'].append({
                'type': 'manual_trigger',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return jsonify({'status': 'alert_triggered', 'message': 'Manual sensor trigger activated'})
        else:
            return jsonify({'status': 'no_action', 'message': 'Timer already active or user authenticated'})
    
    return jsonify({'status': 'authorized', 'message': 'Access granted or no trigger needed'})

@app.route('/timer_status')
def timer_status():
    timer_data = get_timer_status()
    return jsonify(timer_data)

@app.route('/')
def index():
    return render_template('room_standby.html')

@app.route('/reset_timer_after_alarm', methods=['POST'])
def reset_timer_after_alarm():
    print("🔄 Resetting timer after alarm acknowledgment")
    room_status['timer_started'] = True
    room_status['timer_start_time'] = time.time()
    room_status['last_sensor_trigger'] = None
    return jsonify({'status': 'success', 'message': 'Timer reset successfully'})

@app.route('/professor_login', methods=['GET', 'POST'])
def professor_login():
    from_page = request.args.get('from', 'loginInterface')
    print(f"Professor login route accessed with method: {request.method}")
    
    sections = []
    rooms = []
    
    try:
        connection = get_db_connection()
        if connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT section_name FROM sections ORDER BY section_name")
                sections = cursor.fetchall()
                
                cursor.execute("SELECT room_name FROM rooms ORDER BY room_name")
                rooms = cursor.fetchall()
                
            connection.close()
    except Exception as e:
        print(f"Error fetching sections and rooms: {e}")
    
    if request.method == 'POST':
        section = request.form.get('section')
        room = request.form.get('room')
        class_duration = request.form.get('class_duration')
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt - Section: {section}, Room: {room}, Duration: {class_duration}, Username: {username}")
        
        if not username or not password or not section or not room or not class_duration:
            return render_template('professor_login.html', 
                                 error='Please fill in all fields', 
                                 timer_active=get_timer_status(), 
                                 mayoral_timer=get_mayoral_timer_status(), 
                                 from_page=from_page,
                                 sections=sections,
                                 rooms=rooms)
        
        try:
            connection = get_db_connection()
            if not connection:
                return render_template('professor_login.html', 
                                     error='Database connection failed',
                                     timer_active=get_timer_status(), 
                                     mayoral_timer=get_mayoral_timer_status(), 
                                     from_page=from_page,
                                     sections=sections,
                                     rooms=rooms)
            
            with connection.cursor() as cursor:
                sql = "SELECT * FROM faculty WHERE username = %s AND password = %s"
                cursor.execute(sql, (username, password))
                faculty = cursor.fetchone()
                
                print(f"Database query result: {faculty}")
                
                if faculty:
                    session['class_session_id'] = f"{faculty['faculty_id']}_{int(time.time())}"
                    session['class_start_time'] = int(time.time())
                    
                    duration_map = {
                        '1 min': 1,
                        '15 mins': 15,
                        '30 mins': 30, 
                        '1hr': 60,
                        '2hrs': 120,
                        '3hrs': 180
                    }
                    session['class_duration_minutes'] = duration_map.get(class_duration, 60)
                    
                    status_message = f"CURRENTLY IN ROOM {room}"
                    update_sql = "UPDATE faculty SET status_state = %s WHERE faculty_id = %s"
                    cursor.execute(update_sql, (status_message, faculty['faculty_id']))
                    connection.commit()

                    session['faculty_id'] = faculty['faculty_id']
                    session['faculty_name'] = faculty['name']
                    session['username'] = faculty['username']
                    session['department'] = faculty['department']
                    session['selected_section'] = section
                    session['selected_room'] = room
                    session['class_duration'] = class_duration
                    
                    room_status['authenticated'] = True
                    room_status['locked'] = False
                    room_status['timer_started'] = False
                    room_status['timer_start_time'] = None
                    room_status['mayoral_active'] = False
                    room_status['mayoral_timer_start'] = None
                    room_status['professor_logged_in'] = True 
                    
                    print(f"Login successful for: {faculty['name']} - Section: {section}, Room: {room}, Duration: {class_duration}")
                    print(f"Updated status to: {status_message}")
                    connection.close()
                    return redirect(url_for('professor_dashboard'))
                else:
                    connection.close()
                    return render_template('professor_login.html', 
                                         error='Invalid username or password',
                                         timer_active=get_timer_status(), 
                                         mayoral_timer=get_mayoral_timer_status(), 
                                         from_page=from_page,
                                         sections=sections,
                                         rooms=rooms)
                    
        except Exception as e:
            print(f"Database error: {e}")
            return render_template('professor_login.html', 
                                 error=f'Database error: {str(e)}',
                                 timer_active=get_timer_status(), 
                                 mayoral_timer=get_mayoral_timer_status(), 
                                 from_page=from_page,
                                 sections=sections,
                                 rooms=rooms)
    
    return render_template('professor_login.html', 
                         timer_active=get_timer_status(), 
                         mayoral_timer=get_mayoral_timer_status(), 
                         from_page=from_page,
                         sections=sections,
                         rooms=rooms)

@app.route('/professor_dashboard')
def professor_dashboard():
    if 'faculty_id' not in session or 'class_session_id' not in session:
        return redirect(url_for('professor_login'))
    
    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed', 'error')
            return redirect(url_for('professor_login'))
        
        with connection.cursor() as cursor:
            attendance_sql = """
                SELECT student_number, pc_number, check_in_time, check_out_time
                FROM student_attendance 
                WHERE professor_id = %s AND class_session_id = %s
                ORDER BY check_in_time DESC
            """
            cursor.execute(attendance_sql, (session['faculty_id'], session['class_session_id']))
            attendance_records = cursor.fetchall()
            
            for record in attendance_records:
                try:
                    record['check_in_timestamp'] = safe_strftime(record.get('check_in_time'))
                    record['check_out_timestamp'] = safe_strftime(record.get('check_out_time'))
                except Exception as timestamp_error:
                    print(f"Timestamp formatting error: {timestamp_error}")
                    print(f"Record data: {record}")
                    # Fallback to string representation
                    record['check_in_timestamp'] = str(record.get('check_in_time', ''))
                    record['check_out_timestamp'] = str(record.get('check_out_time', ''))
            
            attendance_count = len(attendance_records)
            
        connection.close()
        
        return render_template('professor_dashboard.html', 
                             attendance_records=attendance_records,
                             attendance_count=attendance_count,
                             class_start_time=session.get('class_start_time', 0),
                             class_duration_minutes=session.get('class_duration_minutes', 0))
                             
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('professor_login'))

@app.route('/student_checkin', methods=['POST'])
def student_checkin():
    if 'faculty_id' not in session or 'class_session_id' not in session:
        return jsonify({'status': 'error', 'message': 'Professor not logged in'})
    
    student_number = request.form.get('student_number')
    pc_number = request.form.get('pc_number')
    
    if not student_number or not pc_number:
        return jsonify({'status': 'error', 'message': 'Please fill in all fields'})
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            check_student_sql = """
                SELECT s.*, sec.section_name 
                FROM students s 
                JOIN sections sec ON s.section_id = sec.section_id 
                WHERE s.student_number = %s
            """
            cursor.execute(check_student_sql, (student_number,))
            student = cursor.fetchone()
            
            if not student:
                connection.close()
                return jsonify({'status': 'error', 'message': 'Student number not found'})
            
            professor_section = session.get('selected_section')
            student_section_name = student.get('section_name')
            
            if student_section_name != professor_section:
                connection.close()
                return jsonify({
                    'status': 'error', 
                    'message': f'Student is from section {student_section_name}. This class is for section {professor_section}.'
                })
            
            check_pc_sql = """
                SELECT * FROM student_attendance 
                WHERE pc_number = %s AND class_session_id = %s
            """
            cursor.execute(check_pc_sql, (pc_number, session['class_session_id']))
            pc_taken = cursor.fetchone()
            
            if pc_taken:
                connection.close()
                return jsonify({'status': 'error', 'message': f'{pc_number} is already occupied in this session'})
            
            check_attendance_sql = """
                SELECT * FROM student_attendance 
                WHERE student_number = %s AND class_session_id = %s
            """
            cursor.execute(check_attendance_sql, (student_number, session['class_session_id']))
            already_checked = cursor.fetchone()
            
            if already_checked:
                connection.close()
                return jsonify({'status': 'error', 'message': 'Student already checked in for this session'})
            
            room_number = session.get('selected_room', 'Unknown')
            status_message = f"CURRENTLY IN ROOM {room_number}"
            update_student_sql = "UPDATE students SET status = %s WHERE student_number = %s"
            cursor.execute(update_student_sql, (status_message, student_number))
            
            attendance_sql = """
                INSERT INTO student_attendance 
                (student_number, pc_number, professor_id, check_in_time, room_number, class_session_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            current_time = datetime.now()
            cursor.execute(attendance_sql, (
                student_number, 
                pc_number, 
                session['faculty_id'], 
                current_time, 
                room_number, 
                session['class_session_id']
            ))
            
            connection.commit()
            connection.close()
            
            print(f"Student {student_number} from section {student_section_name} checked in to {pc_number} at {current_time}")
            
            return jsonify({
                'status': 'success', 
                'message': f'Student {student_number} checked in successfully to {pc_number}',
                'student_number': student_number,
                'pc_number': pc_number
            })
            
    except Exception as e:
        print(f"Student check-in error: {e}")
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})

# Add this new route for handling check-out
@app.route('/checkout_all_students', methods=['POST'])
def checkout_all_students():
    if 'faculty_id' not in session or 'class_session_id' not in session:
        return jsonify({'status': 'error', 'message': 'Professor not logged in'})
    
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            # Update all students in current session with check_out_time
            checkout_sql = """
                UPDATE student_attendance 
                SET check_out_time = %s 
                WHERE professor_id = %s AND class_session_id = %s AND check_out_time IS NULL
            """
            current_time = datetime.now()
            cursor.execute(checkout_sql, (current_time, session['faculty_id'], session['class_session_id']))
            
            # Get count of checked out students
            affected_rows = cursor.rowcount
            
            connection.commit()
            connection.close()
            
            print(f"Checked out {affected_rows} students at {current_time}")
            
            return jsonify({
                'status': 'success', 
                'message': f'Successfully checked out {affected_rows} students',
                'checkout_time': current_time.strftime('%H:%M:%S'),
                'students_count': affected_rows
            })
            
    except Exception as e:
        print(f"Error during checkout: {e}")
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})

@app.route('/logout')
def logout():
    if 'faculty_id' in session:
        print(f"Logout for: {session.get('faculty_name', 'Unknown')}")
        
        try:
            connection = get_db_connection()
            if connection:
                with connection.cursor() as cursor:
                    # First, check out all students who haven't been checked out
                    current_time = datetime.now()
                    checkout_sql = """
                        UPDATE student_attendance 
                        SET check_out_time = %s 
                        WHERE professor_id = %s AND class_session_id = %s AND check_out_time IS NULL
                    """
                    cursor.execute(checkout_sql, (current_time, session['faculty_id'], session.get('class_session_id', '')))
                    checked_out_count = cursor.rowcount
                    
                    # Update faculty status
                    update_sql = "UPDATE faculty SET status_state = %s WHERE faculty_id = %s"
                    cursor.execute(update_sql, ('AVAILABLE', session['faculty_id']))
                    
                    # Reset student status to AVAILABLE
                    today = datetime.now().strftime('%Y-%m-%d')
                    reset_students_sql = """
                        UPDATE students SET status = 'AVAILABLE' 
                        WHERE student_number IN (
                            SELECT student_number FROM student_attendance 
                            WHERE professor_id = %s AND DATE(check_in_time) = %s
                        )
                    """
                    cursor.execute(reset_students_sql, (session['faculty_id'], today))
                    
                    connection.commit()
                    print(f"Automatically checked out {checked_out_count} students during logout")
                    print(f"Reset status for faculty_id: {session['faculty_id']} and their students")
                connection.close()
        except Exception as e:
            print(f"Error updating status on logout: {e}")
    
    session.clear()
    room_status['authenticated'] = False
    room_status['locked'] = True
    room_status['professor_logged_in'] = False
    return redirect(url_for('index'))

@app.route('/loginInterface')
def login():
    return render_template('loginInterface.html', timer_active=get_timer_status())

# Add all the other routes (mayoral, maintenance, etc.)
@app.route('/mayoral_timer_status')
def mayoral_timer_status():
    return jsonify(get_mayoral_timer_status())

@app.route('/temporary_key')
def temporary_key():
    return render_template('temporary-key-screen.html', timer_active=get_timer_status())

@app.route('/mayoral_key')
def mayoral_key():
    return render_template('mayoral_key_screen.html')

@app.route('/maintenance_screen')
def maintenance_screen():
    return render_template('maintenance_screen.html')

@app.route('/five_minutes_screen')
def five_minutes_screen():
    return render_template('five-minutes-screen.html')

@app.route('/generate_five_minute_code', methods=['POST'])
def generate_five_minute_code():
    try:
        random_code = ''.join(random.choices(string.digits, k=7))
        
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            sql = "INSERT INTO rand_strings (randomC, Date, State) VALUES (%s, %s, %s)"
            cursor.execute(sql, (random_code, current_date, '5minutes'))
            connection.commit()
            
        connection.close()
        
        print(f"Generated 5-minute code: {random_code} at {current_date}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Code generated and sent to administration'
        })
        
    except Exception as e:
        print(f"Error generating 5-minute code: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to generate code'})

@app.route('/verify_five_minute_code', methods=['POST'])
def verify_five_minute_code():
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code or len(code) != 7:
            return jsonify({'status': 'error', 'message': 'Invalid code format'})
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            sql = "SELECT * FROM rand_strings WHERE randomC = %s AND State = %s"
            cursor.execute(sql, (code, '5minutes'))
            result = cursor.fetchone()

            if result:
                room_status['timer_started'] = False
                room_status['timer_start_time'] = None
                room_status['authenticated'] = True
                room_status['locked'] = False
                room_status['five_minute_active'] = True
                room_status['five_minute_start_time'] = time.time()
                room_status['sensors_disabled'] = True
                room_status['mayoral_active'] = False
                room_status['professor_logged_in'] = False
                room_status['maintenance_active'] = False
                
                delete_sql = "DELETE FROM rand_strings WHERE randomC = %s AND State = %s"
                cursor.execute(delete_sql, (code, '5minutes'))
                connection.commit()
                
                connection.close()
                
                print(f"5-minute code {code} used successfully - 5-minute access granted")
                return jsonify({
                    'status': 'success', 
                    'message': '5-minute access granted!',
                    'redirect': '/five_minute_dashboard'
                })
            else:
                connection.close()
                return jsonify({'status': 'error', 'message': 'Invalid or expired code'})
                
    except Exception as e:
        print(f"Error verifying 5-minute code: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to verify code'})
    
@app.route('/five_minute_dashboard')
def five_minute_dashboard():
    return render_template('five-minutes-key-screen.html')

@app.route('/generate_mayoral_code', methods=['POST'])
def generate_mayoral_code():
    try:
        random_code = ''.join(random.choices(string.digits, k=7))
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            sql = "INSERT INTO rand_strings (randomC, Date, State) VALUES (%s, %s, %s)"
            cursor.execute(sql, (random_code, current_date, 'Mayoral'))
            connection.commit()
            
        connection.close()
        print(f"Generated mayoral code: {random_code} at {current_date}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Code generated and sent to administration'
        })
        
    except Exception as e:
        print(f"Error generating mayoral code: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to generate code'})

@app.route('/verify_mayoral_code', methods=['POST'])
def verify_mayoral_code():
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code or len(code) != 7:
            return jsonify({'status': 'error', 'message': 'Invalid code format'})
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            sql = "SELECT * FROM rand_strings WHERE randomC = %s AND State = %s"
            cursor.execute(sql, (code, 'Mayoral'))
            result = cursor.fetchone()
            
            if result:
                room_status['timer_started'] = False
                room_status['timer_start_time'] = None
                room_status['authenticated'] = True
                room_status['locked'] = False
                room_status['mayoral_active'] = True 
                room_status['mayoral_timer_start'] = time.time()
                room_status['professor_logged_in'] = False 
                
                delete_sql = "DELETE FROM rand_strings WHERE randomC = %s AND State = %s"
                cursor.execute(delete_sql, (code, 'Mayoral'))
                connection.commit()
                connection.close()
                
                print(f"Mayoral code {code} used successfully")
                return jsonify({
                    'status': 'success', 
                    'message': 'Access granted!',
                    'redirect': '/mayoral_screen'
                })
            else:
                connection.close()
                return jsonify({'status': 'error', 'message': 'Invalid or expired code'})
                
    except Exception as e:
        print(f"Error verifying mayoral code: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to verify code'})
    
@app.route('/generate_maintenance_code', methods=['POST'])
def generate_maintenance_code():
    try:
        random_code = ''.join(random.choices(string.digits, k=7))
        
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            sql = "INSERT INTO rand_strings (randomC, Date, State) VALUES (%s, %s, %s)"
            cursor.execute(sql, (random_code, current_date, 'Maintenance'))
            connection.commit()
            
        connection.close()
        
        print(f"Generated maintenance code: {random_code} at {current_date}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Code generated and sent to administration'
        })
        
    except Exception as e:
        print(f"Error generating maintenance code: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to generate code'})

@app.route('/verify_maintenance_code', methods=['POST'])
def verify_maintenance_code():
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code or len(code) != 7:
            return jsonify({'status': 'error', 'message': 'Invalid code format'})
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            sql = "SELECT * FROM rand_strings WHERE randomC = %s AND State = %s"
            cursor.execute(sql, (code, 'Maintenance'))
            result = cursor.fetchone()
            
            if result:
                room_status['timer_started'] = False
                room_status['timer_start_time'] = None
                room_status['authenticated'] = True
                room_status['locked'] = False
                room_status['maintenance_active'] = True
                room_status['sensors_disabled'] = True
                room_status['mayoral_active'] = False
                room_status['professor_logged_in'] = False
                
                delete_sql = "DELETE FROM rand_strings WHERE randomC = %s AND State = %s"
                cursor.execute(delete_sql, (code, 'Maintenance'))
                connection.commit()
                
                connection.close()
                
                print(f"Maintenance code {code} used successfully - Sensors disabled")
                return jsonify({
                    'status': 'success', 
                    'message': 'Maintenance access granted!',
                    'redirect': '/maintenance_dashboard'
                })
            else:
                connection.close()
                return jsonify({'status': 'error', 'message': 'Invalid or expired code'})
                
    except Exception as e:
        print(f"Error verifying maintenance code: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to verify code'})

@app.route('/maintenance_dashboard')
def maintenance_dashboard():
    return render_template('maintenance_main_screen.html')

@app.route('/mayoral_screen')
def mayoral_screen():
    if not room_status.get('mayoral_active', False):
        return redirect(url_for('mayoral_key'))
    return render_template('mayoral_screen.html')

if __name__ == '__main__':
    print("🚀 Starting Room Security Server...")
    print("📡 Server accessible at:")
    print("   - Local: http://127.0.0.1:6969")
    print("   - Network: http://192.168.1.9:6969")
    print("   - ESP32 Test: http://192.168.1.9:6969/api/esp32/test")
    
    app.run(host='0.0.0.0', port=6969, debug=True)