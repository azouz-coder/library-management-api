# Train AI Automation — Library API

A backend library management API built with FastAPI and PostgreSQL as part of my journey toward AI Automation and AI Agent development.

## Features

- User registration and management
- User authentication with JWT
- Access and refresh tokens
- Role-based authorization
- Email verification
- Password reset
- Book CRUD operations
- Book search and filtering
- Book image upload
- Borrowing and returning books
- PostgreSQL database with SQLAlchemy and Alembic migrations
- Automated tests with pytest
- Environment variables for sensitive configuration

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT
- pytest
- Git & GitHub
- python-dotenv

## Project Structure

```
library-management-api/
├── app/
│   ├── book.py
│   ├── borrowing.py
│   ├── crud_book.py
│   ├── crud_borrowing.py
│   ├── crud_user.py
│   ├── database.py
│   ├── email_verification.py
│   ├── loggin_config.py
│   ├── login_user.py
│   ├── main.py
│   ├── models.py
│   ├── schema.py
│   ├── security.py
│   ├── tokens.py
│   └── users.py
├── migrations/
├── tests/
├── alembic.ini
├── pytest.ini
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

Clone the repository and enter the project directory:

```
git clone https://github.com/azouz-coder/library-management-api.git
cd library-management-api
```

Create a virtual environment:

```
python -m venv .venv
```

Activate it on Windows:

```
.venv\Scripts\activate
```

Activate it on Linux / macOS:

```
source .venv/bin/activate
```

Install the dependencies:

```
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```
SECRET_KEY=change_me

DB_HOST=localhost
DB_PORT=5432
DB_NAME=library
DB_USER=postgres
DB_PASSWORD=your_db_password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Optional: used to build the links in verification / reset emails
BASE_URL=http://localhost:8000
```

`SECRET_KEY` is required; the app refuses to start without it. Never commit your real `.env` file.

## Database Setup

Create an empty PostgreSQL database (the name you set in `DB_NAME`), then create the tables with Alembic:

```
alembic upgrade head
```

## Run the API

```
uvicorn app.main:app --reload
```

Then open the FastAPI documentation:

http://127.0.0.1:8000/docs

## Run Tests

```
pytest
```

The tests run against a temporary SQLite file, so they do not touch your PostgreSQL database.

The upload tests expect a few sample image files in the project root (`test_image.png`, `test_image.jpg`, `test_image.ico`, `carbon (49).png` and `watsup.jpeg`). They are listed in `.gitignore`, so add your own copies before running those tests.

## Purpose

This project was built to practice backend development fundamentals that are useful for building automation systems and AI-powered applications.

The next stages of the learning path will focus on automation, AI APIs, and AI agents.
