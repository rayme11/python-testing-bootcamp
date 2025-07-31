from src.day2_basics import greet, multiply, is_even, factorial
import pytest

def test_greet():
    assert greet("Ray") == "Hello, Ray"

def test_multiply():
    assert multiply(3, 4) == 12

def test_is_even():
    assert is_even(2) is True
    assert is_even(3) is False

def test_factorial():
    assert factorial(5) == 120
    assert factorial(0) == 1

    with pytest.raises(ValueError):
        factorial(-1)
