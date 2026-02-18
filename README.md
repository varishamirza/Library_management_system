# Library_management_system
# 📚 Library Management System  A simple yet complete **Library Management System** with two versions:  - **Console version** – classic terminal interface   - **Web version** – modern browser interface built with Streamlit  Both versions share the same SQLite database and core logic.  
## ✨ Features

- Admin & User login (with password hashing)
- Add / Update library members
- Add / Update books & movies (with auto-generated serial numbers)
- Check availability
- Issue & Return items (with automatic late fine calculation – ₹1/day)
- Pay fines
- Reports:
  - Master list of books/movies
  - Active issues
  - Overdue items

## 🛠️ Technologies Used

| Layer              | Technology                  | Purpose                              |
|---------------------|-----------------------------|--------------------------------------|
| Language            | Python 3.8+                 | Core programming language            |
| Database            | SQLite                      | Lightweight, file-based database     |
| Web Framework       | Streamlit                   | Quick & beautiful data apps in Python|
| Data Presentation   | pandas                      | Clean tables in web interface        |
| Security            | hashlib (SHA-256)           | Password hashing                     |
| Date Handling       | datetime                    | Date validation & fine calculation   |

No external heavy frameworks, no JavaScript required for the web version.

## 📋 Project Structure
Library-Management-System/
├── library_management.py      ← Console version (full-featured terminal app)

## 🚀 How to Run

### 1. Prerequisites

- Python 3.8 or higher installed
- Git (optional – for cloning)

### 2. Clone or Download

```bash
git clone https://github.com/yourusername/Library-Management-System.git
cd Library-Management-System
# Recommended: create virtual environment first
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# Install required packages
pip install streamlit pandas
Option A: Console Version (terminal)
python library_management.py
Login credentials (default):

Admin: adm / adm
Normal user: user / user
Option B: Web Version (Streamlit – recommended)
streamlit run library_app.py
Browser will open automatically (usually http://localhost:8501)

├── library_app.py             ← Streamlit web version (browser interface)
├── library.db                 ← SQLite database (created automatically)
└── README.md
