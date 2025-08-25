# Day 1

Perfect 👍 Let’s begin with **Day 01**, fully detailed in its own `README.md` inside `days/day01/`.

Here’s the complete content for that file, in the same expanded and structured style we’ve been using:

---

### 📂 File: `days/day01/README.md`

````markdown
# Day 01 - Bootcamp Setup & First Test

Welcome to **Day 1** of the Python Testing Bootcamp!  
This day is all about **getting the foundation ready**: setting up the environment, running your first test, and understanding the big picture.

---

## 🎯 Goals
By the end of this day, you will:
- Set up a working Python environment for testing.
- Install dependencies needed for our future work.
- Understand how to structure a Python project for tests.
- Write and run your first `pytest` test.
- Learn about the **testing philosophy** we’ll follow in this bootcamp.

---

## 🛠 Step by Step

### 1. Verify Python is Installed
We will use **Python 3.12** (Codespaces defaults to this or similar).  
Check your version:

```bash
python3 --version
````

If it prints something like `Python 3.12.x`, you’re ready.

---

### 2. Create Virtual Environment (Optional but Recommended)

Although Codespaces already isolates dependencies, let’s make a clean environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

We will use `pytest` as our main testing tool.
Install it from `requirements.txt` (already included in the repo):

```bash
pip install -r requirements.txt
```

If you just want to install pytest manually:

```bash
pip install pytest
```

---

### 4. Create the First Test

Let’s add a simple test file in `tests/test_day01.py`.

```python
def test_addition():
    assert 1 + 1 == 2
```

---

### 5. Run the Test

Run all tests with:

```bash
pytest -v
```

Output should look like:

```
tests/test_day01.py::test_addition PASSED
```

---

### 6. Project Structure

We start with a very simple structure:

```
python-testing-bootcamp/
├── days/
│   ├── day01/
│   │   └── README.md     # This file
├── tests/
│   └── test_day01.py     # First test
├── requirements.txt
└── scripts/
    └── start.sh
```

This structure will grow over the days.

---

## 🧠 Theory

### Why Testing?

* Testing ensures software works as expected.
* Automated tests allow quick verification after every change.
* We can prevent regressions (bugs reappearing).
* In professional teams, tests act as **living documentation**.

### What is Pytest?

* `pytest` is the most popular testing framework in Python.
* Features:

  * Simple syntax (just use `assert`).
  * Auto-discovery of tests in `test_*.py` files.
  * Rich plugins ecosystem (e.g., coverage, async testing).
  * Integrates well with CI/CD pipelines.

---

## ✅ Summary

* Installed Python & pytest.
* Wrote the first test (`1 + 1 == 2`).
* Learned about the importance of testing and pytest basics.
* Established the project structure we’ll expand each day.

Tomorrow (Day 2), we’ll dive deeper into **pytest basics**:
test discovery, organizing tests, and using assertions.

```

---

```


Run:
```bash
./scripts/start.sh
```
