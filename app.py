import logging
from base64 import b64encode
import requests
from flask import Flask
import os
import json
import time
from datetime import datetime, timedelta

# Basic logging setup for debugging
logging.basicConfig(level=logging.INFO)

# Initialize the Flask application
app = Flask(__name__)

# Configuration for GitHub API
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # GitHub API token
REPO_NAME = 'nitsofts/hsmdatarefresh'  # Repository name on GitHub
FILE_PATH = 'datarefresh.json'  # Path to the file in the repository
BRANCH = 'main'  # Branch to update in the repository
DATA_REFRESH_URL = 'https://nitsofts.github.io/hsmdatarefresh/datarefresh.json'  # URL to fetch current data

# Fetch current data from the GitHub Pages URL
def fetch_current_data():
    try:
        response = requests.get(DATA_REFRESH_URL)
        if response.status_code == 200:
            return json.loads(response.content)  # Parse JSON content
        else:
            logging.error(f"Error fetching current data: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logging.error(f"Exception during fetch: {str(e)}")
        return None

# Update the datarefresh.json file on GitHub
def update_datarefresh_github(current_time_ms, frequent_request_count, message):
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get the SHA of the current file on GitHub for updating
    get_response = requests.get(url, headers=headers)
    if get_response.status_code != 200:
        error_message = f"Error getting file SHA: {get_response.status_code}, {get_response.text}"
        logging.error(error_message)
        return False, error_message
    sha = get_response.json().get('sha')

    # Prepare and encode the updated content
    content = json.dumps([{
        "lastRefreshInMs": current_time_ms,
        "frequentRequest": frequent_request_count,
        "message": message  # Include the message key here
    }])
    encoded_content = b64encode(content.encode()).decode()

    # Update the file on GitHub
    update_data = {
        'message': 'Update datarefresh.json',
        'content': encoded_content,
        'branch': BRANCH,
        'sha': sha
    }
    put_response = requests.put(url, headers=headers, json=update_data)
    if put_response.status_code != 200:
        error_message = f"Error updating file: {put_response.status_code}, {put_response.text}"
        logging.error(error_message)
        return False, error_message

    return True

@app.route('/datarefresh', methods=['GET'])
def datarefresh():
    current_data = fetch_current_data()
    current_time_ms = int(round(time.time() * 1000))

    if current_data:
        last_refresh_in_ms = current_data[0].get("lastRefreshInMs", 0)
        frequent_request_count = current_data[0].get("frequentRequest", 0)
        time_diff = current_time_ms - last_refresh_in_ms

        if time_diff > 180000:  # 3 minutes
            # Update lastRefreshInMs and reset frequentRequest count if successful
            message = "Data updated successfully"
            success = update_datarefresh_github(current_time_ms, 0, message)
            if success:
                last_refresh_in_ms = current_time_ms  # Update only on successful push
                frequent_request_count = 0
        else:
            # Increment frequentRequest count and do not update lastRefreshInMs
            frequent_request_count += 1
            message = "Frequent request detected"
            update_datarefresh_github(last_refresh_in_ms, frequent_request_count, message)
            success = True  # For response purposes, reflect that frequentRequest count was updated

        # Calculate the time difference in seconds and format it
        time_diff_seconds = int(time_diff / 1000)
        last_refreshed_in_string = format_timedelta(time_diff_seconds)

    else:
        success = False
        frequent_request_count = 0
        message = "Failed to fetch current data"
        last_refresh_in_ms = current_time_ms  # Set to current time if data fetch fails
        last_refreshed_in_string = "N/A"

    response_data = {
        "lastRefreshInMs": last_refresh_in_ms,
        "lastRefreshedInString": last_refreshed_in_string,
        "frequentRequest": frequent_request_count,
        "message": message
    }
    return response_data, 200 if success else 500

def format_timedelta(seconds):
    # Format the timedelta in a human-readable string
    delta = timedelta(seconds=seconds)
    days, seconds = delta.days, delta.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days} {'day' if days == 1 else 'days'} ago"
    elif hours > 0:
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    elif minutes > 0:
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    else:
        return f"{seconds} {'second' if seconds == 1 else 'seconds'} ago"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
