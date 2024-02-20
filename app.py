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

# ... (other code remains the same)

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
