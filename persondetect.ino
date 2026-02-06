#include <WiFi.h>
#include <HTTPClient.h>

#define TRIG_PIN 5
#define ECHO_PIN 18

const char* ssid = "AndroidAPD4B5";
const char* password = "bbdmm1121";

// Your PC/server local IP where Flask is running
const char* serverIP = "http://10.245.122.94:5001/detect";

long duration;
float distance;

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void loop() {
  // Trigger ultrasonic sensor
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read echo
  duration = pulseIn(ECHO_PIN, HIGH);
  distance = duration * 0.034 / 2; // cm

  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  if(distance > 0 && distance < 100) {
    Serial.println("Person detected!");

    if(WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverIP);
      int httpResponseCode = http.GET();
      if(httpResponseCode > 0){
        Serial.println("Notification sent to server!");
      } else {
        Serial.print("Error sending to server: ");
        Serial.println(httpResponseCode);
      }
      http.end();
    }

    delay(5000); // avoid spamming
  }

  delay(500);
}

