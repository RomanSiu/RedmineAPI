import os
import urllib3
from datetime import datetime

from dotenv import load_dotenv
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError, ResourceNotFoundError

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Redmine configuration
load_dotenv()
REDMINE_URL = os.getenv('REDMINE_URL')
API_KEY = os.getenv('API_KEY')


# Connect to Redmine
try:
    print(REDMINE_URL, API_KEY)
    redmine = Redmine(REDMINE_URL, key=API_KEY, requests={'verify': False})
except Exception as e:
    print(f"Failed to connect to Redmine: {e}")
    exit()


def get_catalog_type_activity():
    time_from = datetime.strptime("2024-01-01", '%Y-%m-%d').date()
    issues = redmine.issue.filter(update_on=f"><{time_from}")

    issue_types = []
    activities = []

    for issue in issues:
        try:
            issue_type = issue.custom_fields.get(19).value
            if issue_type not in issue_types and issue_type is not None:
                issue_types.append(issue_type)
        except (ResourceAttrError, AttributeError):
            ...

        time_entries = issue.time_entries

        for entry in time_entries:
            activity = entry.activity.name
            if activity not in activities and activity is not None:
                activities.append(activity)
    return {'issue_type': issue_types, 'activity': activities}
