from flask import Flask, render_template, jsonify
import serial
import threading
import time
import serial.tools.list_ports

app = Flask(__name__)

# Global variables to store sensor state
sensor_status = {"blocked": False, "last_update": time.time()}
bluetooth_connected = False
bt_serial = None

def find_bluetooth_port():
    """Find Bluetooth COM port"""
    ports = serial.tools.list_ports.comports()
    print("Available COM ports:")
    for port, desc, hwid in ports:
        print(f"  {port}: {desc}")
        if any(keyword in desc.upper() for keyword in ['BLUETOOTH', 'HC-05', 'HC-06', 'ESP32']):
            print(f"  -> Potential Bluetooth device found: {port}")
            return port
    return None

def connect_bluetooth():
    global bt_serial, bluetooth_connected
    try:
        print("Connecting to Bluetooth on COM10...")
        bt_serial = serial.Serial('COM10', 9600, timeout=1)
        time.sleep(2)
        bluetooth_connected = True
        print("Bluetooth connected successfully on COM10")
    except Exception as e:
        print(f"Failed to connect to Bluetooth on COM10: {e}")
        # Try COM10 as backup
        try:
            print("Trying COM9...")
            bt_serial = serial.Serial('COM9', 9600, timeout=1)
            time.sleep(2)
            bluetooth_connected = True
            print("Bluetooth connected successfully on COM9")
        except Exception as e2:
            print(f"Failed to connect to COM9: {e2}")
            bluetooth_connected = False

def read_bluetooth_data():
    global sensor_status, bluetooth_connected
    consecutive_failures = 0
    
    while True:
        if bluetooth_connected and bt_serial:
            try:
                if bt_serial.in_waiting > 0:
                    line = bt_serial.readline().decode('utf-8').strip()
                    print(f"Received from Bluetooth: '{line}'")
                    
                    # Check if it's sensor data (digit)
                    if line.isdigit():
                        sensor_blocked = int(line) == 1
                        sensor_status = {
                            "blocked": sensor_blocked,
                            "last_update": time.time()
                        }
                        print(f"Sensor status: {'BLOCKED' if sensor_blocked else 'READY'}")
                        consecutive_failures = 0
                    elif "LASER" in line:
                        print(f"Laser status: {line}")
                    elif line.strip():
                        print(f"Other message: '{line}'")
                        
            except Exception as e:
                print(f"Error reading from Bluetooth: {e}")
                consecutive_failures += 1
                if consecutive_failures > 10:
                    bluetooth_connected = False
                    print("Too many consecutive failures, marking as disconnected")
                    time.sleep(2)
                    connect_bluetooth()
                    consecutive_failures = 0
        else:
            # Not connected, try to connect
            if not bluetooth_connected:
                print("Bluetooth not connected, attempting to connect...")
                connect_bluetooth()
                if not bluetooth_connected:
                    time.sleep(5)  # Wait 5 seconds before trying again
        
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template('sensor.html')

@app.route('/api/sensor-status')
def get_sensor_status():
    current_time = time.time()
    # Check if data is recent (within last 3 seconds)
    data_fresh = (current_time - sensor_status["last_update"]) < 3
    
    response = {
        "blocked": sensor_status["blocked"],
        "connected": bluetooth_connected and data_fresh,
        "last_update": sensor_status["last_update"]
    }
    print(f"API Response: {response}")
    return jsonify(response)

@app.route('/api/laser/<action>')
def control_laser(action):
    if bluetooth_connected and bt_serial:
        try:
            if action.upper() in ['ON', 'OFF']:
                command = f"{action.upper()}\n"
                bt_serial.write(command.encode())
                bt_serial.flush()
                print(f"Sent command via Bluetooth: {action.upper()}")
                return jsonify({"status": "success", "action": action.upper()})
            else:
                return jsonify({"status": "error", "message": "Invalid action"})
        except Exception as e:
            print(f"Error sending Bluetooth command: {e}")
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": "Bluetooth not connected"})

if __name__ == '__main__':
    print("Starting Flask application with Bluetooth...")
    
    # Start Bluetooth connection and reading thread
    connect_bluetooth()
    bluetooth_thread = threading.Thread(target=read_bluetooth_data, daemon=True)
    bluetooth_thread.start()
    
    if bluetooth_connected:
        print("Bluetooth thread started - connected")
    else:
        print("Bluetooth thread started - will keep trying to connect")
    
    print("Flask app running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)