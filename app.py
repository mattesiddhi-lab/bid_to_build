import os
import re
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

CRITICAL_KEYWORDS = [
    "sparking",
    "spark",
    "fire",
    "smoke",
    "exposed wiring",
    "exposed wire",
    "short circuit",
    "electric shock",
    "gas leak",
    "flooding",
    "flood",
    "burst pipe",
    "collapse",
    "acid",
]

HIGH_KEYWORDS = [
    "leaking",
    "leak",
    "broken glass",
    "no water",
    "no power",
    "blackout",
    "stuck",
]

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


def normalize_location(loc):
    """Normalize location string: strip, lowercase, collapse extra spaces."""
    if not loc:
        return ""
    return " ".join(loc.strip().lower().split())


def detect_priority(description, user_priority):
    """
    Scans description (case-insensitive) for keywords.
    - If Critical keyword found: raise to Critical (even if user selected lower).
    - If only High keyword found and user selected Low or Medium: raise to High.
    - Never lower a priority the user chose.
    Returns: (final_priority, auto_flagged (0 or 1), trigger_keyword or None)
    """
    desc = description or ""
    priority_levels = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    user_level = priority_levels.get(user_priority, 1)

    # Check Critical keywords first
    for kw in CRITICAL_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, desc, re.IGNORECASE):
            if user_level < priority_levels["Critical"]:
                return "Critical", 1, kw
            return "Critical", 0, None

    # Check High keywords next
    for kw in HIGH_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, desc, re.IGNORECASE):
            if user_level < priority_levels["High"]:
                return "High", 1, kw
            return user_priority, 0, None

    return user_priority, 0, None


def get_recurrence_info(cursor):
    """
    Calculates recurrence metadata across all complaints in database:
    - is_recurring (bool): True if there is at least one other earlier complaint with same category and normalized location
    - recurrence_count (int): number of earlier matching complaints
    - total_occurrences (int): total count of complaints with same category and normalized location
    """
    cursor.execute("SELECT id, category, location FROM complaints ORDER BY id ASC")
    rows = cursor.fetchall()
    groups = {}
    for row in rows:
        key = (row["category"].strip().lower(), normalize_location(row["location"]))
        if key not in groups:
            groups[key] = []
        groups[key].append(row["id"])

    info_map = {}
    for key, ids in groups.items():
        total = len(ids)
        for idx, cid in enumerate(ids):
            info_map[cid] = {
                "is_recurring": idx > 0,
                "recurrence_count": idx,
                "total_occurrences": total,
            }
    return info_map


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
                auto_flagged INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (assigned_worker_id) REFERENCES workers(id)
            );
        """
        )

        # Handle existing database safely: add column if missing without deleting data
        cursor.execute("PRAGMA table_info(complaints)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "auto_flagged" not in columns:
            cursor.execute(
                "ALTER TABLE complaints ADD COLUMN auto_flagged INTEGER DEFAULT 0"
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
        # 20 realistic sample complaints across campus, including repeated locations for demo
        sample_complaints = [
            # Location 1 (Plumbing at Hostel B - Ground Floor Restroom): 3 complaints
            (
                "TKT-1001",
                "Plumbing",
                "Hostel B - Ground Floor Restroom",
                "Drain clogged in shower stall with dirty water pooling.",
                "Medium",
                "Resolved",
                2,  # Marcus Chen
                None,
                0,
                "2026-09-24 10:00:00",
                "2026-09-25 12:00:00",
            ),
            (
                "TKT-1002",
                "Plumbing",
                "Hostel B - Ground Floor Restroom",
                "Flush tank valve leaking and water continuously running.",
                "High",
                "Resolved",
                2,  # Marcus Chen
                None,
                0,
                "2026-09-28 15:30:00",
                "2026-09-29 11:00:00",
            ),
            (
                "TKT-1003",
                "Plumbing",
                "Hostel B - Ground Floor Restroom",
                "Main water inlet pipe ruptured. Heavy leakage flooding the corridor.",
                "High",
                "In Progress",
                2,  # Marcus Chen
                "sample_water_leak.svg",
                0,
                "2026-10-01 14:15:00",
                "2026-10-02 09:00:00",
            ),
            # Location 2 (Electrical at Science Block - Room 304): 2 complaints
            (
                "TKT-1004",
                "Electrical",
                "Science Block - Room 304",
                "Fume hood exhaust circuit breaker tripped twice under heavy lab load.",
                "High",
                "Resolved",
                1,  # Rajesh Sharma
                None,
                0,
                "2026-09-27 14:00:00",
                "2026-09-28 10:00:00",
            ),
            (
                "TKT-1005",
                "Electrical",
                "Science Block - Room 304",
                "Sparking switchboard near chemical storage rack. Smells like burnt plastic.",
                "Critical",
                "Reported",
                None,
                "sample_switchboard.svg",
                0,
                "2026-10-02 08:30:00",
                "2026-10-02 08:30:00",
            ),
            # Location 3 (Cleaning at Central Cafeteria - Waste Station B): 2 complaints
            (
                "TKT-1006",
                "Cleaning",
                "Central Cafeteria - Waste Station B",
                "Grease trap overflow and discarded food trays stacking up on floor.",
                "Medium",
                "Resolved",
                4,  # Sarah Jenkins
                None,
                0,
                "2026-09-29 09:30:00",
                "2026-09-30 08:00:00",
            ),
            (
                "TKT-1007",
                "Cleaning",
                "Central Cafeteria - Waste Station B",
                "Organic waste bins overflowing, attracting flies and creating foul odor.",
                "High",
                "In Progress",
                4,  # Sarah Jenkins
                None,
                0,
                "2026-10-02 07:45:00",
                "2026-10-02 08:15:00",
            ),
            # Additional campus maintenance complaints
            (
                "TKT-1008",
                "Furniture",
                "Main Auditorium - Row H Seats 12-14",
                "Cushioned seats completely unhinged and armrest bracket loose with sharp exposed edges.",
                "Medium",
                "Assigned",
                3,  # David Miller
                "sample_broken_seat.svg",
                0,
                "2026-10-01 11:20:00",
                "2026-10-01 16:00:00",
            ),
            (
                "TKT-1009",
                "Electrical",
                "Library - 2nd Floor Silent Zone",
                "Flickering ballast on 3 ceiling light tubes causing buzzing noise and headache for students.",
                "Medium",
                "Resolved",
                1,  # Rajesh Sharma
                None,
                0,
                "2026-09-30 10:10:00",
                "2026-10-01 12:00:00",
            ),
            (
                "TKT-1010",
                "Plumbing",
                "Engineering Hall - 3rd Floor Water Cooler",
                "Drain clogged, water overflowing on floor right next to server room doorway.",
                "Critical",
                "Assigned",
                2,  # Marcus Chen
                None,
                0,
                "2026-10-02 09:10:00",
                "2026-10-02 09:30:00",
            ),
            (
                "TKT-1011",
                "Furniture",
                "Classroom 102 - Lecture Pod",
                "Instructor podium castor wheel snapped; unable to maneuver board.",
                "Low",
                "Reported",
                None,
                None,
                0,
                "2026-10-01 16:40:00",
                "2026-10-01 16:40:00",
            ),
            (
                "TKT-1012",
                "Cleaning",
                "Gymnasium - Changing Room",
                "Spilled energy drinks and damp floors requiring machine scrubbing.",
                "Medium",
                "Resolved",
                4,  # Sarah Jenkins
                None,
                0,
                "2026-09-29 18:00:00",
                "2026-09-30 08:30:00",
            ),
            (
                "TKT-1013",
                "Other",
                "North Gate - Security Booth",
                "Boom barrier rubber dampener detached, metal gate slamming loudly.",
                "Low",
                "Assigned",
                3,  # David Miller
                None,
                0,
                "2026-10-01 09:00:00",
                "2026-10-01 11:30:00",
            ),
            (
                "TKT-1014",
                "Electrical",
                "Computer Science Lab 3",
                "Central 10kVA UPS tripping whenever entire batch powers on PCs.",
                "Critical",
                "In Progress",
                1,  # Rajesh Sharma
                None,
                0,
                "2026-10-02 08:00:00",
                "2026-10-02 08:45:00",
            ),
            (
                "TKT-1015",
                "Plumbing",
                "Faculty Lounge - Restroom Sink",
                "Slow continuous drip from chrome faucet aerator.",
                "Low",
                "Resolved",
                2,  # Marcus Chen
                None,
                0,
                "2026-09-28 11:00:00",
                "2026-09-28 17:00:00",
            ),
            (
                "TKT-1016",
                "Cleaning",
                "Student Activity Center - Courtyard",
                "Packing materials and thermocol packaging left behind after club fair.",
                "Medium",
                "Reported",
                None,
                None,
                0,
                "2026-10-02 07:15:00",
                "2026-10-02 07:15:00",
            ),
            (
                "TKT-1017",
                "Furniture",
                "Seminar Hall B - Stage Lectern",
                "Wooden panel loose and goose-neck mic mount screws stripped.",
                "High",
                "In Progress",
                3,  # David Miller
                None,
                0,
                "2026-10-01 15:30:00",
                "2026-10-02 09:15:00",
            ),
            (
                "TKT-1018",
                "Electrical",
                "Hostel A - Stairwell 4th Floor Landing",
                "Overhead emergency light fixture broken, stair landing is pitch black at night.",
                "High",
                "Assigned",
                1,  # Rajesh Sharma
                "sample_hallway_light.svg",
                0,
                "2026-10-01 21:00:00",
                "2026-10-02 07:30:00",
            ),
            (
                "TKT-1019",
                "Plumbing",
                "Chemistry Dept - Emergency Eyewash Station 1",
                "Emergency pull valve stuck shut; low water pressure safety violation.",
                "Critical",
                "Reported",
                None,
                None,
                0,
                "2026-10-02 09:40:00",
                "2026-10-02 09:40:00",
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
                0,
                "2026-09-30 13:00:00",
                "2026-10-01 10:00:00",
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO complaints (
                ticket_no, category, location, description, priority, status,
                assigned_worker_id, photo_filename, auto_flagged, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        # Recurring count calculated at query time
        rec_map = get_recurrence_info(cursor)
        recurring_count = sum(1 for v in rec_map.values() if v["is_recurring"])

    return jsonify(
        {
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "total": total,
            "recurring_count": recurring_count,
        }
    )


@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    category_filter = request.args.get("category")
    recurring_filter = request.args.get("recurring")
    search_query = request.args.get("search")

    query = """
        SELECT 
            c.id, c.ticket_no, c.category, c.location, c.description,
            c.priority, c.status, c.assigned_worker_id, c.photo_filename,
            c.auto_flagged,
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

    # Critical complaints appear at the top (sort by priority, then newest)
    query += """
        ORDER BY 
            CASE c.priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                WHEN 'Low' THEN 4 
                ELSE 5 
            END ASC, 
            c.id DESC
    """

    with get_db() as conn:
        cursor = conn.cursor()
        rec_map = get_recurrence_info(cursor)
        cursor.execute(query, params)
        rows = cursor.fetchall()

        complaints = []
        for row in rows:
            item = dict(row)
            r_info = rec_map.get(
                item["id"],
                {"is_recurring": False, "recurrence_count": 0, "total_occurrences": 1},
            )
            item["is_recurring"] = r_info["is_recurring"]
            item["recurrence_count"] = r_info["recurrence_count"]
            item["total_occurrences"] = r_info["total_occurrences"]

            # Filter recurring if requested
            if recurring_filter in ["true", "1", "True"]:
                if not item["is_recurring"]:
                    continue

            complaints.append(item)

    return jsonify(complaints)


@app.route("/api/complaints/<int:complaint_id>/history", methods=["GET"])
def get_complaint_history(complaint_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, ticket_no, category, location FROM complaints WHERE id = ?",
            (complaint_id,),
        )
        target = cursor.fetchone()
        if not target:
            return jsonify({"error": "Complaint not found"}), 404

        target_cat = target["category"].strip().lower()
        target_loc = normalize_location(target["location"])

        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.auto_flagged, c.created_at, c.updated_at,
                w.name AS assigned_worker_name,
                w.role AS assigned_worker_role,
                w.phone AS assigned_worker_phone
            FROM complaints c
            LEFT JOIN workers w ON c.assigned_worker_id = w.id
            ORDER BY c.id DESC
        """
        )
        all_rows = cursor.fetchall()

        history = []
        for row in all_rows:
            if (
                row["category"].strip().lower() == target_cat
                and normalize_location(row["location"]) == target_loc
            ):
                history.append(dict(row))

    return jsonify(
        {
            "target_id": complaint_id,
            "target_ticket_no": target["ticket_no"],
            "category": target["category"],
            "location": target["location"],
            "total": len(history),
            "history": history,
        }
    )


@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    description = request.form.get("description", "").strip()
    user_priority = request.form.get("priority", "Low").strip()

    if not category or category not in CATEGORIES:
        return jsonify({"error": f"Invalid category. Must be one of {CATEGORIES}"}), 400

    if not location:
        return jsonify({"error": "Location is required"}), 400

    if not description:
        return jsonify({"error": "Description is required"}), 400

    if user_priority not in PRIORITIES:
        return jsonify({"error": f"Invalid priority. Must be one of {PRIORITIES}"}), 400

    # Auto priority detection based on description keywords
    final_priority, auto_flagged, trigger_keyword = detect_priority(
        description, user_priority
    )

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
                status, assigned_worker_id, photo_filename, auto_flagged, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'Reported', NULL, ?, ?, ?, ?)
        """,
            (
                ticket_no,
                category,
                location,
                description,
                final_priority,
                photo_filename,
                auto_flagged,
                now,
                now,
            ),
        )
        new_id = cursor.lastrowid
        conn.commit()

        rec_map = get_recurrence_info(cursor)
        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.auto_flagged,
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
        r_info = rec_map.get(
            new_id,
            {"is_recurring": False, "recurrence_count": 0, "total_occurrences": 1},
        )
        new_complaint["is_recurring"] = r_info["is_recurring"]
        new_complaint["recurrence_count"] = r_info["recurrence_count"]
        new_complaint["total_occurrences"] = r_info["total_occurrences"]

    return (
        jsonify(
            {
                "success": True,
                "complaint": new_complaint,
                "auto_flagged": bool(auto_flagged),
                "trigger_keyword": trigger_keyword,
            }
        ),
        201,
    )


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

        rec_map = get_recurrence_info(cursor)
        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.auto_flagged,
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
        r_info = rec_map.get(
            complaint_id,
            {"is_recurring": False, "recurrence_count": 0, "total_occurrences": 1},
        )
        updated["is_recurring"] = r_info["is_recurring"]
        updated["recurrence_count"] = r_info["recurrence_count"]
        updated["total_occurrences"] = r_info["total_occurrences"]

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

        rec_map = get_recurrence_info(cursor)
        cursor.execute(
            """
            SELECT 
                c.id, c.ticket_no, c.category, c.location, c.description,
                c.priority, c.status, c.assigned_worker_id, c.photo_filename,
                c.auto_flagged,
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
        r_info = rec_map.get(
            complaint_id,
            {"is_recurring": False, "recurrence_count": 0, "total_occurrences": 1},
        )
        updated["is_recurring"] = r_info["is_recurring"]
        updated["recurrence_count"] = r_info["recurrence_count"]
        updated["total_occurrences"] = r_info["total_occurrences"]

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
