# Videoflix Backend

![Videoflix Logo](logo_icon.svg)

This repository contains the Django REST Framework–based backend for **Videoflix**, a Netflix-style demo app with email activation, JWT cookie auth, password reset, and HLS video delivery.

> **Note on migrations:**
> Django migration files are **not tracked** in this repo (except for the `migrations/__init__.py` markers).
> - **Docker**: the container **automatically** runs `makemigrations` + `migrate`.
> - **Local (without Docker)**: you must run `python manage.py makemigrations` before `python manage.py migrate`.

---

## Getting Started

### Run with Docker (recommended)

1. **Copy env file and fill values (locally, do **not** commit '.env')**
    ```bash
    cp .env.template .env
    ```

    > **[!IMPORTANT]**
    >
    > Replace the placeholder values for
    > 
    > - DB_*,
    > - EMAIL_*,
    > - FRONTEND_*
    >
    > within ".env" with actual values specific to your environment if necessary
    >
    > **Keep real secrets OUT of .env.template and OUT of git**

2. **Build & start**
   ```bash
   docker compose up --build
   ```

   The entrypoint runs:
   - collectstatic
   - makemigrations
   - migrate
   - creates a superuser if missing (from .env)
   - starts an RQ worker and Gunicorn

3. **Open**
   - Backend API: http://127.0.0.1:8000
   - Admin: http://127.0.0.1:8000/admin
   - RQ dashboard: http://127.0.0.1:8000/django-rq/

### Backend Setup (without Docker)

Only if you really want to run locally against sqlite/your own services.

1. **Create and activate a virtuel environment**
    ```bash
    python3 -m venv env
    source env/bin/activate         # macOS/Linux
    # .\env\Scripts\Activate.ps1    # Windows PowerShell
    ```

2. **Copy env file and fill values (locally, do **not** commit '.env')**
    ```bash
    cp .env.template .env
    ```

    > **[!IMPORTANT]**
    >
    > Replace the placeholder values for
    > 
    > - DB_*,
    > - EMAIL_*,
    > - FRONTEND_*
    >
    > within ".env" with actual values specific to your environment if necessary
    >
    > **Keep real secrets OUT of .env.template and OUT of git**
   
3. **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Apply database migrations**
    ```bash
    python manage.py makemigrations
    ```
    ```bash
    python manage.py migrate
    ```

5. **Optional: Create a superuser**
    ```bash
    python manage.py createsuperuser
    ```

6. **Run the backend server**
    ```bash
    python manage.py runserver
    ```

    The API will be available at "http://127.0.0.1:8000"

---

### Frontend Setup ("https://github.com/Sessa89/Videoflix_Frontend")

1. **Open the frontend folder**  
    In your code editor (e.g., VS Code), open the frontend directory.

2. **Start a local static server**
    - Right-click on index.html (inside frontend) and select "Open with Live Server" if you have VS Code Live Server installed
    - The frontend will run at "http://127.0.0.1:5500/"

---

## API (short overview)

- POST /api/register/
- POST /api/activate/ (Body: { "uid": "<uidb64>", "token": "<token>" })
- GET /api/activate/<uid>/<token>/
- POST /api/login/
- POST /api/logout/
- POST /api/token/refresh/
- POST /api/password_reset/
- POST /api/password_confirm/<uid>/<token>/
- GET /api/video/
- GET /api/video/<movie_id>/<resolution>/index.m3u8
- GET /api/video/<movie_id>/<resolution>/<segment>/

---

## Features

- **Authentication**
  - Register with email + password
  - Email activation (GET link and POST fallback)
  - Login with email/password → JWT (HttpOnly cookies)
  - Cookie-based token refresh (`refresh_token` read from cookie)
  - Logout (blacklists refresh token and deletes cookies)
  - Password reset request (email with token)
  - Password reset confirm via URL params (`/password_confirm/<uid>/<token>/`)  

- **Video API**
  - List videos (title, description, thumbnail URL, category, created at) — auth required
  - Serve HLS master playlist `index.m3u8` — auth required
  - Serve HLS segment `.ts` — auth required, safe against path traversal

---