#include <Arduino.h>
#include <DHT.h>

// Define DHT11 sensor pin and type
#define DHTPIN 5
#define DHTTYPE DHT11

// Define HC-SR04 pins
#define TRIGPIN 17
#define ECHOPIN 16

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize DHT11 sensor
  dht.begin();

  // Initialize HC-SR04 pins
  pinMode(TRIGPIN, OUTPUT);
  pinMode(ECHOPIN, INPUT);

  Serial.println("DHT11 and HC-SR04 test starting...");
}

void loop() {
  // ----- Read DHT11 -----
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();  // Celsius

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
  } else {
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.print(" %\t");
    
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" *C");
  }
}