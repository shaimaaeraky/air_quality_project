// Author: Shaimaa

int sensorPin = A0;      // MQ-135 connected to A0
int sensorValue = 0;     // variable to store sensor value

void setup() {
  Serial.begin(9600);    // start serial communication
}

void loop() {
  sensorValue = analogRead(sensorPin);  // read analog value
  
  Serial.print("AQI Value: ");
  Serial.println(sensorValue);          // print value
  
  delay(5000);  // wait 5 seconds (required in project)
}
