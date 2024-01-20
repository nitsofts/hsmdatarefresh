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

def update_github_file(message):
    current_time_ms = int(round(time.time() * 1000))  # Current time in milliseconds
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
        return False, current_time_ms, error_message

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
        return False, current_time_ms, error_message

    return True, current_time_ms, "File updated successfully"

@app.route('/update-file', methods=['GET'])
def update_file():
    success, current_time_ms, message = update_github_file('Update requested')
    response_data = {
        "lastRefreshInMs": current_time_ms,
        "lastRefreshMessage": message
    }
    if success:
        return response_data, 200
    else:
        return response_data, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
