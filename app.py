import os
from flask import Flask, render_template_string, request, redirect, url_for
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
# (ជំនួស URL និង Key របស់ Firebase អ្នកនៅទីនេះ ឬប្រើ Environment Variables)
FIREBASE_URL = "https://YOUR_FIREBASE_PROJECT_ID-default-rtdb.firebaseio.com/"
ADMIN_PASSWORD = "admin"  # Password សម្រាប់ Login ចូល Admin Panel

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            return redirect(url_for("admin_panel"))
        else:
            return render_template_string(LOGIN_PAGE, error="Password មិនត្រឹមត្រូវ!")
    return render_template_string(LOGIN_PAGE, error=None)

@app.route("/admin")
def admin_panel():
    try:
        # ទាញយកទិន្នន័យពី Firebase
        response = requests.get(f"{FIREBASE_URL}/users.json")
        data = response.json() if response.ok else {}
        users = data if data else {}
    except Exception as e:
        users = {}
    
    return render_template_string(ADMIN_PAGE, users=users)

@app.route("/approve/<user_id>", methods=["POST"])
def approve_user(user_id):
    plan = request.form.get("plan") # ឧ. 3M, 6M, 1Y, Life
    # Logic សម្រាប់បង្កើត Key និងបញ្ជូនទៅ Firebase របស់អ្នកនៅទីនេះ
    # ...
    return redirect(url_for("admin_panel"))

@app.route("/delete/<user_id>", methods=["POST"])
def delete_user(user_id):
    requests.delete(f"{FIREBASE_URL}/users/{user_id}.json")
    return redirect(url_for("admin_panel"))

# HTML Templates (អាចកែសម្រួល Design តាម Admin Panel របស់អ្នកស្រេចចិត្ត)
LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <title>Admin Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex justify-content-center align-items-center vh-100">
    <div class="card p-4 shadow" style="width: 350px;">
        <h3 class="text-center mb-3">Admin Panel</h3>
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

ADMIN_PAGE = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <title>Web Admin Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>🎛️ Key Management Admin Panel</h2>
            <a href="/" class="btn btn-danger btn-sm">Logout</a>
        </div>
        <div class="card shadow p-4">
            <h4>បញ្ជី User ទាំងអស់</h4>
            <table class="table table-striped mt-3">
                <thead>
                    <tr>
                        <th>User ID / Username</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for uid, uinfo in users.items() %}
                    <tr>
                        <td>{{ uid }}</td>
                        <td>{{ uinfo.get('status', 'Pending') }}</td>
                        <td>
                            <form action="/approve/{{ uid }}" method="POST" class="d-inline">
                                <button type="submit" name="plan" value="3M" class="btn btn-success btn-sm">3M</button>
                                <button type="submit" name="plan" value="1Y" class="btn btn-warning btn-sm">1Y</button>
                            </form>
                            <form action="/delete/{{ uid }}" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3" class="text-center text-muted">គ្មានទិន្នន័យ User ទេ</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
