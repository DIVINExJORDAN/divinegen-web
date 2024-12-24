from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit
import json
import os
import requests
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from marshmallow import Schema, fields, ValidationError

app = Flask(__name__)
socketio = SocketIO(app)

app.secret_key = os.urandom(24)

# File paths
STOCK_FILE = 'accounts.json'
GIVEAWAYS_FILE = 'giveaways.json'
stats_file = 'stats.json'
USER_FILE = 'users.json'

# OAuth2 client setup for Discord
DISCORD_CLIENT_ID = '1300806547970064464'
DISCORD_CLIENT_SECRET = 'q5zW0BvYYtN2ZYYY8KpPD4fAgFHn4qEE'
DISCORD_API_URL = 'https://discord.com/api/v10'
DISCORD_REDIRECT_URI = 'http://localhost:5000/callback'
client = WebApplicationClient(DISCORD_CLIENT_ID)
    
def load_accounts():
    try:
        with open('accounts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_accounts(accounts):
    with open('accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)


# Utility functions
def load_file(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return default

def save_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_users():
    with open(USER_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def find_user(username):
    users = load_users()['users']
    return next((user for user in users if user['username'] == username), None)

# Ensure the user.json file exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w') as file:
        json.dump({"users": []}, file)

# Authentication Decorator

# Routes
@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/stock', methods=['GET', 'POST'])
def manage_stock():
    stock = load_file(STOCK_FILE, {})
    accounts = load_accounts()  # Load accounts from accounts.json
    if request.method == 'POST':
        data = request.json
        category = data.get('category')
        service = data.get('service')
        accounts_list = data.get('accounts', [])
        if category not in stock:
            stock[category] = {}
        if service not in stock[category]:
            stock[category][service] = []
        stock[category][service].extend(accounts_list)
        save_file(STOCK_FILE, stock)
        return jsonify({'success': True, 'message': f'Added accounts to {service} in {category}.'})
    return render_template('stock.html', stock=stock, accounts=accounts)

@app.route('/giveaways', methods=['GET', 'POST'])
def giveaways():
    giveaways = load_file(GIVEAWAYS_FILE, [])
    if request.method == 'POST':
        data = request.json
        giveaways.append({
            'name': data.get('name'),
            'reward': data.get('reward'),
            'end_time': data.get('end_time')
        })
        save_file(GIVEAWAYS_FILE, giveaways)
        return jsonify({'success': True, 'message': 'Giveaway added successfully!'})
    is_empty = len(giveaways) == 0
    return render_template('giveaways.html', giveaways=giveaways, is_empty=is_empty)

@app.route('/fetch_account/<service_name>', methods=['GET'])
def fetch_account(service_name):
    accounts = load_accounts()  # Load accounts from accounts.json
    if service_name not in accounts or not accounts[service_name]:
        return jsonify({"error": "No accounts available for this service."}), 404

    # Get the first account (user:pass) from the list
    account = accounts[service_name].pop(0)  # Remove it from the list after fetching
    save_accounts(accounts)  # Save the updated accounts back to the file

    return jsonify({"account": account}), 200
    
@app.route('/stats/json', methods=['GET'])
def get_stats_json():
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        return jsonify(stats)
    return jsonify({"error": "Stats not available"}), 500

@app.route('/stats', methods=['GET'])
def stats_page():
    # Ensure logs.json exists and read its content
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            stats = json.load(f)

        # Pass stats to the template for rendering
        return render_template('stats.html', stats=stats)
    
    return "Error: Stats file not found", 500

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    return redirect(url_for('login'))  # Updated here

@app.route('/discord-login')
def discord_login():
    discord_authorization_url = client.prepare_request_uri(
        f"https://discord.com/oauth2/authorize",
        redirect_uri=DISCORD_REDIRECT_URI,
        scope="identity email"
    )
    return redirect(discord_authorization_url)

if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w') as file:
        json.dump({"users": []}, file)

def load_users():
    with open(USER_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def find_user(username):
    users = load_users()['users']
    return next((user for user in users if user['username'] == username), None)

@app.route('/services', methods=['GET', 'POST'])
def services():
    accounts = load_accounts()

    if request.method == 'POST':
        # Add new service
        if 'add_service' in request.form:
            service_name = request.form['service_name']
            accounts[service_name] = []  # Initialize with an empty list of accounts
            save_accounts(accounts)
            flash(f"Service '{service_name}' added successfully!", "success")

        # Remove service
        elif 'remove_service' in request.form:
            service_name = request.form['service_name']
            if service_name in accounts:
                del accounts[service_name]
                save_accounts(accounts)
                flash(f"Service '{service_name}' removed successfully!", "success")
            else:
                flash(f"Service '{service_name}' does not exist.", "danger")

    return render_template('services.html', accounts=accounts)

@app.route('/manage_service/<service_name>', methods=['GET', 'POST'])
def manage_service(service_name):
    accounts = load_accounts()
    if service_name not in accounts:
        flash(f"Service '{service_name}' does not exist.", "danger")
        return redirect(url_for('services'))

    if request.method == 'POST':
        # Edit accounts for the service
        new_accounts = request.form['accounts']
        accounts[service_name] = [account.strip() for account in new_accounts.splitlines() if account.strip()]
        save_accounts(accounts)
        flash(f"Accounts for service '{service_name}' updated successfully!", "success")

    return render_template('manage_service.html', service_name=service_name, accounts=accounts)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/services/summary', methods=['GET'])
def service_summary():
    accounts = load_accounts()  # Load accounts from accounts.json
    summary = {service: len(accounts_list) for service, accounts_list in accounts.items()}
    return jsonify(summary)
    
@app.route('/callback')
def discord_callback():
    # Step 1: Get the authorization code
    token_url = f"https://discord.com/oauth2/token"
    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'code': request.args.get('code'),
        'grant_type': 'authorization_code',
        'redirect_uri': DISCORD_REDIRECT_URI,
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    # Step 2: Use the access token to get user data
    user_info_url = f"{DISCORD_API_URL}/users/@me"
    headers = {
        "Authorization": f"Bearer {token_json['access_token']}"
    }
    user_info_response = requests.get(user_info_url, headers=headers)
    user_info = user_info_response.json()

    # Here you can store the user info (like name, email) in session
    session['user'] = user_info
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, threaded=True)
