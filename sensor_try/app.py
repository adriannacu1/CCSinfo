from flask import Flask, render_template, jsonify, request
import requests
import time
import threading

app = Flask(__name__)

# Global variables for storing system state
system_status = {
    "sensor_blocked": False,
    "laser_on": True,
    "esp32_connected": False,
    "last_update": time.time(),
    "esp32_ip": None
}

# ESP32 IP will be auto-detected or set manually
ESP32_IP = None  # Will be set when ESP32 sends data

@app.route('/')
def index():
    return render_template('sensor_control.html')

@app.route('/api/system-status')
def get_system_status():
    """API endpoint to get current system status"""
    # Check if data is recent (within last 3 seconds)
    current_time = time.time()
    data_fresh = (current_time - system_status["last_update"]) < 3
    
    response = {
        "sensor_blocked": system_status["sensor_blocked"],
        "laser_on": system_status["laser_on"],
        "esp32_connected": system_status["esp32_connected"] and data_fresh,
        "last_update": system_status["last_update"],
        "esp32_ip": system_status["esp32_ip"]
    }
    return jsonify(response)

@app.route('/api/esp32/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from ESP32"""
    global ESP32_IP
    try:
        data = request.json
        
        # Update system status
        system_status["sensor_blocked"] = data.get("sensor_blocked", False)
        system_status["esp32_connected"] = True
        system_status["last_update"] = time.time()
        
        # Auto-detect ESP32 IP
        if ESP32_IP is None:
            ESP32_IP = request.remote_addr
            system_status["esp32_ip"] = ESP32_IP
            print(f"✅ ESP32 connected from IP: {ESP32_IP}")
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error receiving sensor data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/laser/on')
def laser_on():
    """API endpoint to turn laser ON"""
    if ESP32_IP:
        try:
            response = requests.get(f"http://{ESP32_IP}/laser/on", timeout=5)
            if response.status_code == 200:
                system_status["laser_on"] = True
                return jsonify({"status": "success", "message": "Laser turned ON"})
            else:
                return jsonify({"status": "error", "message": "Failed to communicate with ESP32"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"ESP32 communication error: {str(e)}"})
    else:
        return jsonify({"status": "error", "message": "ESP32 not connected"})

@app.route('/api/laser/off')
def laser_off():
    """API endpoint to turn laser OFF"""
    if ESP32_IP:
        try:
            response = requests.get(f"http://{ESP32_IP}/laser/off", timeout=5)
            if response.status_code == 200:
                system_status["laser_on"] = False
                return jsonify({"status": "success", "message": "Laser turned OFF"})
            else:
                return jsonify({"status": "error", "message": "Failed to communicate with ESP32"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"ESP32 communication error: {str(e)}"})
    else:
        return jsonify({"status": "error", "message": "ESP32 not connected"})

@app.route('/api/esp32/status')
def get_esp32_status():
    """Get detailed ESP32 status"""
    if ESP32_IP:
        try:
            response = requests.get(f"http://{ESP32_IP}/sensor/status", timeout=5)
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({"status": "error", "message": "Failed to get ESP32 status"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"ESP32 communication error: {str(e)}"})
    else:
        return jsonify({"status": "error", "message": "ESP32 not connected"})

if __name__ == '__main__':
    print("🚀 Starting Flask Application...")
    print("📱 Access from phone: http://YOUR_PC_IP:5000")
    print("🔗 Make sure ESP32 and phone are on the same WiFi network")
    print("⚙️  ESP32 will auto-connect when it sends data")
    
    app.run(debug=True, host='0.0.0.0', port=5000)