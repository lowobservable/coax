#include <Arduino.h>

#define RESET_PIN 2 // FPGA #9

char buffer[20 + 1];
int bufferIndex = 0;

void doReset()
{
    Serial.println("RESET");

    digitalWrite(RESET_PIN, HIGH);
    digitalWrite(RESET_PIN, LOW);

    Serial.println("OK");
}

void setup()
{
    pinMode(RESET_PIN, OUTPUT);

    digitalWrite(RESET_PIN, LOW);

    Serial.begin(115200);

    while (Serial.available() > 0) {
        Serial.read();
    }

    Serial.println("OK");
}

void loop()
{
    if (Serial.available() > 0) {
        uint8_t byte = Serial.read();

        if (byte == '\r') {
            buffer[bufferIndex] = 0;

            Serial.println();

            if (strncmp(buffer, "reset", 20) == 0) {
                doReset();
            } else {
                Serial.println("UNRECOGNIZED COMMAND");
            }

            Serial.flush();

            bufferIndex = 0;
        } else {
            buffer[bufferIndex++] = byte;
        }

        Serial.write(byte);
        Serial.flush();
    }
}
