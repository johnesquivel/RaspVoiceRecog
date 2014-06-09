#include <Wire.h>

// Define pins
#define MICPIN A0
#define LEDPIN 13

// Microphone connects to Analog Pin 0.
#define ADC_CHANNEL 0

// Circular buffer size
#define BZ 200

int i, pac, bufStart, bufEnd;
int sample[BZ];

void setup()
{ 
    Serial.begin(230400);
    pinMode(MICPIN, INPUT);
    pinMode(LEDPIN, OUTPUT);
    digitalWrite(LEDPIN, HIGH);

    analogReference(EXTERNAL);
    // Init ADC free-run mode; f = ( 16MHz/prescaler ) / 13 cycles/conversion
    ADMUX  = ADC_CHANNEL; // Channel sel, right-adj, use AREF pin
    ADCSRA = _BV(ADEN)  | // ADC enable
            _BV(ADSC)  | // ADC start
            _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0); // 128:1 / 13 = 9615 Hz
    ADCSRB = 0;                // Free run mode, no high MUX bit
    DIDR0  = 1 << ADC_CHANNEL; // Turn off digital input for ADC pin
    TIMSK0 = 0;                // Timer0 off
    
    bufStart = 0;
    bufEnd = BZ/2;
}


void loop()
{
  
    // Sample the audio
    sample[bufEnd] = analogRead(MICPIN); // 0-1023

    // If the signal goes beyond  threshold, begin sending data.
    if ((sample[bufEnd] < 452) || (sample[bufEnd] > 572))
    {
        pac = 4;  // Start packet counter at header
        for (i=0; i < 2048; i++)
        {
            if (pac == 4)
            {
                Serial.print('H'); // Send a header character
                pac = 0; // reset packet counter
            }
            // Read sample 
            sample[bufEnd] = analogRead(MICPIN);
            // Truncate the 10bit number to 8bits and send
            sample[bufEnd] = sample[bufEnd] >> 2;
            Serial.write(lowByte(sample[bufStart]));
            //Serial.write(highByte(sample[bufStart]));
            pac += 1;

            // reset buffer pointer
            bufEnd += 1;
            bufStart += 1;
            if (bufEnd >= BZ) { bufEnd = 0; }
            if (bufStart >= BZ) { bufStart = 0; }
        }
        // Now that we send the data packet, set LED high until
        // we are ready to send again (after buffer refill)
        digitalWrite(LEDPIN, HIGH);
    }
        
    sample[bufEnd] = sample[bufEnd] >> 2;
    // reset buffer pointer
    bufEnd += 1;
    bufStart += 1;
    if (bufEnd >= BZ) { bufEnd = 0; }
    if (bufStart >= BZ)
    {
        bufStart = 0;
        // Let us know that the buffer has been
        // filled at least once.
        digitalWrite(LEDPIN, LOW);
    }
}
