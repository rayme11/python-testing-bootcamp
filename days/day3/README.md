# Day 3

Great 🚀 Let’s move on with **Day 03**, keeping the same detailed format as Day 01 and Day 02. This time we introduce one of pytest’s most powerful features: **fixtures**.

Here’s the dedicated README for Day 03:

---

### 📂 File: `days/day03/README.md`

````markdown
# Day 03 - Pytest Fixtures: Setup and Teardown Made Easy

Welcome to **Day 3** of the Python Testing Bootcamp!  

Today we’ll explore **pytest fixtures**, which allow us to:
- Prepare test data or environments before each test runs.
- Clean up resources afterwards.
- Share setup logic across multiple tests.

Fixtures are essential when testing **real applications**, because you often need to:
- Connect to databases.
- Populate test data.
- Reset state between tests.

---

## 🎯 Goals
By the end of today you will:
- Understand how **fixtures** work in pytest.
- Write your own fixtures for reusable setup.
- Use `yield` to provide **setup + teardown** logic.
- Apply fixtures automatically or selectively.
- Understand **fixture scope** (function, class, module, session).

---

## 🛠 Step by Step

### 1. Creating a Simple Fixture
Fixtures are defined using the `@pytest.fixture` decorator.

➡️ Create a new file: `tests/test_day03_fixtures.py`

```python
import pytest

@pytest.fixture
def sample_data():
    return {"name": "Ray", "role": "QA Manager"}

def test_user_has_name(sample_data):
    assert "name" in sample_data
    assert sample_data["name"] == "Ray"

def test_user_role(sample_data):
    assert sample_data["role"] == "QA Manager"
````

Run it:

```bash
pytest -v
```

✅ Notice that `sample_data` was automatically passed into the test functions.

---

### 2. Fixture with Setup + Teardown

Fixtures can use `yield` to provide **setup** before the test and **cleanup** after.

```python
import pytest

@pytest.fixture
def open_file(tmp_path):
    file = tmp_path / "test.txt"
    f = open(file, "w+")
    yield f   # this is where the test runs
    f.close() # cleanup after test

def test_write_and_read(open_file):
    open_file.write("hello world")
    open_file.seek(0)
    content = open_file.read()
    assert content == "hello world"
```

---

### 3. Fixture Scope

Fixtures can run at different scopes:

* `function` (default): runs before **every test**.
* `class`: runs once per test class.
* `module`: runs once per test file.
* `session`: runs once per test session (all tests).

Example:

```python
@pytest.fixture(scope="module")
def shared_resource():
    print(">>> setup once for module")
    return [1, 2, 3]

def test_one(shared_resource):
    assert 1 in shared_resource

def test_two(shared_resource):
    assert 2 in shared_resource
```

Output will show the fixture ran only **once**, not before each test.

---

### 4. Autouse Fixtures

Sometimes you want a fixture to **always run** without explicitly requesting it.

```python
@pytest.fixture(autouse=True)
def run_before_each_test():
    print(">>> this runs automatically before each test")
```

---

### 5. Using Fixtures in Classes

Fixtures can be used inside test classes too:

```python
class TestWithFixtures:
    @pytest.fixture
    def numbers(self):
        return [1, 2, 3]

    def test_sum(self, numbers):
        assert sum(numbers) == 6

    def test_length(self, numbers):
        assert len(numbers) == 3
```

---

## 🧠 Theory

### Why Fixtures Matter

* They prevent **duplicate setup code** in each test.
* Make tests **cleaner** and easier to maintain.
* Allow you to **reuse setup logic** across hundreds of tests.
* Handle **cleanup automatically** (closing files, rolling back databases, stopping servers).

### Example Without Fixtures

```python
def test_example():
    db = connect()
    db.seed()
    result = db.query()
    db.close()
```

### Example With Fixture

```python
@pytest.fixture
def db():
    db = connect()
    db.seed()
    yield db
    db.close()

def test_example(db):
    result = db.query()
```

➡️ Much cleaner!

---

## ✅ Summary

Today we learned:

* Fixtures provide **setup/teardown** for tests.
* They can be **scoped** to function, class, module, or session.
* They can run automatically (`autouse=True`) or be explicitly requested.
* Fixtures make tests **cleaner, reusable, and maintainable**.

Tomorrow (Day 4), we’ll learn about **parameterized tests** in pytest,
which allow us to run one test with many sets of data.

```

---

```

Run:
```bash
./scripts/start.sh
```
