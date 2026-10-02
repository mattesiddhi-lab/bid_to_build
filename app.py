import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "maintenance.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

CATEGORIES = ["Electrical", "Plumbing", "Furniture", "Cleaning", "Other"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUS_ORDER = ["Reported", "Assigned", "In Progress", "Resolved"]
STATUS_NEXT = {
    "Reported": "Assigned",
    "Assigned": "In Progress",
    "In Progress": "Resolved",
}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db(seed_if_empty=True):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                phone TEXT NOT NULL
            );
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_no TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Reported',
                assigned_worker_id INTEGER,
                photo_filename TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (assigned_worker_id) REFERENCES workers(id)
            );
        """
        )

        conn.commit()

        if seed_if_empty:
            seed_data(conn)


def seed_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM workers")
    worker_count = cursor.fetchone()[0]

    if worker_count == 0:
        sample_workers = [
            ("Rajesh Sharma", "Electrical Specialist", "+91 98765-10001"),
            ("Marcus Chen", "Campus Plumber", "+91 98765-10002"),
            ("David Miller", "Carpentry & Furniture Tech", "+91 98765-10003"),
            ("Sarah Jenkins", "Sanitation & Facilities Lead", "+91 98765-10004"),
        ]
        cursor.executemany(
            "INSERT INTO workers (name, role, phone) VALUES (?, ?, ?)",
            sample_workers,
        )
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    complaint_count = cursor.fetchone()[0]

    if complaint_count == 0:
        # 20 realistic sample complaints across campus
        sample_complaints = [
            (
                "TKT-1001",
                "Electrical",
                "Science Block - Room 304",
                "Sparking switchboard near chemical storage rack. Smells like burnt plastic.",
                "Critical",
                "Reported",
                None,
                "sample_switchboard.svg",
                "2026-10-02 08:30:00",
                "2026-10-02 08:30:00",
            ),
            (
                "TKT-1002",
                "Plumbing",
                "Hostel B - Ground Floor Restroom",
                "Main water inlet pipe ruptured. Heavy leakage flooding the corridor.",
                "High",
                "In Progress",
                2,  # Marcus Chen
                "sample_water_leak.svg",
                "2026-10-01 14:15:00",
                "2026-10-02 09:00:00",
            ),
            (
                "TKT-1003",
                "Furniture",
                "Main Auditorium - Row H Seats 12-14",
                "Cushioned seats completely unhinged and armrest bracket loose with sharp exposed edges.",
                "Medium",
                "Assigned",
                3,  # David Miller
                "sample_broken_seat.svg",
                "2026-10-01 11:20:00",
                "2026-10-01 16:00:00",
            ),
            (
                "TKT-1004",
                "Cleaning",
                "Central Cafeteria - Waste Station B",
                "Organic waste bins overflowing, attracting flies and creating foul odor.",
                "High",
                "In Progress",
                4,  # Sarah Jenkins
                None,
                "2026-10-02 07:45:00",
                "2026-10-02 08:15:00",
            ),
            (
                "TKT-1005",
                "Electrical",
                "Library - 2nd Floor Silent Zone",
                "Flickering ballast on 3 ceiling light tubes causing buzzing noise and headache for students.",
                "Medium",
                "Resolved",
                1,  # Rajesh Sharma
                None,
                "2026-09-30 10:10:00",
                "2026-10-01 12:00:00",
            ),
            (
                "TKT-1006",
                "Plumbing",
                "Engineering Hall - 3rd Floor Water Cooler",
                "Drain clogged, water overflowing on floor right next to server room doorway.",
                "Critical",
                "Assigned",
                2,  # Marcus Chen
                None,
                "2026-10-02 09:10:00",
                "2026-10-02 09:30:00",
            ),
            (
                "TKT-1007",
                "Furniture",
                "Classroom 102 - Lecture Pod",
                "Instructor podium castor wheel snapped; unable to maneuver board.",
                "Low",
                "Reported",
                None,
                None,
                "2026-10-01 16:40:00",
                "2026-10-01 16:40:00",
            ),
            (
                "TKT-1008",
                "Cleaning",
                "Gymnasium - Changing Room",
                "Spilled energy drinks and damp floors requiring machine scrubbing.",
                "Medium",
                "Resolved",
                4,  # Sarah Jenkins
                None,
                "2026-09-29 18:00:00",
                "2026-09-30 08:30:00",
            ),
            (
                "TKT-1009",
                "Other",
                "North Gate - Security Booth",
                "Boom barrier rubber dampener detached, metal gate slamming loudly.",
                "Low",
                "Assigned",
                3,  # David Miller
                None,
                "2026-10-01 09:00:00",
                "2026-10-01 11:30:00",
            ),
            (
                "TKT-1010",
                "Electrical",
                "Computer Science Lab 3",
                "Central 10kVA UPS tripping whenever entire batch powers on PCs.",
                "Critical",
                "In Progress",
                1,  # Rajesh Sharma
                None,
                "2026-10-02 08:00:00",
                "2026-10-02 08:45:00",
            ),
            (
                "TKT-1011",
                "Plumbing",
                "Faculty Lounge - Restroom Sink",
                "Slow continuous drip from chrome faucet aerator.",
                "Low",
                "Resolved",
                2,  # Marcus Chen
                None,
                "2026-09-28 11:00:00",
                "2026-09-28 17:00:00",
            ),
            (
                "TKT-1012",
                "Cleaning",
                "Student Activity Center - Courtyard",
                "Packing materials and thermocol packaging left behind after club fair.",
                "Medium",
                "Reported",
                None,
                None,
                "2026-10-02 07:15:00",
                "2026-10-02 07:15:00",
            ),
            (
                "TKT-1013",
                "Furniture",
                "Seminar Hall B - Stage Lectern",
                "Wooden panel loose and goose-neck mic mount screws stripped.",
                "High",
                "In Progress",
                3,  # David Miller
                None,
                "2026-10-01 15:30:00",
                "2026-10-02 09:15:00",
            ),
            (
                "TKT-1014",
                "Other",
                "Biotech Greenhouse - Vent #2",
                "Motorized shutter jammed halfway; rain entering indoor plant bed.",
                "High",
                "Reported",
                None,
                None,
                "2026-10-02 06:50:00",
                "2026-10-02 06:50:00",
            ),
            (
                "TKT-1015",
                "Electrical",
                "Hostel A - Stairwell 4th Floor Landing",
                "Overhead emergency light fixture broken, stair landing is pitch black at night.",
                "High",
                "Assigned",
                1,  # Rajesh Sharma
                "sample_hallway_light.svg",
                "2026-10-01 21:00:00",
                "2026-10-02 07:30:00",
            ),
            (
                "TKT-1016",
                "Plumbing",
                "Chemistry Dept - Emergency Eyewash Station 1",
                "Emergency pull valve stuck shut; low water pressure safety violation.",
                "Critical",
                "Reported",
                None,
                None,
                "2026-10-02 09:40:00",
                "2026-10-02 09:40:00",
            ),
            (
                "TKT-1017",
                "Cleaning",
                "Arts Building - Clay & Sculpture Studio",
                "Thick dried gypsum and clay dust on floor, needs specialized wet vacuuming.",
                "Low",
                "Assigned",
                4,  # Sarah Jenkins
                None,
                "2026-10-01 17:00:00",
                "2026-10-01 18:00:00",
            ),
            (
                "TKT-1018",
                "Furniture",
                "Admin Block - Office 205",
                "Filing cabinet drawer stuck on sliding rails with key stuck inside.",
                "Low",
                "Resolved",
                3,  # David Miller
                None,
                "2026-09-29 14:00:00",
                "2026-09-30 11:00:00",
            ),
            (
                "TKT-1019",
                "Other",
                "West Parking Lot - Pathway Lamp #6",
                "Polycarbonate lens cracked after gusty wind, exposed wiring.",
                "Medium",
                "Reported",
                None,
                None,
                "2026-10-02 08:20:00",
                "2026-10-02 08:20:00",
            ),
            (
                "TKT-1020",
                "Electrical",
                "Mechanical Workshop - Central Lathe Unit",
                "Emergency stop circuit cut out during heavy milling run.",
                "Critical",
                "Resolved",
                1,  # Rajesh Sharma
                None,
                "2026-09-30 13:00:00",
                "2026-10-01 10:00:00",
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO complaints (
                ticket_no, category, location, description, priority, status,
                assigned_worker_id, photo_filename, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            sample_complaints,
        )
        conn.commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/workers", methods=["GET"])
def get_workers():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, phone FROM workers ORDER BY id ASC")
        workers = [dict(row) for row in cursor.fetchall()]
    return jsonify(workers)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()

        # Status counts
        status_counts = {s: 0 for s in STATUS_ORDER}
        cursor.execute(
            "SELECT status, COUNT(*) as count FROM complaints GROUP BY status"
        )
        for row in cursor.fetchall():
            if row["status"] in status_counts:
                status_counts[row["status"]] = row["count"]

        # Priority counts
        priority_counts = {p: 0 for p in PRIORITIES}
        cursor.execute(
            "SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority"
        )
        for row in cursor.fetchall():
            if row["priority"] in priority_counts:
                priority_counts[row["priority"]] = row["count"]

        # Total count
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total = cursor.fetchone()[0]

    return jsonify(
        {
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "total": total,
        }
    )


@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    category_filter = request.args.get("category")
    search_query = request.args.get("search")

    query = """
        SELECT 
            c.id, c.ticket_no, c.category, c.location, c.description,
            c.priority, c.status, c.assigned_worker_id, c.photo_filename,
            c.created_at, c.updated_at,
            w.name AS assigned_worker_name,
            w.role AS assigned_worker_role,
            w.phone AS assigned_worker_phone
        FROM complaints c
        LEFT JOIN workers w ON c.assigned_worker_id = w.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "All":
        query += " AND c.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        query += " AND c.priority = ?"
        params.append(priority_filter)

    if category_filter and category_filter != "All":
        query += " AND c.category = ?"
        params.append(category_filter)

    if search_query:
        query += " AND (c.ticket_no LIKE ? OR c.location LIKE ? OR c.description LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    query += " ORDER BY c.id DESC"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        complaints = [dict(row) for row in cursor.fetchall()]

    return jsonify(complaints)


@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Low").strip()

    if not category or category not in CATEGORIES:
        return jsonify({"error": f"Invalid category. Must be one of {CATEGORIES}"}), 400

    if not location:
        return jsonify({"error": "Location is required"}), 400

    if not description:
        return jsonify({"error": "Description is required"}), 400

    if priority not in PRIORITIES:
        return jsonify({"error": f"Invalid priority. Must be one of {PRIORITIES}"}), 400

    photo_filename = None
    if "photo" in request.files:
        file = request.files["photo"]
        if file and file.filename != "" and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            safe_name = f"upload_{uuid.uuid4().hex[:10]}.{ext}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))
            photo_filename = safe_name

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()

        # Generate unique ticket number
        cursor.execute("SELECT MAX(id) FROM complaints")
        last_id = cursor.fetchone()[0] or 1000
        ticket_no = f"TKT-{last_id + 1}"

        cursor.execute(
            """
            INSERT INTO complaints (
                ticket_no, category, location, description, priority,
                status, assigned_worker_id, photo_filename, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'Reported', NULL, ?, ?, ?)
        """,
            (ticket_no, category, location, description, priority, photo_filename, now, now),
        )
        new_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.created_at, c.updated_at,
                w.name AS assigned_worker_name,
                w.role AS assigned_worker_role
            FROM complaints c
            LEFT JOIN workers w ON c.assigned_worker_id = w.id
            WHERE c.id = ?
        """,
            (new_id,),
        )
        new_complaint = dict(cursor.fetchone())

    return jsonify({"success": True, "complaint": new_complaint}), 201


@app.route("/api/complaints/<int:complaint_id>/assign", methods=["POST"])
def assign_worker(complaint_id):
    data = request.get_json(silent=True) or {}
    worker_id = data.get("worker_id")

    if not worker_id:
        return jsonify({"error": "Worker ID is required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM workers WHERE id = ?", (worker_id,))
        worker = cursor.fetchone()
        if not worker:
            return jsonify({"error": "Worker not found"}), 404

        cursor.execute("SELECT id, status FROM complaints WHERE id = ?", (complaint_id,))
        complaint = cursor.fetchone()
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # If currently 'Reported', assigning a worker advances it to 'Assigned'
        current_status = complaint["status"]
        new_status = "Assigned" if current_status == "Reported" else current_status

        cursor.execute(
            """
            UPDATE complaints 
            SET assigned_worker_id = ?, status = ?, updated_at = ?
            WHERE id = ?
        """,
            (worker_id, new_status, now, complaint_id),
        )
        conn.commit()

        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.created_at, c.updated_at,
                w.name AS assigned_worker_name,
                w.role AS assigned_worker_role,
                w.phone AS assigned_worker_phone
            FROM complaints c
            LEFT JOIN workers w ON c.assigned_worker_id = w.id
            WHERE c.id = ?
        """,
            (complaint_id,),
        )
        updated = dict(cursor.fetchone())

    return jsonify({"success": True, "complaint": updated})


@app.route("/api/complaints/<int:complaint_id>/advance", methods=["POST"])
def advance_status(complaint_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, status, assigned_worker_id FROM complaints WHERE id = ?",
            (complaint_id,),
        )
        complaint = cursor.fetchone()
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        current_status = complaint["status"]
        if current_status not in STATUS_NEXT:
            return jsonify({"error": f"Cannot advance status from '{current_status}'"}), 400

        next_status = STATUS_NEXT[current_status]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "UPDATE complaints SET status = ?, updated_at = ? WHERE id = ?",
            (next_status, now, complaint_id),
        )
        conn.commit()

        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.created_at, c.updated_at,
                w.name AS assigned_worker_name,
                w.role AS assigned_worker_role,
                w.phone AS assigned_worker_phone
            FROM complaints c
            LEFT JOIN workers w ON c.assigned_worker_id = w.id
            WHERE c.id = ?
        """,
            (complaint_id,),
        )
        updated = dict(cursor.fetchone())

    return jsonify({"success": True, "complaint": updated})


@app.route("/api/reset-db", methods=["POST"])
def reset_database():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS complaints")
        cursor.execute("DROP TABLE IF EXISTS workers")
        conn.commit()
    init_db(seed_if_empty=True)
    return jsonify({"success": True, "message": "Database reset and seeded with 4 workers and 20 sample complaints."})


# Initialize DB on import or startup
init_db()

if __name__ == "__main__":
    print("Starting Campus Maintenance Web App...")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(host="127.0.0.1", port=5000, debug=True)
