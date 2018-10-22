const uint8_t PIN_IN_BUTTON = 4;
const uint8_t PIN_OUT_YELLOW = 5;

uint32_t override = 0;
const uint32_t OVERRIDE_INC_MS = 10;
const uint32_t OVERRIDE_MAX_MS = 1000;

void setup() {
    // Initialize indicator LED
    pinMode(PIN_OUT_YELLOW, OUTPUT);
}

void loop() {
    // Read the button input pin;
    // If the override is engaged, wait; else clear
    boolean state = digitalRead(PIN_IN_BUTTON);
    if (state) override += OVERRIDE_INC_MS;
    else override = 0;

    // Check if override has been pressed for long enough
    if (override > OVERRIDE_MAX_MS) {
        override = 0;
        digitalWrite(PIN_OUT_YELLOW, HIGH);
        delay(1000);
        digitalWrite(PIN_OUT_YELLOW, LOW);
    }

    delay(OVERRIDE_INC_MS);
}
