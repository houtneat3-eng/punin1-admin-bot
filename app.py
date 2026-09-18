from datetime import datetime, timedelta
import os
import secrets
from flask import Flask, flash, redirect, render_template_string, request, url_for
import requests

app = Flask(__name__)
app.secret_key = "punin_secret_key_change_this"

# ព័ត៌មាន Firebase របស់អ្នក
FIREBASE_URL = "https://punin-mobile-unlock-default-rtdb.asia-southeast1.firebasedatabase.app"
ADMIN_PASSWORD = "admin"  # លេខសម្ងាត់សម្រាប់ចូល Admin Panel (អាចប្តូរតាមចិត្ត)


def db_get(path):
  try:
    res = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=5)
    return res.json() or {}
  except Exception:
    return {}


def db_put(path, data):
  try:
    res = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=5)
    return res.ok
  except Exception:
    return False


def db_delete(path):
  try:
    res = requests.delete(f"{FIREBASE_URL}/{path}.json", timeout=5)
    return res.ok
  except Exception:
    return False


def generate_random_key(duration_label="1Y"):
  p1, p2 = secrets.token_hex(2).upper(), secrets.token_hex(2).upper()
  return f"PUNIN-{duration_label}-{p1}-{p2}"


def calculate_expiry(duration_choice):
  now = datetime.now()
  if duration_choice == "3M":
    return (now + timedelta(days=90)).strftime("%Y-%m-%d"), "3M"
  elif duration_choice == "6M":
    return (now + timedelta(days=180)).strftime("%Y-%m-%d"), "6M"
  elif duration_choice == "1Y":
    return (now + timedelta(days=365)).strftime("%Y-%m-%d"), "1Y"
  elif duration_choice == "LIFE":
    return "2099-12-31", "LIFE"
  return (now + timedelta(days=365)).strftime("%Y-%m-%d"), "1Y"


# HTML Template សម្រាប់បង្ហាញលើ Web យ៉ាងស្អាត និងងាយស្រួលប្រើ
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <title>Punin Admin Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <h2 class="mb-4 text-center">🛡️ Punin Software Admin Panel</h2>
    
    {% if not logged_in %}
        <div class="card mx-auto p-4 shadow" style="max-width: 400px;">
            <h4 class="mb-3 text-center">Admin Login</h4>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Password:</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Login</button>
            </form>
        </div>
    {% else %}
        <div class="d-flex justify-content-between mb-3">
            <h4>បញ្ជីរង់ចាំអនុម័ត (Pending Users)</h4>
            <a href="/logout" class="btn btn-danger btn-sm">Logout</a>
        </div>
        
        <div class="card shadow mb-4">
            <div class="card-body">
                <table class="table table-bordered table-striped">
                    <thead class="table-dark">
                        <tr>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Password</th>
                            <th>Actions (Duration & Key Generation)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if pending %}
                            {% for username, data in pending.items() %}
                            <tr>
                                <td><b>{{ username }}</b></td>
                                <td>{{ data.email }}</td>
                                <td><code>{{ data.password }}</code></td>
                                <td>
                                    <a href="/approve/{{ username }}/3M" class="btn btn-success btn-sm">✅ 3 ខែ</a>
                                    <a href="/approve/{{ username }}/6M" class="btn btn-warning btn-sm">✅ 6 ខែ</a>
                                    <a href="/approve/{{ username }}/1Y" class="btn btn-info btn-sm text-white">✅ 1 ឆ្នាំ</a>
                                    <a href="/approve/{{ username }}/LIFE" class="btn btn-dark btn-sm">✅ Lifetime</a>
                                    <a href="/reject/{{ username }}" class="btn btn-danger btn-sm">❌ Delete</a>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="4" class="text-center text-muted">គ្មាន User រង់ចាំទេ</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>

        <h4 class="mb-3">បញ្ជី User ដែលបានសកម្មរួច (Approved Users)</h4>
        <div class="card shadow">
            <div class="card-body">
                <table class="table table-bordered table-striped">
                    <thead class="table-secondary">
                        <tr>
                            <th>Username</th>
                            <th>Email</th>
                            <th>License Key</th>
                            <th>Duration</th>
                            <th>Expiry Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if approved %}
                            {% for username, data in approved.items() %}
                            <tr>
                                <td><b>{{ username }}</b></td>
                                <td style="max-width: 150px; word-break: break-all;">{{ data.email }}</td>
                                <td><code class="text-primary fw-bold">{{ data.license_key }}</code></td>
                                <td>{{ data.duration }}</td>
                                <td>{{ data.expiry_date }}</td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="5" class="text-center text-muted">គ្មាន User សកម្មទេ</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    {% endif %}
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  logged_in = request.cookies.get("auth") == "true"

  if request.method == "POST":
    if request.form.get("password") == ADMIN_PASSWORD:
      resp = redirect(url_for("index"))
      resp.set_cookie("auth", "true")
      return resp

  pending = db_get("pending_users")
  approved = db_get("approved_users")
  return render_template_string(
      HTML_TEMPLATE,
      logged_in=logged_in,
      pending=pending if isinstance(pending, dict) else {},
      approved=approved if isinstance(approved, dict) else {},
  )


@app.route("/logout")
def logout():
  resp = redirect(url_for("index"))
  resp.set_cookie("auth", "", expires=0)
  return resp


@app.route("/approve/<username>/<duration>")
def approve_user(username, duration):
  if request.cookies.get("auth") != "true":
    return redirect(url_for("index"))

  pending_users = db_get("pending_users")
  if pending_users and username in pending_users:
    user_data = pending_users[username]
    exp_date, code = calculate_expiry(duration)
    activation_key = generate_random_key(code)

    approved_payload = {
        "email": user_data.get("email"),
        "password": user_data.get("password"),
        "license_key": activation_key,
        "duration": duration,
        "expiry_date": exp_date,
        "status": "ACTIVE",
        "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if db_put(f"approved_users/{username}", approved_payload):
      db_delete(f"pending_users/{username}")

  return redirect(url_for("index"))


@app.route("/reject/<username>")
def reject_user(username):
  if request.cookies.get("auth") != "true":
    return redirect(url_for("index"))
  db_delete(f"pending_users/{username}")
  return redirect(url_for("index"))


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=7860, debug=True)
