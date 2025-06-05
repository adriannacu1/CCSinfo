from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import pymysql
import time

app = Flask(__name__)
app.secret_key = 'CCS-2025-SecretKey'  

room_status = {
    'locked': True,
    'authenticated': False,
    'last_sensor_trigger': None,
    'access_log': [],
    'timer_started': False,
    'timer_start_time': None,
    'timer_duration': 300  # 5 minutes in seconds
}

# Database connection
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

@app.route('/')
def index():
    alarm = request.args.get('alarm')
    if alarm == 'true':
        room_status['last_sensor_trigger'] = True
    
    return render_template('room_standby.html')

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
    return jsonify(get_timer_status())

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
                    
                    print(f"Login successful for: {faculty['name']}")
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

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("Starting Room Security Server...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} {list(rule.methods)}")
    
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, port=5000)