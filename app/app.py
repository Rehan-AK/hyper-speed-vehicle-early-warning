from flask import Flask, send_from_directory, request, jsonify, session
from pathlib import Path
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_FOLDER = PROJECT_ROOT / "frontend"
DATA_FOLDER = PROJECT_ROOT / "data"
DATABASE = DATA_FOLDER / "users.db"

DATA_FOLDER.mkdir(parents=True, exist_ok=True)

# College-project secret key.
# Replace this before any real deployment.
app.secret_key = "hyper-speed-mca-demo-secret-2026"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL UNIQUE,
                vehicle_id TEXT NOT NULL,
                speed REAL NOT NULL,
                start_distance REAL NOT NULL,
                current_distance REAL NOT NULL,
                eta REAL NOT NULL,
                direction TEXT,
                source TEXT,
                status TEXT NOT NULL DEFAULT 'DETECTED',
                alert_triggered INTEGER NOT NULL DEFAULT 0,
                result TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        demo_username = "rehan"
        demo_password = "Rehan@123"

        existing = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (demo_username,)
        ).fetchone()

        if existing is None:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (demo_username, generate_password_hash(demo_password))
            )

        db.commit()


init_database()


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def page(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


def api_login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Login required."
            }), 401
        return fn(*args, **kwargs)

    return wrapped


def clean_text(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def clean_number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------
# MAIN PAGES
# ---------------------------------------------------------

@app.route("/")
def login():
    return page("index.html")


@app.route("/dashboard")
def dashboard():
    return page("dashboard.html")


@app.route("/monitoring")
def monitoring():
    return page("monitoring.html")


@app.route("/history")
def history():
    return page("history.html")


@app.route("/alerts")
def alerts():
    return page("alerts.html")


@app.route("/settings")
def settings():
    return page("settings.html")


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------

@app.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}

    username = clean_text(data.get("username"))
    password = clean_text(data.get("password"))

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Please enter username and password."
        }), 400

    with get_db() as db:
        user = db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "username": user["username"]
    })


@app.route("/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or {}

    username = clean_text(data.get("username"))
    password = clean_text(data.get("password"))

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    if len(username) < 3:
        return jsonify({
            "success": False,
            "message": "Username must contain at least 3 characters."
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters."
        }), 400

    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            db.commit()
    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Username already exists."
        }), 409

    return jsonify({
        "success": True,
        "message": "Account created successfully."
    })


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


@app.route("/me")
def current_user():
    if "user_id" not in session:
        return jsonify({
            "authenticated": False
        })

    return jsonify({
        "authenticated": True,
        "username": session.get("username")
    })


# ---------------------------------------------------------
# SHARED VEHICLE EVENT API
# ---------------------------------------------------------

@app.route("/api/vehicle-events", methods=["POST"])
@api_login_required
def vehicle_event():
    data = request.get_json(silent=True) or {}

    action = clean_text(data.get("action")).upper()
    event_key = clean_text(data.get("event_key"))
    vehicle_id = clean_text(data.get("vehicle_id"))

    if not event_key or not vehicle_id:
        return jsonify({
            "success": False,
            "message": "event_key and vehicle_id are required."
        }), 400

    speed = clean_number(data.get("speed"))
    start_distance = clean_number(data.get("start_distance"))
    current_distance = clean_number(data.get("current_distance"))
    eta = clean_number(data.get("eta"))
    direction = clean_text(data.get("direction"))
    source = clean_text(data.get("source"), "camera")
    result = clean_text(data.get("result"))

    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM vehicle_events WHERE event_key = ?",
            (event_key,)
        ).fetchone()

        if action == "START":
            if existing is None:
                db.execute("""
                    INSERT INTO vehicle_events (
                        event_key,
                        vehicle_id,
                        speed,
                        start_distance,
                        current_distance,
                        eta,
                        direction,
                        source,
                        status,
                        alert_triggered
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DETECTED', 0)
                """, (
                    event_key,
                    vehicle_id,
                    speed,
                    start_distance,
                    current_distance,
                    eta,
                    direction,
                    source
                ))
            else:
                db.execute("""
                    UPDATE vehicle_events
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE event_key = ?
                """, (event_key,))

        elif action == "ALERT":
            if existing is None:
                db.execute("""
                    INSERT INTO vehicle_events (
                        event_key,
                        vehicle_id,
                        speed,
                        start_distance,
                        current_distance,
                        eta,
                        direction,
                        source,
                        status,
                        alert_triggered
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'WARNING', 1)
                """, (
                    event_key,
                    vehicle_id,
                    speed,
                    start_distance,
                    current_distance,
                    eta,
                    direction,
                    source
                ))
            else:
                db.execute("""
                    UPDATE vehicle_events
                    SET
                        speed = ?,
                        current_distance = ?,
                        eta = ?,
                        source = ?,
                        status = 'WARNING',
                        alert_triggered = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE event_key = ?
                """, (
                    speed,
                    current_distance,
                    eta,
                    source,
                    event_key
                ))

        elif action == "COMPLETE":
            if existing is None:
                db.execute("""
                    INSERT INTO vehicle_events (
                        event_key,
                        vehicle_id,
                        speed,
                        start_distance,
                        current_distance,
                        eta,
                        direction,
                        source,
                        status,
                        alert_triggered,
                        result
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', ?, ?)
                """, (
                    event_key,
                    vehicle_id,
                    speed,
                    start_distance,
                    current_distance,
                    eta,
                    direction,
                    source,
                    1 if result.upper() == "WARNING" else 0,
                    result or "NORMAL"
                ))
            else:
                db.execute("""
                    UPDATE vehicle_events
                    SET
                        speed = ?,
                        current_distance = ?,
                        eta = ?,
                        source = ?,
                        status = 'COMPLETED',
                        result = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE event_key = ?
                """, (
                    speed,
                    current_distance,
                    eta,
                    source,
                    result or "NORMAL",
                    event_key
                ))

        else:
            return jsonify({
                "success": False,
                "message": "Unknown event action."
            }), 400

        db.commit()

    return jsonify({
        "success": True,
        "action": action,
        "event_key": event_key
    })


@app.route("/api/vehicle-events", methods=["GET"])
@api_login_required
def list_vehicle_events():
    try:
        limit = int(request.args.get("limit", 100))
    except (TypeError, ValueError):
        limit = 100

    limit = max(1, min(limit, 500))

    with get_db() as db:
        rows = db.execute("""
            SELECT
                id,
                event_key,
                vehicle_id,
                speed,
                start_distance,
                current_distance,
                eta,
                direction,
                source,
                status,
                alert_triggered,
                result,
                detected_at,
                updated_at
            FROM vehicle_events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return jsonify({
        "success": True,
        "events": [dict(row) for row in rows]
    })


@app.route("/api/vehicle-stats", methods=["GET"])
@api_login_required
def vehicle_stats():
    with get_db() as db:
        totals = db.execute("""
            SELECT
                COUNT(*) AS vehicles,
                SUM(CASE WHEN speed > 85 THEN 1 ELSE 0 END) AS high_speed,
                SUM(CASE WHEN alert_triggered = 1 THEN 1 ELSE 0 END) AS warnings,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS passes
            FROM vehicle_events
        """).fetchone()

    return jsonify({
        "success": True,
        "stats": {
            "vehicles": int(totals["vehicles"] or 0),
            "highSpeed": int(totals["high_speed"] or 0),
            "warnings": int(totals["warnings"] or 0),
            "passes": int(totals["passes"] or 0)
        }
    })


# ---------------------------------------------------------
# FRONTEND STATIC FILES
# ---------------------------------------------------------

@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
