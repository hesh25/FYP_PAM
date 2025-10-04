import time
import os
import requests
import json

# --- Configuration ---
API_ENDPOINT = 'http://127.0.0.1:5000/analyze'
LOG_FILES_TO_WATCH = {
    'auth_activity.log': 'auth',
    'real_activity.log': 'action'
}
POLL_INTERVAL = 3 # seconds

# --- State Tracking ---
lines_processed_counts = {file: 0 for file in LOG_FILES_TO_WATCH}

def analyze_log_entry(log_line, log_type):
    """Parses a log line and sends it to the analysis API with its type."""
    try:
        parts = log_line.strip().split(',')
        payload = {}
        
        # Auth logs have 4 parts
        if log_type == 'auth' and len(parts) >= 4:
            payload = {
                'hour': int(parts[0]),
                'ip_is_local': int(parts[1]),
                'event_type': parts[2],
                'user_role': parts[3],
                'log_source': log_type
            }
        # Action logs now have 6 parts (..., session_id, details)
        elif log_type == 'action' and len(parts) >= 6:
            details_str = parts[5]
            # Convert the details string back into a dictionary
            details_dict = json.loads(details_str.replace(';', ','))

            payload = {
                'hour': int(parts[0]),
                'ip_is_local': int(parts[1]),
                'event_type': parts[2],
                'user_role': parts[3],
                'session_id': parts[4],
                'details': details_dict, # <-- Pass the details dictionary
                'log_source': log_type
            }
        else:
            return # Ignore malformed lines

        print(f"Watcher detected new '{log_type}' log. Sending for analysis: {payload['event_type']}")
        requests.post(API_ENDPOINT, json=payload)

    except Exception as e:
        print(f"Error processing log line: '{log_line.strip()}'. Error: {e}")

# (The rest of the watcher.py script remains the same)
def initialize_line_counts():
    for file in LOG_FILES_TO_WATCH:
        try:
            with open(file, 'r') as f:
                lines_processed_counts[file] = len(f.readlines())
            print(f"Found {lines_processed_counts[file]} existing lines in '{file}'.")
        except FileNotFoundError:
            print(f"Log file '{file}' not found. Will start watching.")

print("Multi-log watcher started...")
initialize_line_counts()

while True:
    for file, log_type in LOG_FILES_TO_WATCH.items():
        try:
            with open(file, 'r') as f:
                lines = f.readlines()
                total_lines_now = len(lines)
                if total_lines_now > lines_processed_counts[file]:
                    new_lines_to_process = lines[lines_processed_counts[file]:]
                    for line in new_lines_to_process:
                        analyze_log_entry(line, log_type)
                    lines_processed_counts[file] = total_lines_now
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"An error occurred watching '{file}': {e}")
    time.sleep(POLL_INTERVAL)