# define BUZZER_PIN   13
# define PIR_INPUT_PIN  2
 
int pirState = LOW;

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(PIR_INPUT_PIN, INPUT);
  Serial.begin(9600);
}

void loop() {
  if (digitalRead(PIR_INPUT_PIN) == HIGH) {
    playTone(300, 160);
    delay(150);
    
    if (pirState == LOW) {
      pirState = HIGH;
    }
  } else {
      playTone(0, 0);
      delay(300);    
      if (pirState == HIGH){
        pirState = LOW;
      }
  }
}

// duration in mSecs, frequency in hertz
void playTone(long duration, int freq) {
    duration *= 1000;
    int period = (1.0 / freq) * 1000000;
    long elapsed_time = 0;
    while (elapsed_time < duration) {
        digitalWrite(BUZZER_PIN, HIGH);
        delayMicroseconds(period / 2);
        digitalWrite(BUZZER_PIN, LOW);
        delayMicroseconds(period / 2);
        elapsed_time += (period);
    }
}