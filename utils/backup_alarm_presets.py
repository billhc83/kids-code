BACKUP_ALARM_PRESETS = {


    'backup_alarm': {
        'sketch': """
//>> Step 1 - Define Global Variables | guided

//?? Define trigPin
int trigPin = 9;

//?? Define echoPin
int echoPin = 10;

//?? Define buzzerPin
int buzzerPin = 3;

//?? Define greenLED
int greenLED = 4;

//?? Define yellowLED
int yellowLED = 5;

//?? Define redLED
int redLED = 6;

//?? Define duration
long duration;

//?? Define distance
int distance;

void setup() {
    }
void loop() {
    }

//>> Step 2 - Setup the System | guided

void setup() {
  //?? Set trigPin as OUTPUT
  pinMode(trigPin, OUTPUT);

  //?? Set echoPin as INPUT
  pinMode(echoPin, INPUT);

  //?? Set buzzerPin as OUTPUT
  pinMode(buzzerPin, OUTPUT);

  //?? Set greenLED as OUTPUT
  pinMode(greenLED, OUTPUT);

  //?? Set yellowLED as OUTPUT
  pinMode(yellowLED, OUTPUT);

  //?? Set redLED as OUTPUT
  pinMode(redLED, OUTPUT);

  Serial.begin(9600);
}

void loop() {
}

//>> Step 3 - Prepare Sensor | guided

void loop() {
  //?? Set trigPin LOW
  digitalWrite(trigPin, LOW);

  //?? Small delay
  delayMicroseconds(2);
}

//>> Step 4 - Send Pulse | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);

  //?? Set trigPin HIGH
  digitalWrite(trigPin, HIGH);

  //?? Wait 10 microseconds
  delayMicroseconds(10);

  //?? Set trigPin LOW
  digitalWrite(trigPin, LOW);
}

//>> Step 5 - Read Echo | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);

  //?? Read duration from echoPin
  duration = pulseIn(echoPin, HIGH);
}

//>> Step 6 - Calculate Distance | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);

  //?? Convert duration to distance
  distance = duration * 0.034 / 2;
}

//>> Step 7 - Safe Zone Check | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;

  //?? If distance > 50
  if (distance > 50) {
  }
}

//>> Step 8 - Safe Zone Output | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## if (distance > 50) {

  //?? Turn buzzer OFF
  noTone(buzzerPin);

  //?? Turn green LED ON
  digitalWrite(greenLED, HIGH);

  //?? Turn yellow LED OFF
  digitalWrite(yellowLED, LOW);

  //?? Turn red LED OFF
  digitalWrite(redLED, LOW);

  //## }
}

//>> Step 9 - Warning Zone Check | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }

  //?? Else if distance > 20
  else if (distance > 20) {
  }
}

//>> Step 10 - Warning Zone Output | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {

  //?? Turn buzzer ON (1000 Hz)
  tone(buzzerPin, 1000);

  //?? Delay 300 ms
  delay(300);

  //?? Turn buzzer OFF
  noTone(buzzerPin);

  //?? Delay 300 ms
  delay(300);

  //?? Turn green LED OFF
  digitalWrite(greenLED, LOW);

  //?? Turn yellow LED ON
  digitalWrite(yellowLED, HIGH);

  //?? Turn red LED OFF
  digitalWrite(redLED, LOW);

  //## }
}

//>> Step 11 - Danger Zone | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }

  //?? Else (very close)
  else {

    //?? Turn buzzer ON (2000 Hz)
    tone(buzzerPin, 2000);

    //?? Turn green LED OFF
    digitalWrite(greenLED, LOW);

    //?? Turn yellow LED OFF
    digitalWrite(yellowLED, LOW);

    //?? Turn red LED ON
    digitalWrite(redLED, HIGH);
  }
}

//>> Step 12 - Loop Delay | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else {
  //##   tone(buzzerPin, 2000);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, HIGH);
  //## }

  //?? Small delay for stability
  delay(50);
}

//>> Step 13 - Complete System | locked

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else {
  //##   tone(buzzerPin, 2000);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, HIGH);
  //## }
  //## delay(50);
//##}
"""
    }
}