import logging
from base64 import b64encode
import requests
from flask import Flask
import os
import json
import time
from datetime import datetime

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

# Convert milliseconds to a formatted time string
def format_time(milliseconds):
    timestamp = datetime.fromtimestamp(milliseconds / 1000)
    return timestamp.strftime('%Y %b %d, %I:%M:%S %p')

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
def update_datarefresh_github(message, current_time_ms):
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
    current_time_str = format_time(current_time_ms)
    content = json.dumps([{
        "lastRefreshInMs": current_time_ms,
        "lastRefreshInString": current_time_str,
        "lastRefreshMessage": message
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

    return True, "File updated successfully"

# Flask route to handle the update process
@app.route('/datarefresh', methods=['GET'])
def datarefresh():
    # Fetch current data and determine if update is needed
    current_data = fetch_current_data()
    current_time_ms = int(round(time.time() * 1000))

    # Check if an update is required based on time elapsed
    if current_data:
        last_refresh_in_ms = current_data[0].get("lastRefreshInMs", 0)
        if current_time_ms - last_refresh_in_ms > 180000:  # 3 minutes
            success, message = update_datarefresh_github('Update requested', current_time_ms)
        else:
            success, message = True, "Update not required - last refresh was less than 3 minutes ago"
    else:
        success, message = False, "Failed to fetch current data"

    # Build response data
    response_data = {
        "lastRefreshInMs": current_time_ms,
        "lastRefreshInString": format_time(current_time_ms),
        "lastRefreshMessage": message
    }
    return response_data, 200 if success else 500

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
