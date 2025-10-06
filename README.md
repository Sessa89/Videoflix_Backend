# Videoflix Backend

![Videoflix Logo](logo_icon.svg)

This repository contains the Django REST Framework–based backend for **Videoflix**, a Netflix-style demo app with email activation, JWT cookie auth, password reset, and HLS video delivery.

---

## Getting Started

### Backend Setup

1. **Set your virtual environment**
    ```bash
    Define the environment variables using the ".env.template"-file

    # [!IMPORTANT]
    # Replace the placeholder values with actual values specific to your environment, if necessary
    ```

2. **Create ".env"-file with the settings of your ".env.template"-file**
    ```bash
    cp .env.template .env
    ```

3. **Create a virtuel environment**
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

    ```bash
    python3 -m manage.py makemigrations
    ```

    ```bash
    python3 -m manage.py migrate
    ``` 

4. **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5. **Apply database migrations**
    ```bash
    python manage.py makemigrations
    ```
    ```bash
    python manage.py migrate
    ```

6. **Optional: Create a superuser**
    ```bash
    python manage.py createsuperuser
    ```

7. **Run the backend server**
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