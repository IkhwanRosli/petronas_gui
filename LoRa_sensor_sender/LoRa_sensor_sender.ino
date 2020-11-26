#include "Adafruit_VL53L0X.h"
#include <SPI.h>
#include <LoRa.h>
const unsigned long SECOND = 1000;
const unsigned long MINUTE = 60*SECOND;
const unsigned long HOUR = 60*MINUTE;
Adafruit_VL53L0X lox = Adafruit_VL53L0X();
const int x = 0;
const int y = 1;
const int z = 2;
void setup() {
  Serial.begin(9600);

 while (! Serial) {
    delay(1);
  }

  Serial.println("LoRa Sender");
  if (!lox.begin()) {
    Serial.println(F("Failed to boot VL53L0X"));
    while(1);
  }

  if (!LoRa.begin(915E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  
}


void loop() {
  VL53L0X_RangingMeasurementData_t measure;
    
  Serial.print("Reading a measurement...  ");
  lox.rangingTest(&measure, false); // pass in 'true' to get debug data printout!
  LoRa.beginPacket();
  if (measure.RangeStatus != 4) {  // phase failures have incorrect data
    LoRa.print(x);
    LoRa.print(",");
    LoRa.print(measure.RangeMilliMeter);
    
    Serial.println(measure.RangeMilliMeter);
  } else {
    LoRa.print(" out of range ");
    Serial.println(" out of range ");
  }
   LoRa.endPacket(); 
  delay(10*SECOND);  
}
