# tests/test_math_ops.py
from src.day2_basics import multiply

def test_multiply_param(multiply_data):
    a, b, expected = multiply_data
    assert multiply(a, b) == expected
