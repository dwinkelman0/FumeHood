void setup() {
    // Create serial connection
    Serial.begin(9600);
}

void loop() {
    // Output voltage from IR sensor to analog pin
    char buf[6];
    sprintf(buf, "%i", analogRead(0));
    Serial.println(buf);
    delay(100);
}
