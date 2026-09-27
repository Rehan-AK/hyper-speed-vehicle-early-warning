from flask import Flask, send_from_directory
from pathlib import Path

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_FOLDER = PROJECT_ROOT / "frontend"


def page(filename):
    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


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


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


if __name__ == "__main__":
    app.run(debug=True)
