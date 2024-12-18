import os
import urllib3
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Redmine configuration
load_dotenv()
REDMINE_URL = os.getenv('REDMINE_URL')
API_KEY = os.getenv('API_KEY')

# Connect to Redmine
try:
    redmine = Redmine(REDMINE_URL, key=API_KEY, requests={'verify': False})
    print("Connected to Redmine successfully.")
except Exception as e:
    print(f"Failed to connect to Redmine: {e}")
    exit()


def get_issues_by_query(contract_num: str = None, project_stage: int = None,
                        time_from: str = None, time_to: str = None):
    filter_kwargs = {}
    start_date = datetime(year=1970, month=1, day=1).date()
    if contract_num:
        filter_kwargs['cf_13'] = contract_num
    if project_stage:
        filter_kwargs['cf_18'] = project_stage
    if time_from or time_to:
        if time_from:
            time_from = datetime.strptime(time_from, '%d.%m.%Y').date()
        if time_to:
            time_to = datetime.strptime(time_to, '%d.%m.%Y').date()
        filter_kwargs['start_date'] = f"><{time_from if time_from else start_date}|{time_to if time_to else ''}"

    if filter_kwargs:
        issues = redmine.issue.filter(**filter_kwargs)
    else:
        issues = redmine.issue.all()
    return issues


def get_user_name(issue) -> str | None:
    try:
        user_name = issue.assigned_to.name
    except ResourceAttrError:
        try:
            parent_issue = redmine.issue.get(issue.parent)
        except ResourceAttrError:
            return None
        user_name = get_user_name(parent_issue)
    return user_name


def get_user_hours(issues) -> dict:
    user_burned_hours_dict = defaultdict(int)
    for issue in issues:
        user_name = get_user_name(issue)
        if not user_name:
            continue
        user_hours = issue.spent_hours
        user_burned_hours_dict[user_name] += user_hours
    return user_burned_hours_dict


def get_burned_hours(**kwargs):
    issues = get_issues_by_query(time_from='16.12.2024', time_to='18.12.2024')
    user_burned_hours = get_user_hours(issues)
    print(user_burned_hours)


if __name__ == '__main__':
    get_burned_hours()
