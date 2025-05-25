from flask import Flask, render_template, request, jsonify, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'CCS-2025-SecretKey'  

room_status = {
    'locked': True,
    'authenticated': False,
    'last_sensor_trigger': None,
    'access_log': []
}

@app.route('/')
def index():
    """Main room security screen"""
    return render_template('room_standby.html')


@app.route('/trigger_sensor', methods=['POST'])
def trigger_sensor():
    """API endpoint to trigger sensor alert"""
    if not room_status['authenticated']:
        room_status['last_sensor_trigger'] = True
        room_status['access_log'].append({
            'type': 'unauthorized_access',
            'timestamp': 'now' 
        })
        return jsonify({'status': 'alert_triggered', 'message': 'Unauthorized access detected'})
    return jsonify({'status': 'authorized', 'message': 'Access granted'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for room access"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'password123':
            room_status['authenticated'] = True
            room_status['locked'] = False
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("Starting Room Security Server...")
    print("Open your browser to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)