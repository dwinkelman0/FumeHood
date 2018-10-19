/******************************************************************************
 * TEAM FUME HOOD
 * Sensing Module
 *
 * Daniel Winkelman <ddw30@duke.edu>
 * Duke University
 * EGR 101
 *
 * Summary:
 *    This is a quick test for an array of passive light sensors. A line of
 *    phototransistors has a baseline resistance, interpreted by the Arduino as
 *    an analog voltage; higher voltage indicates more light reaching the
 *    phototransistor. A rapid change in any of the phototransistors from the
 *    baseline brightness indicates motion within the plane of the sash.
 */



/******************************************************************************
 * Debugging commands (with serial to IDE)
 */
#define SERIAL_DEBUG

void serial_setup() {
#ifdef SERIAL_DEBUG
    Serial.begin(9600);
#endif
}

void println(const char * str) {
#ifdef SERIAL_DEBUG
    Serial.println(str);
#endif
}



/******************************************************************************
 * Define constants and persistent memory
 */

// Frame rate (frames per second)
const int32_t FPS = 40;

// Timeout until closure signal sent
const int32_t MAX_TIMEOUT_MS = 15 * 1000000; // 15 seconds
const int32_t TIMEOUT_INC_MS = 1000000 / FPS;

int32_t timeout_ms = MAX_TIMEOUT_MS;

// Sensor input pins
const uint16_t N_PIN_INPUT_PHOTO = 1;
const uint16_t PIN_INPUT_PHOTO[N_PIN_INPUT_PHOTO] = { 1 };

// Analog input difference threshold needed to trigger timeout reset
const uint16_t SENSITIVITY = 50;

// Phototransistor voltage state buffer
//
// Assuming that the buffer is 4 samples large....
//     --back---   --head---
//    [ * * * * ] [ - - - - ]   (* = stored sample)
//      0 1 2 3     4 5 6 7     (- = empty sample)
//                              (X = selected stored sample)
// 4 looks back at 1...         (O = new sample)
//    [ X * * * ] [ O - - - ]
//
// 5 looks back at 2...
//    [ * X * * ] [ * O - - ]
//
// and so on...
//
//    [ * * * * ] [ * * * * ]
//                  =======---------> These four at pos. 4-7 go to pos. 0-3
//
// and repeat
//
// NOTE: buffer needs to be twice the size as the number of samples
const uint16_t N_BUFFER_SAMPLES = 10;
int16_t buffer_head[N_BUFFER_SAMPLES][N_PIN_INPUT_PHOTO];
int16_t buffer_back[N_BUFFER_SAMPLES][N_PIN_INPUT_PHOTO];

// Indicator LED timeouts
const uint8_t PIN_OUTPUT_GREEN = 0;
const uint8_t PIN_OUTPUT_RED = 1;
const int32_t MAX_TIMEOUT_GREEN_MS = 1000000;
const int32_t MAX_TIMEOUT_RED_MS = 500000;
int32_t timeout_green_ms = 0;
int32_t timeout_red_ms = 0;


/******************************************************************************
 * Close sash
 */
void close_sash() {
    println("Close Sash!");

    // Signal to green LED
    // TODO: Implement interrupt system if the sensors detect motion while closing
    digitalWrite(PIN_OUTPUT_GREEN, HIGH);
    delay(MAX_TIMEOUT_GREEN_MS);
    digitalWrite(PIN_OUTPUT_RED, LOW);
}



/******************************************************************************
 * Initialization
 */
void setup() {
    // Set up debug serial connection
    serial_setup();

    // Set up LED indicator pins
    pinMode(PIN_OUTPUT_GREEN, OUTPUT);
    pinMode(PIN_OUTPUT_RED, OUTPUT);

    // Populate buffer with initial analog pin values
    for (uint16_t pin_i = 0; pin_i < N_PIN_INPUT_PHOTO; pin_i++) {
        
        // Read the pin value and copy to first half of buffer
        int16_t state = analogRead(PIN_INPUT_PHOTO[pin_i]);
        for (uint16_t buf_i = 0; buf_i < N_BUFFER_SAMPLES; buf_i++) {
            buffer_back[buf_i][pin_i] = state;
        }
    }
}



/******************************************************************************
 * Program Loop
 */
void loop() {
    // For each element in the buffer
    for (uint16_t buf_i = 0; buf_i < N_BUFFER_SAMPLES; buf_i++) {
        
        // For each pin
        for (uint16_t pin_i = 0; pin_i < N_PIN_INPUT_PHOTO; pin_i++) {
            
            // Read value and place into buffer
            int16_t value = analogRead(PIN_INPUT_PHOTO[pin_i]);
            
            buffer_head[buf_i][pin_i] = value;
            
            // Get difference between two samples
            int16_t difference = buffer_head[buf_i][pin_i] - buffer_back[buf_i][pin_i];
            
            // If the difference exceeds a threshold, then set a reset
            if (abs(difference) > SENSITIVITY) {
                timeout_ms = MAX_TIMEOUT_MS;

                // Signal to red LED
                digitalWrite(1, HIGH);
                timeout_red_ms = MAX_TIMEOUT_RED_MS;
            }
        }
        
        // Wait until next cycle
        delayMicroseconds(TIMEOUT_INC_MS);

        timeout_red_ms -= TIMEOUT_INC_MS;
        if (timeout_red_ms < 0) {
            digitalWrite(PIN_OUTPUT_RED, LOW);
        }
        
        // Decrement timeout
        timeout_ms -= TIMEOUT_INC_MS;
        
        // Check if time to close sash
        if (timeout_ms < 0) {
            close_sash();
        }
    }

    // Swap the second half of the buffer with the first half
    const uint16_t BLOCK_SIZE =
        N_BUFFER_SAMPLES * N_PIN_INPUT_PHOTO * sizeof(uint16_t);
    memcpy(buffer_back, buffer_head, BLOCK_SIZE);
}
