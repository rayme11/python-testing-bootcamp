# Python Testing Bootcamp – Day 0 (Introduction)

Welcome to the **Python Testing Bootcamp** 🚀.  
This training course is designed to walk you step-by-step through building and testing a real-world **FastAPI + MongoDB + GraphQL** application inside **GitHub Codespaces**.

---

## 🎯 How This Bootcamp Works

Each **day** introduces new concepts, code changes, and tests.  
You’ll progressively build a full-stack backend with REST and GraphQL APIs, authentication, database integration, and automated testing.

---

## ⚠️ Important Note About Errors & Refactoring

This bootcamp is **not** meant to be a perfect “copy–paste and everything works immediately” tutorial.

Instead:

- **Some days will contain intentional errors or incomplete code.**
  - This is by design. Debugging is part of the learning process.
  - You will encounter issues like schema mismatches, missing fixtures, async loop errors, etc.

- **Why?**  
  Because real-world software development is messy. You rarely get everything right the first time.  
  Learning how to read error messages, ask the right questions, and refactor code is just as important as writing it.

- **Your Mission:**  
  When you hit an error, don’t panic.  
  Use AI assistants (like ChatGPT), search engines, documentation, and community resources to:
  - Understand the error
  - Propose solutions
  - Apply fixes
  - Keep refactoring until it works

- **Pro Tip:** Ask “why” often. Instead of just fixing errors, dig into what caused them. That’s where the real learning happens.

---

## 🧭 Suggested Workflow

1. **Follow the steps for the day** in the corresponding `dayN/README.md`.
2. **Run the code/tests** — expect that something might break.
3. **Investigate errors**:
   - Read stack traces carefully
   - Check the docs (FastAPI, Pytest, Strawberry GraphQL, Motor/MongoDB)
   - Ask AI or online resources
4. **Refactor** until tests pass.
5. **Commit your changes** before moving on to the next day.

---

## ⚡ How to Start Everything

This project comes with a script (`./scripts/start.sh`) that sets up and runs all necessary services.

### 1️⃣ Run Autostart Script

```bash
chmod +x scripts/start.sh
./scripts/start.sh
