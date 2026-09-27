from flask import Flask, send_from_directory, request, jsonify, session
from pathlib import Path
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_FOLDER = PROJECT_ROOT / "frontend"
DATA_FOLDER = PROJECT_ROOT / "data"
DATABASE = DATA_FOLDER / "users.db"

DATA_FOLDER.mkdir(parents=True, exist_ok=True)

# Used for login sessions
# For production, put a strong random value in an environment variable.
app.secret_key = "hyper-speed-demo-secret-key"


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


init_database()


# --------------------------------------------------
# PAGE HELPER
# --------------------------------------------------

def page(filename):
    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


# --------------------------------------------------
# LOGIN PROTECTION
# --------------------------------------------------

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        return function(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

@app.route("/")
def login():
    return page("index.html")


# --------------------------------------------------
# SIGN UP API
# --------------------------------------------------

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
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

    connection = get_db()

    existing_user = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing_user:
        connection.close()

        return jsonify({
            "success": False,
            "message": "Username already exists."
        }), 409

    password_hash = generate_password_hash(password)

    connection.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password_hash)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully."
    })


# --------------------------------------------------
# LOGIN API
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login_api():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Please enter username and password."
        }), 400

    connection = get_db()

    user = connection.execute(
        "SELECT id, username, password FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    if not check_password_hash(user["password"], password):
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "ACCESS GRANTED",
        "username": user["username"]
    })


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return page("index.html")

    return page("dashboard.html")


# --------------------------------------------------
# MONITORING
# --------------------------------------------------

@app.route("/monitoring")
def monitoring():

    if "user_id" not in session:
        return page("index.html")

    return page("monitoring.html")


# --------------------------------------------------
# HISTORY
# --------------------------------------------------

@app.route("/history")
def history():

    if "user_id" not in session:
        return page("index.html")

    return page("history.html")


# --------------------------------------------------
# ALERTS
# --------------------------------------------------

@app.route("/alerts")
def alerts():

    if "user_id" not in session:
        return page("index.html")

    return page("alerts.html")


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

@app.route("/settings")
def settings():

    if "user_id" not in session:
        return page("index.html")

    return page("settings.html")


# --------------------------------------------------
# CURRENT USER
# --------------------------------------------------

@app.route("/me")
def current_user():

    if "user_id" not in session:
        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "username": session["username"]
    })


# --------------------------------------------------
# FRONTEND FILES
# --------------------------------------------------

@app.route("/<path:filename>")
def frontend_files(filename):

    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)