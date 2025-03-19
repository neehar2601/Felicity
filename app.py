from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import json
import os
import hashlib
from datetime import datetime
import secrets

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(16)
CORS(app)

# File paths
POINTS_DATA_FILE = 'data/points_data.json'
POINTS_HISTORY_FILE = 'data/points_history.json'
ADMIN_CREDENTIALS_FILE = 'data/admin_credentials.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Initialize data files if they don't exist
def initialize_data_files():
    # Points data
    if not os.path.exists(POINTS_DATA_FILE):
        initial_data = [
            {"group": "Alchemist", "sports": 0, "cultural": 0},
            {"group": "Mavericks", "sports": 0, "cultural": 0},
            {"group": "Phoenix", "sports": 0, "cultural": 0},
            {"group": "Titans", "sports": 0, "cultural": 0}
        ]
        with open(POINTS_DATA_FILE, 'w') as f:
            json.dump(initial_data, f)

    # Points history
    if not os.path.exists(POINTS_HISTORY_FILE):
        with open(POINTS_HISTORY_FILE, 'w') as f:
            json.dump([], f)

    # Admin credentials (default password:)
    if not os.path.exists(ADMIN_CREDENTIALS_FILE):
        default_username = "admin1"
        default_password = "admin123"
        hashed_password = hashlib.sha256(default_password.encode()).hexdigest()  # Hash the password
        admin_credentials = {
            "username": default_username,
            "password_hash": hashed_password
        }
        with open(ADMIN_CREDENTIALS_FILE, 'w') as f:
            json.dump(admin_credentials, f)


initialize_data_files()

# Helper functions
def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f)

def verify_admin(username, password):
    admin_credentials = load_data(ADMIN_CREDENTIALS_FILE)
    entered_password_hash = hashlib.sha256(password.encode()).hexdigest()  # Hash the entered password
    # ADDING PRINT STATEMENTS FOR DEBUGGING
    #print(f"Entered username: {username}")
    #print(f"Entered password hash: {entered_password_hash}")
    #print(f"Stored username: {admin_credentials['username']}")
    #print(f"Stored password hash: {admin_credentials['password_hash']}")

    return (username == admin_credentials["username"] and
            entered_password_hash == admin_credentials["password_hash"])

def calculate_ranks(points_data):
    # Calculate total points and add to data
    for item in points_data:
        item["total"] = item["sports"] + item["cultural"]

    # Sort by total points (descending)
    sorted_data = sorted(points_data, key=lambda x: x["total"], reverse=True)

    # Assign ranks
    current_rank = 1
    prev_total = -1
    skip_ranks = 0

    for i, item in enumerate(sorted_data):
        if item["total"] != prev_total:
            current_rank = i + 1 - skip_ranks
            prev_total = item["total"]
        else:
            skip_ranks += 1

        item["rank"] = current_rank

    return sorted_data

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/points', methods=['GET'])
def get_points():
    points_data = load_data(POINTS_DATA_FILE)
    ranked_data = calculate_ranks(points_data)
    return jsonify(ranked_data)

@app.route('/api/points/history', methods=['GET'])
def get_points_history():
    points_history = load_data(POINTS_HISTORY_FILE)
    return jsonify(points_history)

@app.route('/api/points/update', methods=['POST'])
def update_points():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    group = data.get('group')
    category = data.get('category')
    event = data.get('event')
    points = data.get('points')

    if not all([group, category, event, points]):
        return jsonify({"error": "Missing required fields"}), 400

    # Update points data
    points_data = load_data(POINTS_DATA_FILE)
    for item in points_data:
        if item["group"] == group:
            item[category] += points

    save_data(points_data, POINTS_DATA_FILE)

    # Add to history
    points_history = load_data(POINTS_HISTORY_FILE)
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "group": group,
        "category": category,
        "event": event,
        "points": points
    }
    points_history.append(history_entry)
    save_data(points_history, POINTS_HISTORY_FILE)

    return jsonify({"success": True, "message": f"Added {points} points to {group} for {event}"})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if verify_admin(username, password):
        session['admin_logged_in'] = True
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({"success": True})

@app.route('/api/admin/status', methods=['GET'])
def admin_status():
    return jsonify({"logged_in": session.get('admin_logged_in', False)})

if __name__ == '__main__':
    app.run(debug=True)