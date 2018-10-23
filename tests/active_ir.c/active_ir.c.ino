void setup() {
    // Create serial connection
    Serial.begin(9600);
}

void loop() {
    // Output voltage from IR sensor to analog pin
    // High values are close, low values are far
    // Device targets distances between 0.2 and 1.5 meters
    // http://www.farnell.com/datasheets/1386113.pdf?_ga=2.110934277.1478548236.1540322089-1941483107.1539717387
    char buf[6];
    sprintf(buf, "%i", analogRead(0));
    Serial.println(buf);
    delay(100);
}
