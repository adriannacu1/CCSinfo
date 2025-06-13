int sensorPin0 = A0;
int sensorPin1 = A1;
int sensor0 = 1000;
int sensor1 = 1000;
int sensorValue = 0;

int sensorControlPin = 9;

float threshold = 800;
int sent = 0;
 
String command = "";
 
// Const, change depending on needs 
const float secondsCalibrating = 1.5; 
 
void setup() {
  pinMode(sensorPin0, INPUT);
  pinMode(sensorPin1, INPUT);
  pinMode(sensorControlPin, OUTPUT);
  Serial.begin(9600);
 
  digitalWrite(sensorControlPin, HIGH);
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
}
 
void loop() {
  sensor0 = analogRead(sensorPin0);
  sensor1 = analogRead(sensorPin1);
 
  // Will send a constant 0 to the phone, and 1 if both sensors are triggered
  if (sensor0 >= threshold || sensor1 >= threshold) {
    sent = 0;
    delay(500);
  }
  else {
    sent = 1;
    delay(500);
  }
 
  Serial.println(String(sent));
 
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
 
  delay(300);
}
 
void handleCommand(String cmd) {
  cmd.trim();
  if (cmd == "ON") {
    // Send "ON" on tablet
    // Code here for turning on the laser module
    digitalWrite(sensorControlPin, HIGH);
    Serial.println("LASER ON");
  }
  else if (cmd == "OFF") {
    // Send "OFF" on the tablet
    // Code here for turning off the laser module
    digitalWrite(sensorControlPin, LOW);
    Serial.println("LASER OFF");
  }
}