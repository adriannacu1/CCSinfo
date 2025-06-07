from flask import Flask, render_template, request, jsonify, redirect, url_for, session
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
    print(f"Professor login route accessed with method: {request.method}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt - Username: {username}, Password: {password}")
        
        if not username or not password:
            return render_template('professor_login.html', error='Please enter both username and password', 
                                 timer_active=get_timer_status())
        
        try:
            connection = get_db_connection()
            if not connection:
                return render_template('professor_login.html', error='Database connection failed',
                                     timer_active=get_timer_status())
            
            with connection.cursor() as cursor:
                sql = "SELECT * FROM faculty WHERE username = %s AND password = %s"
                cursor.execute(sql, (username, password))
                faculty = cursor.fetchone()
                
                print(f"Database query result: {faculty}")
                
                if faculty:
                    session['faculty_id'] = faculty['faculty_id']
                    session['faculty_name'] = faculty['name']
                    session['username'] = faculty['username']
                    session['department'] = faculty['department']
                    
                    room_status['authenticated'] = True
                    room_status['locked'] = False
                    room_status['timer_started'] = False
                    room_status['timer_start_time'] = None
                    room_status['mayoral_active'] = False
                    room_status['professor_logged_in'] = True 
                    
                    print(f"Login successful for: {faculty['name']} - Mayoral timer deactivated")
                    connection.close()
                    return redirect(url_for('professor_dashboard'))
                else:
                    connection.close()
                    return render_template('professor_login.html', error='Invalid username or password',
                                         timer_active=get_timer_status())
                    
        except Exception as e:
            print(f"Database error: {e}")
            return render_template('professor_login.html', error=f'Database error: {str(e)}',
                                 timer_active=get_timer_status())
    
    return render_template('professor_login.html', timer_active=get_timer_status())

@app.route('/professor_dashboard')
def professor_dashboard():
    print(f"Dashboard accessed - Session: {session}")
    
    if 'faculty_id' not in session:
        print("No faculty_id in session, redirecting to login")
        return redirect(url_for('professor_login'))
    
    try:
        connection = get_db_connection()
        if not connection:
            return redirect(url_for('professor_login'))
            
        with connection.cursor() as cursor:
            sql = "SELECT * FROM faculty WHERE faculty_id = %s"
            cursor.execute(sql, (session['faculty_id'],))
            faculty = cursor.fetchone()
            connection.close()
            
            if faculty:
                print(f"Rendering dashboard for: {faculty['name']}")
                return render_template('professor_dashboard.html', faculty=faculty)
            else:
                return redirect(url_for('professor_login'))
                
    except Exception as e:
        print(f"Dashboard error: {e}")
        return redirect(url_for('professor_login'))

@app.route('/unlock_room', methods=['POST'])   #change to disable sensor------
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
    
    session.clear()
    room_status['authenticated'] = False
    room_status['locked'] = True
    return redirect(url_for('index'))

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
    # Only accessible if mayoral code was used
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
            
            #temporarily disable sensors and delete generated code
            if result:
                room_status['timer_started'] = False
                room_status['timer_start_time'] = None
                room_status['authenticated'] = True
                room_status['locked'] = False
                room_status['mayoral_active'] = True 
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
            
            #disable sensors and delete generated code!!!
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
    if not room_status.get('maintenance_active', False):
        return redirect(url_for('maintenance_screen'))
    
    return render_template('maintenance_main_screen.html')

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

            #disable sensors and delete generated code
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
                cursor.execute(delete_sql, (code, 'FiveMinute'))
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

# Add a new route to handle timer reset after alarm
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