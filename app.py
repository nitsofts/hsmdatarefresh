import logging
from base64 import b64encode
import requests
from flask import Flask
import os
import json
import time

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)

# GitHub configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = 'nitsofts/hsmdatarefresh'
FILE_PATH = 'datarefresh.json'
BRANCH = 'main'
DATA_REFRESH_URL = 'https://nitsofts.github.io/hsmdatarefresh/datarefresh.json'

def fetch_current_data():
    try:
        response = requests.get(DATA_REFRESH_URL)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            logging.error(f"Error fetching current data: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logging.error(f"Exception during fetch: {str(e)}")
        return None

def format_time(milliseconds):
    timestamp = datetime.fromtimestamp(milliseconds / 1000)
    return timestamp.strftime('%Y %b %d, %I:%M %p')

def update_github_file(message, current_time_ms):
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get the file's SHA
    get_response = requests.get(url, headers=headers)
    if get_response.status_code != 200:
        error_message = f"Error getting file SHA: {get_response.status_code}, {get_response.text}"
        logging.error(error_message)
        return False, error_message

    sha = get_response.json().get('sha')

    # Prepare the content to be updated
    content = json.dumps([{
        "lastRefreshInMs": current_time_ms,
        "lastRefreshMessage": message
    }])
    encoded_content = b64encode(content.encode()).decode()

    # Update the file
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


@app.route('/update-file', methods=['GET'])
def update_file():
    current_data = fetch_current_data()
    current_time_ms = int(round(time.time() * 1000))
    current_time_str = format_time(current_time_ms)

    if current_data:
        last_refresh_in_ms = current_data[0].get("lastRefreshInMs", 0)
        if current_time_ms - last_refresh_in_ms > 180000:  # 3 minutes
            success, message = update_github_file('Update requested', current_time_ms)
        else:
            success, message = True, "Update not required - last refresh was less than 3 minutes ago"
    else:
        success, message = False, "Failed to fetch current data"

    response_data = {
        "lastRefreshInMs": current_time_ms,
        "lastRefreshInString": current_time_str,
        "lastRefreshMessage": message
    }
    return response_data, 200 if success else 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
