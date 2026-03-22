CODEBREAKER_PRESETS = {

# ── Code Breaker Progression Series ──────────────────────────────────
# Single progression sketch using //>> and //?? flags.
# The parser builds all 8 steps from one sketch file.
# Previous work accumulates automatically — no repetition.
#
# Usage in presets.py:
#   from codebreaker_presets import CODEBREAKER_PRESETS
#   PRESETS.update(CODEBREAKER_PRESETS)

    'codebreaker': {
        'sketch': """
//>> Step 1 - The Variables | guided
//?? Declare the secret word
String answer = "SPARK";
//?? Declare the score tracker
int likeness = 0;
//?? Declare the solved flag
bool solved = false;

void setup() {
}
void loop() {
}

//>> Step 2 - Serial Begin | guided
void setup() {
  //?? Start serial communication
  Serial.begin(9600);
  //## Serial.println("================================");
  //## Serial.println("     C O D E  B R E A K E R    ");
  //## Serial.println("================================");
  //## Serial.println("Find the hidden 5-letter word.");
  //## Serial.println("");
  //## Serial.println("X K Q S P A R K M Z");
  //## Serial.println("B R T F L A M E Q X");
  //## Serial.println("P Q S P A R K T Z R");
  //## Serial.println("W Z X B R A N D T P");
  //## Serial.println("S P A R K X Q Z B M");
  //## Serial.println("T R X N G L O W K B");
  //## Serial.println("Q Z B S P A R K X T");
  //## Serial.println("M X T R B L A Z E P");
  //## Serial.println("B T Z X Q M R N V K");
  //## Serial.println("P N V Q Z B X T M R");
  //## Serial.println("");
  //## Serial.println("Enter your guess:");
}
void loop() {
}

//>> Step 3 - Listen for Input | guided
void setup() {
}
void loop() {
  //?? Listen for player input
  if (Serial.available() > 0) {
  }
}

//>> Step 4 - Read the Guess | guided
void setup() {
}
void loop() {
  //## if (Serial.available() > 0) {
  //?? Read the player's guess
  String guess = Serial.readString(); // includes .trim() and .toUpperCase()
  //##   guess.trim();
  //##   guess.toUpperCase();
  //## }
}

//>> Step 5 - Reset the Score | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //?? Reset the score before counting
  likeness = 0;
  //## }
}

//>> Step 6 - The Letter Checker | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //## }
}

//>> Step 7 - Print the Result | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //?? Print the score label
  Serial.println("Likeness = ");
  //?? Print the score value
  Serial.print(likeness);
  //## }
}

//>> Step 8 - Win or Try Again | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //##   Serial.print("Likeness = ");
  //##   Serial.println(likeness);
  //?? Print the win message
  if (likeness == 5) {
    //?? Show success
    Serial.println("CODE CRACKED! ACCESS GRANTED.");
    //?? Unlock the game
    solved = true;
  } else {
    //?? Prompt to retry
    Serial.println("Try again:");
  }
  //## }
}

//>> Step 9 - Code Cracker Complete | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //##   Serial.print("Likeness = ");
  //##   Serial.println(likeness);
  //##   if (likeness == 5) {
  //##     Serial.println("CODE CRACKED! ACCESS GRANTED.");
  //##     solved = true;
  //##   } else {
  //##     Serial.println("Try again:");
  //##   }
  //## }
}
""",
    },

}    
