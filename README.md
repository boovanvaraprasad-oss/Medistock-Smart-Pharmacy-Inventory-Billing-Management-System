# MediStock

Smart Pharmacy Inventory & Billing Management System.

- **Backend:** Python, FastAPI, MongoDB (Motor)
- **Frontend:** HTML, CSS, JavaScript (served by FastAPI)
- **Security:** JWT access and refresh tokens, Bcrypt passwords, role-based permissions

## Requirements

- Python 3.11 or newer
- MongoDB running locally (default: `mongodb://localhost:27017`)

## First-time setup

1. Open a terminal in the `backend` folder.
2. Create and activate a virtual environment:

```
   python -m venv .venv
   .venv\Scripts\activate
```

3. Install the libraries:

```
   pip install -r requirements.txt
```

4. Copy `.env.example` to a new file named `.env` and set your own
   values, especially `JWT_SECRET_KEY` (use a long random text).
   Never share or commit the `.env` file.

## Run the project

From the `backend` folder:

```
uvicorn main:app --reload
```

- App and login page: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs

## Creating the first account

Public signup only works while the database has **no users**. The first
person to sign up becomes the **owner**. After that, the owner creates
staff accounts (pharmacist, inventory executive, and so on).

For local testing only, `python create_test_user.py` creates an owner
account. Do not use it in a real deployment, because its password is
written in the file.

## Roles

owner, pharmacist, inventory_executive, purchase_executive,
store_manager, compliance_officer.

What each role may do is defined in `backend/app/core/permissions.py`.