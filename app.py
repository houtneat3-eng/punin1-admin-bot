from datetime import datetime, timedelta
import secrets
from flask import Flask, redirect, render_template_string, request, url_for
import requests

app = Flask(__name__)

FIREBASE_URL = (
    "https://punin-mobile-unlock-default-rtdb.asia-southeast1.firebasedatabase.app"
)
ADMIN_PASSWORD = "admin"  # អ្នកអាចប្តូរ Password ចូល Admin Panel បាននៅទីនេះ


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
  if duration_choice == "3 ខែ (3 Months)":
    return (now + timedelta(days=90)).strftime("%Y-%m-%d"), "3M"
  elif duration_choice == "6 ខែ (6 Months)":
    return (now + timedelta(days=180)).strftime("%Y-%m-%d"), "6M"
  elif duration_choice == "1 ឆ្នាំ (1 Year)":
    return (now + timedelta(days=365)).strftime("%Y-%m-%d"), "1Y"
  elif duration_choice == "Lifetime (អាយុកាល)":
    return "2099-12-31", "LIFE"
  else:
    return (now + timedelta(days=365)).strftime("%Y-%m-%d"), "1Y"


@app.route("/", methods=["GET", "POST"])
def login():
  error = None
  if request.method == "POST":
    if request.form.get("password") == ADMIN_PASSWORD:
      return redirect(url_for("admin_dashboard"))
    else:
      error = "Password មិនត្រឹមត្រូវ!"
  return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route("/admin")
def admin_dashboard():
  pending_users = db_get("pending_users")
  approved_users = db_get("approved_users")
  version_info = db_get("app_control/version_info")
  return render_template_string(
      ADMIN_TEMPLATE,
      pending_users=pending_users,
      approved_users=approved_users,
      version_info=version_info,
  )


@app.route("/push_version", methods=["POST"])
def push_version():
  ver = request.form.get("version")
  url = request.form.get("download_url")
  if ver and url:
    payload = {
        "version": ver,
        "download_url": url,
        "status": "pending",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    db_put("app_control/version_info", payload)
  return redirect(url_for("admin_dashboard"))


@app.route("/set_version_status/<status>", methods=["POST"])
def set_version_status(status):
  info = db_get("app_control/version_info")
  if info and isinstance(info, dict):
    info["status"] = status
    db_put("app_control/version_info", info)
  return redirect(url_for("admin_dashboard"))


@app.route("/confirm/<username>", methods=["POST"])
def confirm_user(username):
  duration = request.form.get("duration")
  key = request.form.get("license_key")
  pending_users = db_get("pending_users")

  if pending_users and username in pending_users:
    user_data = pending_users[username]
    exp_date, _ = calculate_expiry(duration)

    approved_payload = {
        "email": user_data.get("email", ""),
        "password": user_data.get("password", ""),
        "license_key": key,
        "duration": duration,
        "expiry_date": exp_date,
        "status": "ACTIVE",
        "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if db_put(f"approved_users/{username}", approved_payload):
      db_delete(f"pending_users/{username}")
  return redirect(url_for("admin_dashboard"))


@app.route("/delete_pending/<username>", methods=["POST"])
def delete_pending(username):
  db_delete(f"pending_users/{username}")
  return redirect(url_for("admin_dashboard"))


@app.route("/set_pass/<username>", methods=["POST"])
def set_pass(username):
  new_pass = request.form.get("new_password")
  approved_users = db_get("approved_users")
  if approved_users and username in approved_users:
    approved_users[username]["password"] = new_pass
    db_put(f"approved_users/{username}", approved_users[username])
  return redirect(url_for("admin_dashboard"))


@app.route("/renew/<username>", methods=["POST"])
def renew_user(username):
  duration = request.form.get("duration")
  approved_users = db_get("approved_users")
  if approved_users and username in approved_users:
    exp_date, code = calculate_expiry(duration)
    new_key = generate_random_key(code)
    approved_users[username]["expiry_date"] = exp_date
    approved_users[username]["duration"] = duration
    approved_users[username]["license_key"] = new_key
    approved_users[username]["status"] = "ACTIVE"
    db_put(f"approved_users/{username}", approved_users[username])
  return redirect(url_for("admin_dashboard"))


@app.route("/delete_approved/<username>", methods=["POST"])
def delete_approved(username):
  db_delete(f"approved_users/{username}")
  return redirect(url_for("admin_dashboard"))


# HTML Templates (Frontend Web UI)
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <title>Admin Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light d-flex justify-content-center align-items-center vh-100">
    <div class="card bg-secondary p-4 shadow" style="width: 350px;">
        <h3 class="text-center mb-3">🛠️ Admin Login</h3>
        {% if error %}
            <div class="alert alert-danger py-2">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Password:</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Login</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <title>Online Admin Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>🔑 ONLINE ADMIN ACTIVATION & CONTROL CENTER</h2>
            <a href="/" class="btn btn-danger btn-sm">Logout</a>
        </div>

        <!-- VERSION CONTROL SECTION -->
        <div class="card bg-secondary p-3 mb-4">
            <h4>🚀 Auto-Update & Version Approve</h4>
            <form action="/push_version" method="POST" class="row g-2 mt-2">
                <div class="col-md-4">
                    <input type="text" name="version" class="form-control" placeholder="Version (ឧ. 2.1)" value="{{ version_info.get('version', '') if version_info else '' }}" required>
                </div>
                <div class="col-md-6">
                    <input type="text" name="download_url" class="form-control" placeholder="Link ទាញយក (Google Drive/Mediafire)" value="{{ version_info.get('download_url', '') if version_info else '' }}" required>
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-warning w-100">Push Update</button>
                </div>
            </form>
            <div class="mt-2">
                <p>Status បច្ចុប្បន្ន៖ <b>{{ version_info.get('status', 'pending') if version_info else 'N/A' }}</b></p>
                <form action="/set_version_status/approved" method="POST" class="d-inline">
                    <button type="submit" class="btn btn-success btn-sm">✅ Approve Version</button>
                </form>
                <form action="/set_version_status/pending" method="POST" class="d-inline">
                    <button type="submit" class="btn btn-danger btn-sm">❌ Block Version</button>
                </form>
            </div>
        </div>

        <!-- PENDING USERS SECTION -->
        <div class="card bg-secondary p-3 mb-4">
            <h4>⏳ Pending Approval Users</h4>
            <div class="table-responsive mt-3">
                <table class="table table-dark table-striped">
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Email</th>
                            <th>Action & Keygen</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if pending_users %}
                            {% for user, data in pending_users.items() %}
                            <tr>
                                <td>{{ user }}</td>
                                <td>{{ data.get('email', '') }}</td>
                                <td>
                                    <form action="/confirm/{{ user }}" method="POST" class="row g-1">
                                        <div class="col-auto">
                                            <select name="duration" class="form-select form-select-sm">
                                                <option>3 ខែ (3 Months)</option>
                                                <option>6 ខែ (6 Months)</option>
                                                <option selected>1 ឆ្នាំ (1 Year)</option>
                                                <option>Lifetime (អាយុកាល)</option>
                                            </select>
                                        </div>
                                        <div class="col-auto">
                                            <input type="text" name="license_key" class="form-control form-control-sm" placeholder="Key..." required>
                                        </div>
                                        <div class="col-auto">
                                            <button type="submit" class="btn btn-success btn-sm">Confirm</button>
                                        </div>
                                    </form>
                                    <form action="/delete_pending/{{ user }}" method="POST" class="d-inline mt-1">
                                        <button type="submit" class="btn btn-danger btn-sm mt-1">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="3" class="text-center">គ្មានទិន្នន័យរង់ចាំទេ</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- APPROVED USERS SECTION -->
        <div class="card bg-secondary p-3 mb-4">
            <h4>👥 Active / Approved Users</h4>
            <div class="table-responsive mt-3">
                <table class="table table-dark table-striped">
                    <thead>
                        <tr>
                            <th>User Info</th>
                            <th>Management Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if approved_users %}
                            {% for user, data in approved_users.items() %}
                            <tr>
                                <td>
                                    <b>User:</b> {{ user }} | <b>Pass:</b> {{ data.get('password') }}<br>
                                    <b>Key:</b> {{ data.get('license_key') }}<br>
                                    <b>ផុតកំណត់៖</b> {{ data.get('expiry_date') }} ({{ data.get('duration') }})
                                </td>
                                <td>
                                    <form action="/set_pass/{{ user }}" method="POST" class="d-flex gap-1 mb-1">
                                        <input type="text" name="new_password" class="form-control form-control-sm" placeholder="Pass ថ្មី" style="width: 100px;" required>
                                        <button type="submit" class="btn btn-primary btn-sm">Set Pass</button>
                                    </form>
                                    <form action="/renew/{{ user }}" method="POST" class="d-flex gap-1 mb-1">
                                        <select name="duration" class="form-select form-select-sm" style="width: 120px;">
                                            <option>3 ខែ (3 Months)</option>
                                            <option>6 ខែ (6 Months)</option>
                                            <option selected>1 ឆ្នាំ (1 Year)</option>
                                            <option>Lifetime (អាយុកាល)</option>
                                        </select>
                                        <button type="submit" class="btn btn-warning btn-sm">Renew</button>
                                    </form>
                                    <form action="/delete_approved/{{ user }}" method="POST">
                                        <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="2" class="text-center">គ្មានទិន្នន័យ Active User ទេ</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=False)
