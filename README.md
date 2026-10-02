# CampusFix - College / Campus Maintenance Complaint Management

A lightweight, modern web application for college and campus maintenance teams to report, triage, assign, and track facility complaints.

---

## Tech Stack
- **Backend:** Python (Flask 3.x)
- **Database:** SQLite (`maintenance.db`)
- **Frontend:** Plain HTML5, Modern Vanilla CSS, Plain JavaScript (no frontend build tools or frameworks required)

---

## Features (MVP)
1. **Complaint Filing Form:**
   - **Categories:** Electrical, Plumbing, Furniture, Cleaning, Other
   - **Priority Levels:** Low, Medium, High, Critical
   - **Location:** Specific room, wing, or campus area
   - **Description:** Problem details
   - **Photo Upload:** Drag-and-drop or file selector with instant preview
2. **Priority Badges:**
   - **Critical** = Bright Red badge with pulse indicator
   - **High** = Orange badge
   - **Medium** = Blue badge
   - **Low** = Green badge
3. **Role Switcher (User / Admin):**
   - Toggle between **Resident / User** mode and **Maintenance Admin** mode directly from the top header (no login required).
4. **Maintenance Dashboard:**
   - Real-time count cards by **Status** (`Reported`, `Assigned`, `In Progress`, `Resolved`).
   - Real-time count cards by **Priority** (`Critical`, `High`, `Medium`, `Low`).
   - Clickable metric cards to instantly filter tickets.
5. **Worker Assignment & Status Workflow:**
   - Admin can assign any ticket to a maintenance worker.
   - Status workflow progression: `Reported` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`.
6. **Automatic Seeding:**
   - Seeds **4 maintenance specialists** and **20 sample campus complaints** on first startup.

---

## Project Structure

```text
bid_to_build/
├── app.py                  # Flask backend, SQLite schema, REST endpoints & seeder
├── requirements.txt        # Flask dependency
├── maintenance.db          # SQLite database (auto-generated & seeded on first run)
├── run.bat                 # One-click launch script for Windows
├── run.ps1                 # PowerShell launch script
├── templates/
│   └── index.html          # Single-page responsive HTML template
├── static/
│   ├── css/
│   │   └── style.css       # Clean, modern CSS styles & colored badges
│   ├── js/
│   │   └── app.js          # Role toggle, AJAX calls, filters, workflow transitions
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

1. **Switch Roles:**
   - Click **"👤 Resident / User"** at the top right to file complaints as a student or staff member.
   - Click **"🛡️ Maintenance Admin"** to access the maintenance dashboard, assign tickets to workers, and move tickets forward through the workflow.
2. **Submit a Complaint (User Mode):**
   - Choose a Category (e.g. *Electrical*), Priority (e.g. *Critical*), enter Location (e.g. *Science Block 304*), Description, and optional Photo.
   - Click **Submit Maintenance Ticket**.
3. **Assign and Move Tickets (Admin Mode):**
   - Use the **"Select worker to assign..."** dropdown on any complaint card.
   - Click **"Assign"** to dispatch the worker.
   - Click **"Start Work (In Progress) ➔"** to mark work actively underway.
   - Click **"Mark Resolved ✓"** when repairs are complete.
4. **Interactive Dashboard:**
   - Click on any status card (e.g., *Reported (6)*) or priority card (e.g., *Critical (5)*) to filter the complaints view.
   - Click **"Reset Filters"** to view all tickets.