# Day 2

Perfect 🙌 Let’s continue with **Day 02**, written in the same detailed style, and saved as `days/day02/README.md`.

---

### 📂 File: `days/day02/README.md`

````markdown
# Day 02 - Pytest Fundamentals: Discovery & Assertions

Welcome back!  
On **Day 2** we’ll focus on **learning pytest in more detail**:
- How pytest discovers tests.
- How to use assertions effectively.
- How to organize test files and functions.

---

## 🎯 Goals
By the end of today you will:
- Understand **pytest discovery rules**.
- Write multiple tests in a single file.
- Learn different **assertion styles**.
- Run specific tests instead of all at once.
- Understand why test naming matters.

---

## 🛠 Step by Step

### 1. Test Discovery Rules
Pytest will automatically find and run tests following these rules:

- Files must be named `test_*.py` or `*_test.py`.
- Test functions must start with `test_`.
- Test classes must start with `Test` and contain methods named `test_*`.

➡️ Let’s create `tests/test_day02_discovery.py`:

```python
def test_simple_math():
    assert 2 + 2 == 4

def test_strings():
    assert "hello".upper() == "HELLO"

class TestDiscovery:
    def test_inside_class(self):
        assert isinstance(123, int)
````

Run it:

```bash
pytest -v
```

---

### 2. Assertions in Detail

Pytest allows **plain Python `assert` statements**.
It automatically gives rich error messages when an assertion fails.

Example file: `tests/test_day02_asserts.py`

```python
def test_numbers():
    x = 5
    y = 10
    assert x + y == 15

def test_lists():
    mylist = [1, 2, 3]
    assert 2 in mylist
    assert len(mylist) == 3

def test_dicts():
    data = {"name": "Ray", "age": 30}
    assert data["name"] == "Ray"
    assert "age" in data
```

Run:

```bash
pytest -v
```

---

### 3. Running Specific Tests

* Run only one test file:

```bash
pytest tests/test_day02_asserts.py -v
```

* Run only one test function:

```bash
pytest -k "test_lists" -v
```

* Run only tests containing a keyword:

```bash
pytest -k "string" -v
```

---

### 4. Organizing Tests

By convention:

* All tests go inside a `tests/` folder.
* Group related tests together by feature.
* Use meaningful names.

Example structure now:

```
python-testing-bootcamp/
├── days/
│   ├── day01/
│   │   └── README.md
│   ├── day02/
│   │   └── README.md   # This file
├── tests/
│   ├── test_day01.py
│   ├── test_day02_discovery.py
│   └── test_day02_asserts.py
```

---

## 🧠 Theory

### Test Naming

* Clear names = self-documenting.
* Bad: `test_1`, `test_a`.
* Good: `test_user_login_redirects`, `test_cart_total_with_discount`.

### Assertions

* Unlike `unittest`, pytest does **not** require special assertion methods.
* Plain Python is enough: `assert a == b`.
* If it fails, pytest shows the **exact difference**.

Example failure:

```python
def test_fail():
    assert 1 + 1 == 3
```

Output:

```
>       assert 1 + 1 == 3
E       assert 2 == 3
```

---

## ✅ Summary

Today we learned:

* Pytest automatically **discovers tests** by naming rules.
* We can write multiple tests in one file.
* Assertions are simple but powerful with detailed error output.
* We can run specific tests when needed.
* Organized tests = maintainable tests.

Tomorrow (Day 3), we’ll learn about **pytest fixtures**,
a powerful feature to set up and clean up test environments.

```

---

```


Run:
```bash
./scripts/start.sh
```
