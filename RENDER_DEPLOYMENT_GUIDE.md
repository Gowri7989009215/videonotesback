# VideoNotes AI — Render.com Deployment Guide (FastAPI Backend)

This guide provides step-by-step instructions to prepare, commit, and deploy the `backend-fastapi` service to [Render.com](https://render.com).

---

## 1. Pre-Deployment Verification

### 1.1 `.gitignore` Check
Ensure [.gitignore](file:///d:/pro2/backend-fastapi/.gitignore) ignores transient virtual environments, secrets, and generated media files while keeping essential configuration files:

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# Virtual environments
venv/
.venv/

# Secrets & Environment variables
.env
.env.*
!.env.example

# Storage and runtime files
storage/*
!storage/.gitkeep
temp/
tmp/
*.log
logs/

# IDE files
.vscode/
.idea/
.DS_Store
```

### 1.2 Essential Files Included
- `main.py` — Application entry point
- `requirements.txt` — Python dependencies
- `.env.example` — Template environment variables
- `storage/.gitkeep` — Retains storage directory structure in Git

---

## 2. Push Code to GitHub / GitLab

Run the following commands in terminal to commit and push your code:

```bash
cd backend-fastapi

# Initialize Git repository (if not already done)
git init

# Stage all files
git add .

# Commit changes
git commit -m "Prepare FastAPI backend for Render deployment"

# Connect to your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/your-username/videonotes-backend-fastapi.git
git branch -M main
git push -u origin main
```

---

## 3. Database Configuration (Supabase or Render PostgreSQL)

### Option A: Use Supabase PostgreSQL (Recommended)
Copy your Supabase connection string:
```
postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

### Option B: Create PostgreSQL on Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **PostgreSQL**.
3. Name: `videonotes-db`
4. Copy the **Internal Database URL** or **External Database URL**.

---

## 4. Deploying to Render.com

### Step 1: Create a New Web Service
1. In Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub/GitLab repository (`videonotes-backend-fastapi`).

### Step 2: Configure Service Settings
- **Name**: `videonotes-backend-api`
- **Region**: Choose closest to your database (e.g., Oregon, Frankfurt, Singapore)
- **Branch**: `main`
- **Root Directory**: `backend-fastapi` *(Leave blank if repository contains only backend files)*
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

---

## 5. Configure Environment Variables on Render

In the Render Dashboard, navigate to **Environment** tab for your Web Service and add the following keys:

| Environment Variable | Value Example / Description |
| :--- | :--- |
| `NODE_ENV` | `production` |
| `DATABASE_URL` | `postgresql://user:password@host:5432/database_name` |
| `JWT_SECRET` | `your-secure-random-jwt-secret` |
| `REQUIRE_EMAIL_VERIFICATION` | `false` |
| `ALLOWED_ORIGINS` | `https://your-frontend-domain.onrender.com,http://localhost:5173` |
| `OPENAI_API_KEY` | `sk-proj-...` *(Required if using OpenAI)* |
| `RESEND_API_KEY` | `re_...` *(Required if using Resend email)* |
| `EMAIL_FROM` | `onboarding@resend.dev` |
| `STORAGE_ROOT` | `storage` |

Click **Save Changes**. Render will automatically trigger a deployment.

---

## 6. System Dependency Note (FFmpeg for Video Extraction)

If your app extracts video frames using system-level `ffmpeg`:

### Option A: Use Render Docker Deployment (Zero-headache setup)
Create a `Dockerfile` in `backend-fastapi`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies (FFmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-4000}"]
```

On Render:
- Set **Runtime**: `Docker`
- Render will automatically build the container with FFmpeg included!

---

## 7. Verification & Swagger UI Access

Once deployed, visit your Render Web Service URL:
- **Swagger Docs**: `https://videonotes-backend-api.onrender.com/docs`
- **Health Check**: `https://videonotes-backend-api.onrender.com/api/health`
- **ReDoc**: `https://videonotes-backend-api.onrender.com/redoc`

You should receive `{"status": "ok", "database": true}` on the health check endpoint!
