def greet(name: str) -> str:
    return f"Hello, {name}"

def multiply(a: int, b: int) -> int:
    return a * b

def is_even(number: int) -> bool:
    return number % 2 == 0

def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("Negative values are not allowed")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
