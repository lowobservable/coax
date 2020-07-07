#include <Arduino.h>

#include <NewCoax.h>

NewCoaxDataBus dataBus;
NewCoaxReceiver receiver(dataBus);

uint16_t buffer[1024];

void setup()
{
    Serial.begin(115200);

    while (Serial.available() > 0) {
        Serial.read();
    }

    receiver.begin();
}

void loop()
{
    int count = receiver.receive(buffer, 1024, 1000);

    Serial.println(count);
}
