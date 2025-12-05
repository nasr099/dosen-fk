# Operations Runbook

Medical Exam Preparation Web Application

---

## 1. Overview

This document describes how to operate the project on your Mac, from turning the computer on to shutting everything down.

- Project folder: `/Users/andrifa95/Documents/01dosenfk`
- Backend: FastAPI (Python 3.11) in `backend/`
- Database: PostgreSQL (Homebrew `postgresql@15`), DB name `medical_exam_db`
- Frontend: Vue 3 + Vite in `frontend/`

---

## 2. Startup Procedure (from power on)

### 2.1 Log in and open terminal

1. Turn on the Mac and log in.
2. Open **Terminal** (or iTerm).

All commands below assume the same user account and default shell (zsh).

---

### 2.2 Start PostgreSQL

PostgreSQL is installed via Homebrew as `postgresql@15`.

```bash
brew services start postgresql@15
```

Optional: verify that it is running

```bash
brew services list | grep postgresql
```

---

### 2.3 Start the backend API

1. Go to the backend folder and activate the virtual environment:

```bash
cd /Users/andrifa95/Documents/01dosenfk/backend
source venv/bin/activate
```

2. Run the FastAPI server with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Keep this terminal **open**; the backend logs and requests will appear here.

Check it in the browser:

- `http://localhost:8000/` – simple health message.
- `http://localhost:8000/docs` – interactive API documentation.

---

### 2.4 Start the frontend

Open a **second** terminal window or tab.

1. Go to the frontend folder:

```bash
cd /Users/andrifa95/Documents/01dosenfk/frontend
```

2. Start the Vite dev server:

```bash
npm run dev
```

Vite will show something like:

```text
VITE vX.X.X  ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173/` in your browser to use the app.

At this point:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Database: PostgreSQL service started by Homebrew

---

## 3. During Operation

- Keep the following running:
  - Backend terminal with `uvicorn`.
  - Frontend terminal with `npm run dev`.
- Watch backend logs for API errors and database issues.
- Watch frontend logs for build errors or network errors.

If something crashes:

- **Backend**: re-run `uvicorn main:app ...` after fixing the error.
- **Frontend**: re-run `npm run dev`.

---

## 4. Shutdown Procedure (end of day)

Follow this order when you are done working.

### 4.1 Stop the frontend dev server

In the terminal where `npm run dev` is running (frontend):

- Press `Ctrl + C`.

You should see Vite stopping and returning to a shell prompt.

---

### 4.2 Stop the backend server

In the terminal where `uvicorn` is running (backend):

- Press `Ctrl + C`.

Optional: deactivate the Python virtual environment:

```bash
deactivate
```

---

### 4.3 Stop PostgreSQL

From any terminal window:

```bash
brew services stop postgresql@15
```

Optional: confirm it is stopped:

```bash
brew services list | grep postgresql
```

---

### 4.4 Close tools and shut down macOS

1. Close Terminal, IDE (VS Code, etc.), and browser windows.
2. Shut down the Mac from the Apple menu:

- **Apple logo → Shut Down…**

---

## 5. Notes

- If you pull new backend dependencies, reinstall with:

```bash
cd /Users/andrifa95/Documents/01dosenfk/backend
source venv/bin/activate
pip install -r requirements.txt
```

- If you pull new frontend dependencies, reinstall with:

```bash
cd /Users/andrifa95/Documents/01dosenfk/frontend
npm install
```

- Database migrations (only when needed):

```bash
cd /Users/andrifa95/Documents/01dosenfk/backend
source venv/bin/activate
alembic upgrade head
```
