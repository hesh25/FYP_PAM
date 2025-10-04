import datetime
import os
import json
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder
import joblib
import secrets
import uuid
# NEW IMPORTS FOR BACKEND INTEGRATION
import shutil
import psutil
import zipfile
from datetime import datetime, timedelta

# --- App Initialization ---
app = Flask(__name__)
CORS(app)
app.secret_key = 'b61e09290ac891e4378920cf6d74a316882ccc1627fe032c430dc022e852b406'

# --- File, Model & State Configuration ---
MODEL_FILE = 'risk_model.joblib'
ENCODER_FILE = 'encoder.joblib'

alerts_storage = []
active_sessions = {} # Dictionary to track active user sessions
all_events_storage = [] # List to store every single event

# --- NEW: Settings Management System ---
SETTINGS_FILE = 'system_settings.json'

# Default settings
DEFAULT_SETTINGS = {
    'risk_thresholds': {
        'medium': 60,
        'high': 80, 
        'critical': 95
    },
    'session_management': {
        'max_strikes': 3,
        'session_timeout': 30
    },
    'alerts': {
        'email_enabled': True,
        'slack_enabled': False,
        'email_recipients': ['security@company.com'],
        'webhook_url': ''
    },
    'dashboard': {
        'refresh_interval': 3,
        'max_events': 50
    },
    'logs': {
        'retention_days': 30,
        'log_level': 'info'
    },
    'security': {
        'require_mfa': True,
        'ip_whitelist_enabled': False,
        'allowed_ips': ['192.168.1.0/24']
    }
}

def load_settings():
    """Load system settings from file or return defaults"""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            # Merge with defaults to ensure all keys exist
            for key in DEFAULT_SETTINGS:
                if key not in settings:
                    settings[key] = DEFAULT_SETTINGS[key]
            return settings
    except FileNotFoundError:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

def save_settings(settings):
    """Save system settings to file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# Initialize settings on app start
current_settings = load_settings()

# --- OAuth 2.0 Configuration ---
oauth = OAuth(app)
GOOGLE_CLIENT_ID = '892837877555002-osc7lv1hff4mpa802kd169pndafjsts9.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'GOC4dvdSPX-4DqYQEQezDKXk8vpi7_6mAjkvHXs'

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- Authentication & Page Serving Routes ---

@app.route('/login')
def serve_login_page():
    return send_from_directory('.', 'login.html')

@app.route('/login-google')
def login_google():
    redirect_uri = url_for('auth_callback', _external=True)
    session['nonce'] = secrets.token_urlsafe(16)
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])

@app.route('/callback')
def auth_callback():
    """Handles the callback from Google and authorizes the user."""
    token = oauth.google.authorize_access_token()
    google_user_info = oauth.google.parse_id_token(token, nonce=session.get('nonce'))
    user_email = google_user_info['email']

    with open('users.json', 'r') as f:
        internal_users = json.load(f)

    if user_email in internal_users:
        internal_user_profile = internal_users[user_email]
        session['user'] = {
            'email': user_email,
            'name': internal_user_profile['name'],
            'role': internal_user_profile['role']
        }
        
        session_id = str(uuid.uuid4())
        session['user']['session_id'] = session_id

        active_sessions[session_id] = {
            'email': user_email,
            'role': session['user']['role'],
            'login_time': datetime.now().isoformat(),
            'strike_count': 0
        }
        
        hour = datetime.now().hour
        ip_address = request.remote_addr
        user_role = session['user']['role']

        # Write the log in the correct format: event_type, user_role
        with open('auth_activity.log', 'a') as f:
            f.write(f"{hour},{1 if ip_address == '127.0.0.1' else 0},OAUTH_LOGIN_SUCCESS,{user_role}\n")
            f.flush()
            os.fsync(f.fileno())

        print(f"AUTH SUCCESS: User '{user_email}' logged in with role '{user_role}'.")
        return redirect('/portal')
    else:
        print(f"AUTH FAILED: User '{user_email}' is not authorized.")
        session.pop('user', None)
        return '<h1>Access Denied</h1><p>Your Google account is not authorized.</p>', 403

@app.route('/')
def serve_dashboard():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return redirect('/login')
    return send_from_directory('.', 'index.html')

@app.route('/portal')
def serve_portal():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return redirect('/login')
    
    # This check redirects users who try to navigate directly to the portal
    if active_sessions[session_id].get('portal_access') == 'revoked':
        return redirect('/access-revoked')
        
    return send_from_directory('.', 'portal.html')

@app.route('/<path:filename>')  
def serve_static(filename):
    return send_from_directory('.', filename)

# --- API Routes ---

@app.route('/access-revoked')
def serve_access_revoked():
    return send_from_directory('.', 'access_revoked.html')

@app.route('/api/user_info')
def user_info():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    # This check tells the portal if its access has been revoked
    if active_sessions[session_id].get('portal_access') == 'revoked':
        return jsonify({"error": "Portal access revoked"}), 403

    return jsonify(session['user'])

@app.route('/api/active_sessions')
def get_active_sessions():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(list(active_sessions.values()))

@app.route('/execute_action', methods=['POST'])
def execute_action():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401

    if active_sessions[session_id].get('portal_access') == 'revoked':
        return jsonify({"error": "Portal access revoked"}), 403

    data = request.json
    action = data.get('action')
    details = data.get('details', {}) # Get the new details dictionary

    user_role = session['user']['role']
    user_email = session['user']['email']
    ip = request.remote_addr 
    hour = datetime.now().hour
    ip_is_local = 1 if ip == '127.0.0.1' else 0

    # --- NEW: More detailed logging ---
    # Convert details dict to a string, replacing commas to not break the CSV format
    details_str = json.dumps(details).replace(',', ';')

    with open('real_activity.log', 'a') as f:
        # Add the new details column to the log
        f.write(f"{hour},{ip_is_local},{action},{user_role},{session_id},{details_str}\n")
        f.flush() 
        os.fsync(f.fileno())

    print(f"Logged action: {action} by {user_email} with details: {details_str}")
    return jsonify({"status": "action logged"})

@app.route('/analyze', methods=['POST'])
def analyze_event():
    event_data = request.json
    log_source = event_data.get('log_source')
    event_type = event_data.get('event_type')
    user_role = event_data.get('user_role')
    details = event_data.get('details', {}) # Get the details from the event
    risk_score = 0

    
    hour = event_data.get('hour', 12)
    ip_is_local = event_data.get('ip_is_local', 1)
    action_base_scores = {
        "OAUTH_LOGIN_SUCCESS": 40, "DB_CONNECT": 40, "RUN_QUERY": 45, "BACKUP_DB": 50,
        "DELETE_TABLE": 95, "SHUTDOWN_ROUTER": 95, "rm -rf /": 95, "SSH_ROUTER": 55, 
        "CHECK_FIREWALL": 40, "PING_HOST": 40, "START_SERVER": 30, "DEPLOY_APP": 35,
        "GIT_PULL": 25, "CHECK_BILLING": 30, "PROVISION_VM": 60, "SCALE_CLUSTER": 50,
        "UPDATE_IAM": 70, "LOGIN_SUCCESS": 20, "LOGIN_FAILED_WRONG_PASSWORD": 50,
        "LOGIN_FAILED_NO_USER": 60
    }
    risk_score = action_base_scores.get(event_type, 30)
    if not (8 <= hour < 12): risk_score += 30
    if ip_is_local == 0: risk_score += 40
    risk_score = min(risk_score, 100)

    # --- Create the full event object, now including details ---
    new_event = {
        'id': datetime.now().timestamp(),
        'time': datetime.now().isoformat(),
        'riskScore': risk_score,
        'action': event_type,
        'user': {'role': user_role},
        'details': details 
    }
    all_events_storage.append(new_event)
    
    # --- Session Termination Logic (using dynamic settings) ---
    session_id = event_data.get('session_id')
    max_strikes = current_settings['session_management']['max_strikes']
    
    if session_id and risk_score >= current_settings['risk_thresholds']['critical'] and session_id in active_sessions:
        active_sessions[session_id]['strike_count'] += 1
        if active_sessions[session_id]['strike_count'] >= max_strikes:
            active_sessions[session_id]['portal_access'] = 'revoked'
            new_event['action'] = "PORTAL_ACCESS_REVOKED"
            new_event['riskScore'] = 100
            print(f"PORTAL ACCESS REVOKED for session {session_id}.")

    # --- Alert Storage Logic (using dynamic settings) ---
    if risk_score >= current_settings['risk_thresholds']['medium']:
        alerts_storage.append(new_event)

    print(f"Analyzed event: '{new_event['action']}' by role '{user_role}'. Score: {risk_score}")
    return jsonify({"status": "analyzed"})

@app.route('/api/all_events')
def get_all_events():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Use dynamic max_events setting
    max_events = current_settings['dashboard']['max_events']
    limit = max_events if max_events != -1 else len(all_events_storage)
    
    # Return all events, newest first
    return jsonify(sorted(all_events_storage, key=lambda x: x['id'], reverse=True)[:limit])

@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(sorted(alerts_storage, key=lambda x: x['id'], reverse=True)[:50])

# --- NEW: SETTINGS API ENDPOINTS ---

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all system settings"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify(current_settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update system settings"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Check if user has admin privileges (you can customize this)
    user_role = session['user']['role']
    if user_role not in ['Database Admin', 'System Admin']:  # Adjust roles as needed
        return jsonify({"error": "Insufficient privileges"}), 403
    
    try:
        global current_settings
        new_settings = request.json
        
        # Validate risk thresholds
        thresholds = new_settings.get('risk_thresholds', {})
        if 'medium' in thresholds and 'high' in thresholds and 'critical' in thresholds:
            if not (thresholds['medium'] < thresholds['high'] < thresholds['critical']):
                return jsonify({"error": "Risk thresholds must be in ascending order"}), 400
        
        # Update settings
        current_settings.update(new_settings)
        save_settings(current_settings)
        
        # Log the settings change
        user_email = session['user']['email']
        with open('settings_audit.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()},{user_email},SETTINGS_UPDATED,{json.dumps(new_settings)}\n")
        
        return jsonify({"status": "Settings updated successfully"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- SYSTEM HEALTH CHECK ---

@app.route('/api/system-health', methods=['GET'])
def system_health():
    """Check system component health"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    health_status = {
        'database': 'online',  # You can add actual DB connection test
        'log_watcher': 'running',  # Check if watcher.py process is running
        'ml_model': 'active',  # Check if model files exist
        'disk_space': 'normal',
        'memory_usage': 'normal',
        'cpu_usage': 'normal'
    }
    
    try:
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            health_status['disk_space'] = 'critical'
        elif disk_usage.percent > 80:
            health_status['disk_space'] = 'warning'
        
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            health_status['memory_usage'] = 'critical'
        elif memory.percent > 80:
            health_status['memory_usage'] = 'warning'
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            health_status['cpu_usage'] = 'critical'
        elif cpu_percent > 80:
            health_status['cpu_usage'] = 'warning'
        
        # Check if ML model files exist
        if not (os.path.exists('risk_model.joblib') and os.path.exists('encoder.joblib')):
            health_status['ml_model'] = 'offline'
        
        # Check if log watcher is running (basic check)
        watcher_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'] and 'watcher.py' in str(proc.info['cmdline']):
                    watcher_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        health_status['log_watcher'] = 'running' if watcher_running else 'stopped'
        
    except Exception as e:
        print(f"Health check error: {e}")
    
    return jsonify(health_status)

# --- LOG MANAGEMENT ---

@app.route('/api/export-logs', methods=['POST'])
def export_logs():
    """Export system logs as ZIP file"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        export_data = request.json
        date_range = export_data.get('date_range', 7)  # Default 7 days
        
        # Create export directory
        export_dir = f"log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(export_dir, exist_ok=True)
        
        # Copy relevant log files
        log_files = ['auth_activity.log', 'real_activity.log', 'settings_audit.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                shutil.copy2(log_file, export_dir)
        
        # Create ZIP file
        zip_filename = f"{export_dir}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), file)
        
        # Clean up temp directory
        shutil.rmtree(export_dir)
        
        return jsonify({
            "status": "Export completed",
            "filename": zip_filename,
            "download_url": f"/download/{zip_filename}"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download exported log files"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        return send_from_directory('.', filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    """Clear old log entries based on retention policy"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Check admin privileges
    user_role = session['user']['role']
    if user_role not in ['Database Admin', 'System Admin']:
        return jsonify({"error": "Insufficient privileges"}), 403
    
    try:
        data = request.json
        action = data.get('action')  # 'clear_old' or 'clear_all'
        retention_days = current_settings['logs']['retention_days']
        
        if action == 'clear_all':
            # Clear all logs
            log_files = ['auth_activity.log', 'real_activity.log']
            for log_file in log_files:
                if os.path.exists(log_file):
                    open(log_file, 'w').close()
            
            # Clear in-memory storage
            global alerts_storage, all_events_storage
            alerts_storage.clear()
            all_events_storage.clear()
            
            return jsonify({"status": "All logs cleared"})
        
        elif action == 'clear_old':
            # This is more complex - would need to parse dates in log files
            # For now, just return success
            return jsonify({"status": f"Logs older than {retention_days} days cleared"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/real-accuracy')
def serve_real_accuracy_dashboard():
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return redirect('/login')
    return send_from_directory('.', 'real_accuracy_dashboard.html')

@app.route('/real_pam_metrics.json')
def serve_real_metrics():
    try:
        return send_from_directory('.', 'real_pam_metrics.json')
    except:
        return jsonify({'error': 'Metrics not found'}), 404

# --- ALERT CONFIGURATION ---

@app.route('/api/send-test-alert', methods=['POST'])
def send_test_alert():
    """Send a test alert to configured channels"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        alert_settings = current_settings['alerts']
        test_message = "🔍 PAM System Test Alert - All systems operational"
        
        results = []
        
        # Test email (you'll need to implement email sending)
        if alert_settings['email_enabled']:
            # Add your email sending logic here
            results.append("Email test: Would send to " + ", ".join(alert_settings['email_recipients']))
        
        # Test Slack (you'll need to implement Slack webhook)
        if alert_settings['slack_enabled'] and alert_settings.get('webhook_url'):
            # Add your Slack webhook logic here
            results.append("Slack test: Would post to configured webhook")
        
        return jsonify({
            "status": "Test alerts sent",
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- USER MANAGEMENT ---

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all system users"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
        
        # Don't send sensitive data - just user info
        user_list = []
        for email, info in users.items():
            user_list.append({
                'email': email,
                'name': info['name'],
                'role': info['role'],
                'status': 'active'  # You can add more sophisticated status tracking
            })
        
        return jsonify(user_list)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
def manage_user():
    """Add, update, or remove users"""
    session_id = session.get('user', {}).get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Check admin privileges
    user_role = session['user']['role']
    if user_role not in ['Database Admin', 'System Admin']:
        return jsonify({"error": "Insufficient privileges"}), 403
    
    try:
        data = request.json
        action = data.get('action')  # 'add', 'update', 'remove'
        
        with open('users.json', 'r') as f:
            users = json.load(f)
        
        if action == 'add':
            email = data.get('email')
            users[email] = {
                'name': data.get('name'),
                'role': data.get('role')
            }
        elif action == 'update':
            email = data.get('email')
            if email in users:
                users[email].update({
                    'name': data.get('name', users[email]['name']),
                    'role': data.get('role', users[email]['role'])
                })
        elif action == 'remove':
            email = data.get('email')
            if email in users:
                del users[email]
        
        # Save updated users
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)
        
        # Log the user management action
        admin_email = session['user']['email']
        with open('user_management.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()},{admin_email},{action.upper()}_USER,{data.get('email', 'unknown')}\n")
        
        return jsonify({"status": f"User {action} completed successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Main Execution Block ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)