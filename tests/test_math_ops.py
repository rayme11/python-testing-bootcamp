# tests/test_math_ops.py
import pytest
from src.day2_basics import multiply

@pytest.mark.parametrize("a,b,result", [(2,2,4), (3,3,9)])
def test_multiply_param(a, b, result):
    assert multiply(a, b) == result
