from flask import Flask
import requests
from base64 import b64encode
import os

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get('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')  # Get the token from an environment variable
REPO_NAME = 'nitsofts/hsmdatarefresh'
FILE_PATH = 'hsmdatarefresh/datarefresh.json'
BRANCH = 'main'

def update_github_file(message):
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get the file's SHA (necessary for updating)
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha')

    # Update the file
    data = {
        'message': 'Update datarefresh.json',
        'content': b64encode(message.encode()).decode(),
        'branch': BRANCH,
        'sha': sha
    }
    response = requests.put(url, headers=headers, json=data)
    return response.ok

@app.route('/update-file', methods=['GET'])
def update_file():
    if update_github_file('Hello World'):
        return 'File updated successfully'
    else:
        return 'Failed to update the file', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
