void setup() {
  // Set pin modes
  Serial.begin(9600);
  Serial.write("Hello World");
}

void loop() {
  int val = analogRead(A0);
  char buf[16];
  sprintf(buf, "%i\n", val);
  Serial.write(buf);
}
