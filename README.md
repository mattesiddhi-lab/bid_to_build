# CampusFix - College / Campus Maintenance Complaint Management

A lightweight, modern web application for college and campus maintenance teams to report, triage, assign, and track facility complaints.

---

## Tech Stack
- **Backend:** Python (Flask 3.x with Flask Sessions & Werkzeug Password Security)
- **Database:** SQLite (`maintenance.db`)
- **Frontend:** Plain HTML5, Modern Vanilla CSS, Plain JavaScript (no frontend build tools or frameworks required)

---

## Seeded Login Credentials

The application includes two pre-seeded accounts:

| Role | Username | Password | Access Level |
|---|---|---|---|
| **Maintenance Admin** | `admin` | `admin123` | Full triage, worker assignment, status progression, workload metrics & problem areas |
| **Student Resident** | `student` | `student123` | Report complaints, upload photos, view live status and track complaints |

> You can also register a new account on `/register` (new accounts are assigned the `User` role).

---

## Features
1. **Authentication & Role-Based Access Control (RBAC):**
   - Secure Flask session management with werkzeug password hashing.
   - Server-enforced permissions for all administrative endpoints.
   - User registration at `/register` and login at `/login`.
2. **Complaint Filing Form:**
   - **Categories:** Electrical, Plumbing, Furniture, Cleaning, Other
   - **Priority Levels:** Low, Medium, High, Critical (with auto-priority detection)
   - **Location:** Specific room, wing, or campus area
   - **Description:** Problem details
   - **Photo Upload:** Drag-and-drop or file selector with instant preview
   - **Reported By:** Tracks author name on each ticket
3. **Smart Priority & Recurrence Flags:**
   - **Auto-flagged:** Automatically detects emergency keywords (fire, sparking, burst pipe, etc.) and raises ticket priority.
   - **Recurring Issues:** Highlights recurring complaints at the same location and category with a history viewer for admins.
4. **Maintenance Dashboard:**
   - Real-time count cards by **Status** (`Reported`, `Assigned`, `In Progress`, `Resolved`).
   - Real-time count cards by **Priority** (`Critical`, `High`, `Medium`, `Low`).
   - **Worker Workload:** Live capacity tracking across maintenance specialists.
   - **Problem Areas:** Ranked top 6 complaint hotspot locations with filter chips.
5. **Worker Assignment & Status Workflow (Admin Only):**
   - Admins can assign tickets to workers (sorted least-loaded first).
   - Status workflow progression: `Reported` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`.

---

## Project Structure

```text
bid_to_build/
├── app.py                  # Flask backend, SQLite schema, auth, sessions & REST endpoints
├── requirements.txt        # Flask dependency
├── maintenance.db          # SQLite database (auto-generated & seeded on first run)
├── run.bat                 # One-click launch script for Windows
├── run.ps1                 # PowerShell launch script
├── templates/
│   ├── index.html          # Main application responsive HTML template
│   ├── login.html          # Authentication login template with demo shortcuts
│   └── register.html       # User registration template
├── static/
│   ├── css/
│   │   └── style.css       # Clean, modern CSS styles & colored badges
│   ├── js/
│   │   └── app.js          # Client-side UI interactions, AJAX calls, filters
│   └── uploads/            # Uploaded photos and sample ticket SVGs
└── README.md               # Setup and usage guide
```

---

## Exact Steps to Run the App

### Option A: Quick Run on Windows (One-Click)

Double-click `run.bat` or run in PowerShell:

```powershell
.\run.ps1
```

---

### Option B: Standard Python Setup (Windows / macOS / Linux)

#### 1. Open Terminal or Command Prompt
Navigate to the project folder:
```bash
cd bid_to_build
```

#### 2. Create and Activate a Virtual Environment

**On Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run the Application
```bash
python app.py
```

#### 5. Open in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## How to Use the App

1. **Log In:**
   - Navigate to `http://127.0.0.1:5000/login`.
   - Click **"Login as Student"** or **"Login as Admin"** for instant 1-click demo access, or enter your credentials.
2. **Submit a Complaint (User):**
   - Choose a Category, Priority, Location, Description, and optional Photo.
   - Click **Submit Maintenance Ticket**. The ticket records your name as the reporter.
3. **Manage Tickets (Admin):**
   - Use the **"Select worker to assign..."** dropdown on any complaint card to dispatch a technician.
   - Click **"Start Work (In Progress) ➔"** when repairs begin.
   - Click **"Mark Resolved ✓"** when completed.
4. **Interactive Dashboard & Problem Areas:**
   - Click on any status card or priority card to filter tickets.
   - In Admin mode, view **Worker Workloads** and click any **Problem Area** row to filter by location.
   - Click **"Sign Out"** in the top navigation bar to log out.