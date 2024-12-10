String modifyMessage(String receivedMessage) {
  return receivedMessage + " - Modified";
}

void setup() {
  Serial.begin(9600);
  Serial.println("Ready to receive messages");
}

void loop() {
  // Check if there is incoming data
  if (Serial.available() > 0) {
    String receivedMessage = Serial.readStringUntil('\n');
    
    String modifiedMessage = modifyMessage(receivedMessage);
    Serial.println(modifiedMessage);
  }
}

