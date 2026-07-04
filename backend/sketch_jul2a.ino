#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <time.h>
#include <HTTPClient.h>

/* This is code for Entrance Sensor

https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf

library depandnace:
esp32 
Adafruit Unified Sensor 
DHT sensor library

Remark:
Trigger pluse at least 60ms and when it is charged please connect GND first then VDD


Since DHT11 is failed so I use delay() with HC-SR04, if we can find other alternative, then 
we should use non-blocking apporach instead, so we can run 2 devices in same time

3 levels of time s > ms(0.001s) > us(1e-6)

Should test the passed time of the gate
Cycle:

1: Sending 10us trigger pluse > Read the duration of the echo pulse > calculate the distance 

2: > if someone pass then record time and count 
> analyse the record if it is too close to each other reject it else save it in into 30 size CircularBuffer

3:So conclude 2 scanning scystem 


*/


/*DHT11 and IMMT4 are clock drivened (Failed to read DHT11 )

step: 

*/


// Define HC-SR04 pins
#define TRIGPIN 17
#define ECHOPIN 16
#define LED 2

const char* Wifi_ssid = "POCOF7";
const char* Wifi_password = "e6bq2qvbuq";
const char* serverUrl = "http://YOUR_SERVER_IP_OR_DOMAIN/occupancy/upload";

const int BUFFER_SIZE = 75;

struct Record {
  unsigned long time;      //number that count in second represent ms and us in fraction
  unsigned long lastTime;  //number that count in second represent ms and us in fraction
  int id;                  // this will track the count of verified records
};

template<typename T>
class CircularBuffer {
private:
  T buffer[BUFFER_SIZE];
  int head = 0;   // next write position
  int count = 0;  // number of stored records

public:
  //  add() that adds record only if time difference > bounder
  // and assigns a sequential id (each soild passing) automatically
  // bounder in ms
  bool add(unsigned long time, unsigned long bounder) {
    unsigned long lastTime = 0;
    if (count > 0) {
      // last stored record is at position (head - 1) wrapped
      int lastIdx = (head + BUFFER_SIZE - 1) % BUFFER_SIZE;
      lastTime = buffer[lastIdx].time;
    }

    // Calculate time difference (there has bug)
    unsigned long diff;
    if (count == 0) {
      diff = bounder + 1000;  // in ms
    } else {
      if (time > lastTime) {
        diff = time - lastTime;
      } else {
        diff = lastTime - time;
      }
    }

    // Add only if far enough apart form last record
    if (diff > bounder) {
      // Create the new record
      Record rec;
      rec.time = time;
      rec.lastTime = lastTime;
      rec.id = count + 1;  // id = count of verified records so far + 1

      // Add to buffer
      buffer[head] = rec;
      head = (head + 1) % BUFFER_SIZE;
      if (count < BUFFER_SIZE) count++;

      // Return success
      return true;
    }

    // Too close in time, skip adding
    return false;
  }

  void print() const {
  }
  // clear the data by overwrite from 0
  void clear() {
    count = 0;
  }
  int size() const {
    return count;
  }

  Record get(int id) const {
    // may have add bounds checking here
    return buffer[id];
  }
};

CircularBuffer<Record> data_buffer;

String serializeBufferToJson(const CircularBuffer<Record>& buffer) {
  String json = "[";
  for (int i = 0; i < buffer.size(); i++) {
    Record rec = buffer.get(i);
    json += "{";
    json += "\"time\":" + String(rec.time) + ",";
    json += "\"lastTime\":" + String(rec.lastTime);
    json += "\"difference\":" + String(rec.time - rec.lastTime);
    json += "}";
    if (i < buffer.size() - 1) json += ",";
  }
  json += "]";
  return json;
}

bool uploadData_fromBuffer() {
  HTTPClient http;
  http.begin("serverUrl");
  http.addHeader("Content-Type", "application/json");

  String jsonPayload = serializeBufferToJson(data_buffer);  // serialize your buffer to JSON string

  int code = http.POST(jsonPayload);

  bool status = false;
  if (code > 0) {
    Serial.printf("HTTP code: %d\n", code);
    String resp = http.getString();
    Serial.println(resp);
    status = (code == 200);  // status if HTTP 200 OK then is sucess else failed
  } else {
    Serial.printf("HTTP POST failed, error: %s\n", http.errorToString(code).c_str());
  }

  http.end();
  return status;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(1000);

  // Initialize Wifi and Time
  WiFi.begin(Wifi_ssid, Wifi_password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  configTime(8 * 3600, 0, "1.hk.pool.ntp.org", "time.nist.gov");

  Serial.println("Waiting for time");
  time_t now = time(nullptr);

  while (now < 8 * 3600 * 2) {  // wait for time to be set
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("\nTime has been settled");

  // Initialize HC-SR04 pins
  pinMode(TRIGPIN, OUTPUT);
  pinMode(ECHOPIN, INPUT);

  Serial.println("DHT11 and HC-SR04 test starting...");
}

constexpr float Exit1_max_distance = 20.0f;  // in cm
constexpr float Exit2_max_distance = 0.0f;
constexpr float max_distance = Exit1_max_distance;

constexpr int Timeout_with_max_distance = static_cast<int>((max_distance * 2 * 1.2) / 0.0343);

unsigned long time_difference_bounder = 1000000;  // minimal time difference to add record in us
float detect_bounder = 0.6;

unsigned long lastUploadTime = 0;
const unsigned long uploadInterval = 10000;  // 10 seconds

bool dataPending = false;

void loop() {
  // put your main code here, to run repeatedly:


  long duration = 0;
  float distance = 0;


  // ----- Read HC-SR04 -----
  // Send a 10us HIGH pulse to TRIG
  digitalWrite(TRIGPIN, LOW);
  delayMicroseconds(1);
  digitalWrite(TRIGPIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGPIN, LOW);

  // Read the duration of the echo pulse
  // Timeout etc: Timeout_with_max_distance = 30 (max ~5m distance)
  duration = pulseIn(ECHOPIN, HIGH, 30000);  // in us

  if (duration == 0) {
    Serial.println("No pulse received from HC-SR04");
  }
  else {
    // Calculate distance in cm
    distance = duration * 0.0343 / 2;

    // if detect_bounder has been triggered wihch means someone passed
    // create a new instance for saving record
    // update it to store at buff
    if (distance <= detect_bounder * max_distance) {
      Record current_rec;

      time_t now_sec = time(nullptr);
      int64_t now_us = esp_timer_get_time();
      unsigned long long precise_time__in_us = (unsigned long long)now_sec * 1000000ULL + (now_us % 1000000);

      Serial.print("Precise timestamp (us): ");
      Serial.println(precise_time__in_us);

      if (data_buffer.add(precise_time__in_us, time_difference_bounder)) {
        Serial.println("Record is saved");


        // upload data when the buff is almost full and give some space when the upload is fail
        if (dataPending && WiFi.status() == WL_CONNECTED && data_buffer.size() >= (BUFFER_SIZE - 20)) {
          if (uploadData_fromBuffer()) {
            Serial.println("Upload successful, clearing flag");
            dataPending = false;  // clear flag on success
            data_buffer.clear();  // optionally clear buffer after upload by overwrite the data from 0 idx

          } else {
            Serial.println("Upload failed, will retry later");
            // keep flag true for retry next loop}
          }
        }
      } else {
        Serial.println("Record is failed");
      }
    }
  }
    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println("cm");
    Serial.println("--------------------------");

    delay(200);  // Wait 0.2 seconds before next reading
}
