# Python Testing Bootcamp

This repository contains a 3-month learning course focused on Python testing, API development, MongoDB, GraphQL, and modern testing frameworks — all built and tested inside GitHub Codespaces.

---

## Getting Started

### Prerequisites

- A GitHub account with access to **GitHub Codespaces**
- Basic knowledge of Python and testing concepts

---

## Setup

1. **Open this repository in GitHub Codespaces:**

   - Click the green **Code** button → select **Codespaces** → **Create codespace on main**

2. **Environment**

   This project uses a `.devcontainer` folder to automatically configure the development environment inside Codespaces:

   - Python 3.11
   - FastAPI web framework
   - MongoDB drivers (`motor`, `pymongo`)
   - GraphQL (`graphene`)
   - Testing tools (`pytest`, `pytest-asyncio`, `httpx`, `faker`)

3. **Install dependencies**

   Dependencies are automatically installed when Codespaces container builds.  
   If you open the repo locally, run:

   ```bash
   pip install -r requirements.txt
