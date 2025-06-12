int sensorPin0 = A0;
int sensorPin1 = A1;
int sensor0 = 1000;
int sensor1 = 1000;
int sensorValue = 0;

int laserControlPin = 9;
 
float threshold = 800;
int sent = 0;
int lastSent = -1; // Track previous state to avoid spam
 
String command = "";
 
// Const, change depending on needs 
const float secondsCalibrating = 1.5; 
 
void setup() {
  pinMode(sensorPin0, INPUT);
  pinMode(sensorPin1, INPUT);
  pinMode(laserControlPin, OUTPUT);
  Serial.begin(9600);
 
  digitalWrite(laserControlPin, HIGH);
  sensor0 = analogRead(sensorPin0);
  sensor1 = analogRead(sensorPin1);
  Serial.println("Calibrating...");
  int tick = secondsCalibrating * 10;
  int sum = 0;
  for (int i = 0; i < tick; i++) {
    sum += sensor0 + sensor1;
    delay(100);
  }
 
  float thres = sum / (tick * 2);
  threshold = thres + 200;
  Serial.println("Average ambiant light: " + String(thres));
  Serial.println("Threshold: " + String(threshold));
  Serial.println("SENSOR_READY"); // Signal to Flask that sensor is ready
}
 
void loop() {
  sensor0 = analogRead(sensorPin0);
  sensor1 = analogRead(sensorPin1);
 
  // Will send a constant 0 to the phone, and 1 if both sensors are triggered
  if (sensor0 >= threshold || sensor1 >= threshold) {
    sent = 0;
  }
  else {
    sent = 1;
  }
  
  // Only send when state changes to avoid spam
  if (sent != lastSent) {
    if (sent == 1) {
      Serial.println("SENSOR_TRIGGERED");
    } else {
      Serial.println("SENSOR_CLEAR");
    }
    lastSent = sent;
  }
 
  // Handle commands from Flask
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      handleCommand(command);
      command = "";
    }
    else {
      command += c;
    }
  }
 
  delay(100); // Reduced delay for faster response
}
 
void handleCommand(String cmd) {
  cmd.trim();
  if (cmd == "ON") {
    digitalWrite(laserControlPin, HIGH);
    Serial.println("LASER_ON");
  }
  else if (cmd == "OFF") {
    digitalWrite(laserControlPin, LOW);
    Serial.println("LASER_OFF");
  }
  else if (cmd == "STATUS") {
    Serial.println("SENSOR_STATUS:" + String(sent));
  }
}