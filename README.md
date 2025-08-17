# Videoflix Backend

![Videoflix Logo](logo_icon.svg)

This repository contains the Django REST Framework–based backend for **Videoflix**, a Netflix-style demo app with email activation, JWT cookie auth, password reset, and HLS video delivery.

---

## Getting Started

### Backend Setup

1. **Create a virtuel environment**
    ```bash
    python3 -m venv env
    ```
    ```bash
    source env/bin/activate   # macOS/Linux
    ```
    ### or
    ```bash
    .\env\Scripts\Activate.ps1  # Windows PowerShell
    ```

2. **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Apply database migrations**
    ```bash
    python manage.py makemigrations
    ```
    ```bash
    python manage.py migrate
    ```

4. **Optional: Create a superuser**
    ```bash
    python manage.py createsuperuser
    ```

5. **Run the backend server**
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

## Configuration

Key settings (see `videoflix_core/settings.py`):

- **Email**
  - `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` (emails appear in the runserver console)
  - `DEFAULT_FROM_EMAIL = 'noreply@videoflix.local'`
  - `FRONTEND_BASE_URL = 'http://localhost:5500'`  
    (used to build activation/reset links; point this to the folder that contains `activate.html` / `reset.html`)

- **JWT (SimpleJWT)**
  - Access: 30 min, Refresh: 7 days
  - HttpOnly cookies: `access_token`, `refresh_token`
  - Refresh token blacklist enabled on logout

- **CORS**
  - `CORS_ALLOWED_ORIGINS` includes `http://127.0.0.1:5500` and `http://localhost:5500`
  - `CORS_ALLOW_CREDENTIALS = True`

- **HLS (video files)**
  - `HLS_ROOT = BASE_DIR / 'hls'`
  - Allowed resolutions: `{'240p','360p','480p','720p','1080p'}`
  - Allowed segment extensions: `{'.ts'}`

---