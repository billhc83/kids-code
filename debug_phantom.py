from lark import Lark
import time

with open('utils/arduino.lark', 'r') as f:
    grammar = f.read()

parser = Lark(grammar, start='block_list', parser='lalr')

test_code = """
int x = 10;
//?? Add 5 to x
x = x + 5;
"""

try:
    tree = parser.parse(test_code)
    print(tree.pretty())
except Exception as e:
    print(f"Error: {e}")
