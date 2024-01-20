import logging
from base64 import b64encode
import requests
from flask import Flask
import os

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
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get the file's SHA
    get_response = requests.get(url, headers=headers)
    if get_response.status_code != 200:
        logging.error(f"Error getting file SHA: {get_response.status_code}, {get_response.text}")
        return False

    sha = get_response.json().get('sha')

    # Update the file
    update_data = {
        'message': 'Update datarefresh.json',
        'content': b64encode(message.encode()).decode(),
        'branch': BRANCH,
        'sha': sha
    }
    put_response = requests.put(url, headers=headers, json=update_data)
    if put_response.status_code != 200:
        logging.error(f"Error updating file: {put_response.status_code}, {put_response.text}")
        return False

    return True

@app.route('/update-file', methods=['GET'])
def update_file():
    if update_github_file('Hello World'):
        return 'File updated successfully'
    else:
        return 'Failed to update the file', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
