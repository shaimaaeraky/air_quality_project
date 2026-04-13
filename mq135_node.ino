// Physical Edge Node: Arduino + MQ135
// Author: Shaimaa Ghoneim

const int MQ135_PIN = A0; // MQ-135 analog output connected to A0

void setup() {
  // Initialize serial communication to match the Python bridge
  Serial.begin(9600); 
  pinMode(MQ135_PIN, INPUT);
}

void loop() {
  // Read the raw analog voltage from the sensor
  int aqi_raw = analogRead(MQ135_PIN);
  
  // Broadcast only the integer to the Serial port for the Python script to catch
  Serial.println(aqi_raw); 
  
  // 5-second delay to match the temporal resampling baseline in the report
  delay(5000); 
}
