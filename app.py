import logging
from base64 import b64encode, b64decode
import requests
from flask import Flask, request
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

def get_current_file_content(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = b64decode(response.json()['content']).decode()
        return json.loads(content)
    else:
        return None

def update_github_file(message, current_time_ms):
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get current file content
    current_content = get_current_file_content(url, headers)
    if current_content:
        last_refresh_time_ms = current_content[0]['lastRefreshInMs']
        # Check if the last refresh was more than 3 minutes ago
        if current_time_ms - last_refresh_time_ms > 180000:
            content_to_update = json.dumps([{
                "lastRefreshInMs": current_time_ms,
                "lastRefreshMessage": message
            }])
            encoded_content = b64encode(content_to_update.encode()).decode()
            sha = current_content[0]['sha']

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
        else:
            return True, "Update not required - last refresh was less than 3 minutes ago"
    else:
        return False, "Error retrieving current file content"

@app.route('/update-file', methods=['GET'])
def update_file():
    current_time_ms = int(round(time.time() * 1000))  # Current time in milliseconds
    success, message = update_github_file('Update requested', current_time_ms)
    response_data = {
        "lastRefreshInMs": current_time_ms,
        "lastRefreshMessage": message
    }
    return response_data, 200 if success else 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
