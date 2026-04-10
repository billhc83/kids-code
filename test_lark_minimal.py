from lark import Lark
import time

with open('utils/arduino.lark', 'r') as f:
    grammar = f.read()

print("Loading parser...")
parser = Lark(grammar, start='block_list', parser='lalr')

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

print("Parsing...")
start = time.time()
try:
    tree = parser.parse(test_code)
    print(f"Success in {time.time() - start:.2f}s")
    print(tree.pretty())
except Exception as e:
    print(f"Error: {e}")
