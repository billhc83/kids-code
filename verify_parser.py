import json
from utils.block_parser import parse_blocks, parse_sketch

test_code = """
int x = 10;
//?? Add 5 to x
x = x + 5;
if (x > 10) {
  digitalWrite(13, HIGH);
} else {
  digitalWrite(13, LOW);
}
"""

print("--- Testing parse_blocks ---")
blocks = parse_blocks(test_code, fill_values=True)
print(json.dumps(blocks, indent=2))

sketch_code = """
void setup() {
  Serial.begin(9600);
}
void loop() {
  int val = analogRead(A0);
  Serial.println(val);
  delay(100);
}
"""

print("\n--- Testing parse_sketch ---")
sketch = parse_sketch(sketch_code, fill_values=True)
print(json.dumps(sketch, indent=2))
