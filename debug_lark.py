from lark import Lark
import os

GRAMMAR_PATH = 'utils/arduino.lark'
with open(GRAMMAR_PATH, 'r') as f:
    grammar = f.read()

parser = Lark(grammar, start='block_list', parser='lalr')

test_code = "int x = 10;"
try:
    tree = parser.parse(test_code)
    print(tree.pretty())
except Exception as e:
    print(f"Error: {e}")
