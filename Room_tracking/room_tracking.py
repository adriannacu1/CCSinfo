from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import pymysql
import time
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'CCS-2025-SecretKey'  

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
    'five_minute_start_time': None  
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

def check_authentication():
    return 'faculty_id' in session and room_status['authenticated']

def get_timer_status():
    if not room_status['timer_started'] or check_authentication():
        return {'active': False, 'time_left': 0}
    
    if room_status['timer_start_time']:
        elapsed = time.time() - room_status['timer_start_time']
        time_left = max(0, room_status['timer_duration'] - elapsed)
        return {'active': time_left > 0, 'time_left': int(time_left)}
    
    return {'active': False, 'time_left': 0}

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

#trigger sensor room_standby and professor_login
@app.route('/trigger_sensor', methods=['POST'])
def trigger_sensor():
    if not check_authentication():
        room_status['last_sensor_trigger'] = True
        room_status['timer_started'] = True
        room_status['timer_start_time'] = time.time()
        room_status['access_log'].append({
            'type': 'unauthorized_access',
            'timestamp': 'now' 
        })
        return jsonify({'status': 'alert_triggered', 'message': 'Unauthorized access detected'})
    return jsonify({'status': 'authorized', 'message': 'Access granted'})

@app.route('/timer_status')
def timer_status():
    timer_data = get_timer_status()
    if room_status['timer_started'] and timer_data['time_left'] <= 0:
        pass
    return jsonify(timer_data)

@app.route('/')
def index():
    alarm = request.args.get('alarm')
    if alarm == 'true':
        room_status['last_sensor_trigger'] = True

    return render_template('room_standby.html')

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
                    
                    session['class_start_time'] = int(time.time())  # Current timestamp
                    
                    duration_map = {
                        '1 min': 1,
                        '1 Hour': 60,
                        '1.5 Hours': 90,
                        '2 Hours': 120,
                        '2.5 Hours': 150,
                        '3 Hours': 180
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
                SELECT student_number, pc_number, check_in_time as timestamp 
                FROM student_attendance 
                WHERE professor_id = %s AND class_session_id = %s
                ORDER BY check_in_time DESC
            """
            cursor.execute(attendance_sql, (session['faculty_id'], session['class_session_id']))
            attendance_records = cursor.fetchall()
            
            for record in attendance_records:
                if record['timestamp']:
                    record['timestamp'] = record['timestamp'].strftime('%H:%M:%S')
            
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

@app.route('/unlock_room', methods=['POST'])
def unlock_room():
    if 'faculty_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'})
    
    room_status['locked'] = False
    room_status['authenticated'] = True
    
    return jsonify({'status': 'success', 'message': 'Room unlocked successfully!'})

@app.route('/logout')
def logout():
    if 'faculty_id' in session:
        print(f"Logout for: {session.get('faculty_name', 'Unknown')}")
        
        try:
            connection = get_db_connection()
            if connection:
                with connection.cursor() as cursor:
                    update_sql = "UPDATE faculty SET status_state = %s WHERE faculty_id = %s"
                    cursor.execute(update_sql, ('AVAILABLE', session['faculty_id']))
                    
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
                    print(f"Reset status for faculty_id: {session['faculty_id']} and their students")
                connection.close()
        except Exception as e:
            print(f"Error updating status on logout: {e}")
    
    session.clear()
    room_status['authenticated'] = False
    room_status['locked'] = True
    room_status['professor_logged_in'] = False
    return redirect(url_for('index'))

@app.route('/mayoral_timer_status')
def mayoral_timer_status():
    return jsonify(get_mayoral_timer_status())

@app.route('/acknowledge_mayoral_alarm', methods=['POST'])
def acknowledge_mayoral_alarm():
    if room_status.get('mayoral_active', False):
        room_status['mayoral_timer_start'] = time.time()
        print("Mayoral alarm acknowledged - Timer restarted")
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})

@app.route('/temporary_key')
def temporary_key():
    return render_template('temporary-key-screen.html', timer_active=get_timer_status())

@app.route('/loginInterface')
def login():
    return render_template('loginInterface.html', timer_active=get_timer_status())

@app.route('/mayoral_key')
def mayoral_key():
    return render_template('mayoral_key_screen.html')

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

@app.route('/mayoral_screen')
def mayoral_screen():
    if not room_status.get('mayoral_active', False):
        return redirect(url_for('mayoral_key'))
    
    return render_template('mayoral_screen.html')

@app.route('/check_professor_status')
def check_professor_status():
    return jsonify({
        'professor_logged_in': room_status.get('professor_logged_in', False),
        'authenticated': room_status.get('authenticated', False)
    })

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
                
                print(f"Mayoral code {code} used successfully - Redirecting to dashboard")
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

@app.route('/maintenance_screen')
def maintenance_screen():
    return render_template('maintenance_screen.html')

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
    if not room_status.get('five_minute_active', False):
        return redirect(url_for('five_minutes_screen'))
    
    if room_status['five_minute_start_time']:
        elapsed = time.time() - room_status['five_minute_start_time']
        if elapsed > 300: 
            room_status['five_minute_active'] = False
            room_status['five_minute_start_time'] = None
            room_status['authenticated'] = False
            room_status['locked'] = True
            room_status['sensors_disabled'] = False
            return redirect(url_for('index'))
    
    return render_template('five-minutes-key-screen.html')

@app.route('/check_five_minute_status')
def check_five_minute_status():
    if not room_status.get('five_minute_active', False):
        return jsonify({'active': False})
    
    if room_status['five_minute_start_time']:
        elapsed = time.time() - room_status['five_minute_start_time']
        if elapsed > 300: 
            room_status['five_minute_active'] = False
            room_status['five_minute_start_time'] = None
            room_status['authenticated'] = False
            room_status['locked'] = True
            room_status['sensors_disabled'] = False

            try:
                connection = get_db_connection()
                if connection:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM rand_strings WHERE State = %s", ('5minutes',))
                        connection.commit()
                    connection.close()
            except Exception as e:
                print(f"Error cleaning up expired codes: {e}")
            
            return jsonify({'active': False})
    
    return jsonify({'active': True})

@app.route('/expire_five_minute_access', methods=['POST'])
def expire_five_minute_access():
    room_status['five_minute_active'] = False
    room_status['five_minute_start_time'] = None
    room_status['authenticated'] = False
    room_status['locked'] = True
    room_status['sensors_disabled'] = False
    
    try:
        connection = get_db_connection()
        if connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM rand_strings WHERE State = %s", ('5minutes',))
                connection.commit()
            connection.close()
            print("Expired 5-minute access and cleaned up unused codes")
    except Exception as e:
        print(f"Error cleaning up codes: {e}")
    
    return jsonify({'status': 'success'})

@app.route('/reset_timer_after_alarm', methods=['POST'])
def reset_timer_after_alarm():
    room_status['timer_started'] = False
    room_status['timer_start_time'] = None
    room_status['last_sensor_trigger'] = None
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("Starting Room Security Server...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} {list(rule.methods)}")
    
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, port=5000)