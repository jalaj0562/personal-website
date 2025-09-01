from flask import Flask, render_template, session, redirect, url_for, send_from_directory
import os
import json
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for sessions

ANALYTICS_FILE = "analytics.json"

# ---------------- CONTEXT PROCESSOR ----------------
@app.context_processor
def inject_now():
    return {'now': datetime.now}


# ---------------- ANALYTICS FUNCTIONS ----------------
def load_analytics():
    default = {"page_views": {}, "sessions": {}, "visits": 0, "durations": []}
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r") as f:
                data = json.load(f)
            # Ensure all keys exist
            for k, v in default.items():
                if k not in data:
                    data[k] = v
            return data
        except:
            return default
    return default


def save_analytics(data):
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def update_analytics(page):
    data = load_analytics()

    # Track page views
    data["page_views"][page] = data["page_views"].get(page, 0) + 1
    data["visits"] += 1

    # Track sessions
    if "session_id" not in session:
        session["session_id"] = str(time.time())
        session["start_time"] = time.time()
        data["sessions"][session["session_id"]] = {"pages": [page]}
    else:
        sid = session["session_id"]
        if sid not in data["sessions"]:  # FIX: prevent KeyError
            data["sessions"][sid] = {"pages": []}
        data["sessions"][sid]["pages"].append(page)

    save_analytics(data)


@app.after_request
def track_duration(response):
    if "start_time" in session:
        duration = time.time() - session["start_time"]
        data = load_analytics()
        data["durations"].append(duration)
        save_analytics(data)
    return response


# ---------------- ROUTES ----------------
@app.route("/")
def route_home():
    update_analytics("home")
    return render_template("home.html", title="Home")


@app.route("/about")
def route_about():
    update_analytics("about")
    return render_template("about.html", title="About")


@app.route("/services")
def route_services():
    update_analytics("services")
    return render_template("services.html", title="Projects")


@app.route("/experience")
def route_experience():
    update_analytics("experience")
    return render_template("experience.html", title="Experience")


@app.route("/contact")
def route_contact():
    update_analytics("contact")
    return render_template("contact.html", title="Contact")


@app.route("/dashboard")
def route_dashboard():
    data = load_analytics()
    total_visits = data["visits"]

    # Most visited page
    most_visited = max(data["page_views"], key=data["page_views"].get) if data["page_views"] else "N/A"

    # Bounce rate = sessions with only 1 page / total sessions
    bounces = sum(1 for s in data["sessions"].values() if len(s["pages"]) == 1)
    bounce_rate = round((bounces / len(data["sessions"])) * 100, 2) if data["sessions"] else 0

    # Average session duration
    avg_duration = round(sum(data["durations"]) / len(data["durations"]), 2) if data["durations"] else 0

    return render_template(
        "dashboard.html",
        page_views=data["page_views"],
        total_visits=total_visits,
        most_visited=most_visited,
        bounce_rate=bounce_rate,
        avg_duration=avg_duration,
        title="Analytics Dashboard"
    )


# ---------------- RESUME DOWNLOAD ----------------
@app.route("/download_resume")
def download_resume():
    return send_from_directory("static/files", "resume.pdf", as_attachment=True)


# ---------------- START APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
