import os
import urllib3
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv
from openpyxl import Workbook
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError

from logger import logger

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Redmine configuration
load_dotenv()
REDMINE_URL = os.getenv('REDMINE_URL')
API_KEY = os.getenv('API_KEY')

# Connect to Redmine
try:
    redmine = Redmine(REDMINE_URL, key=API_KEY, requests={'verify': False})
    logger.info('Redmine connected successfully')
except Exception as e:
    logger.error(f"Failed to connect to Redmine: {e}")
    exit()


def logging_func(func):
    def inner(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = None
            logger.error(f"Failed to run {func.__name__}: {e}")
        else:
            return result
        return result
    return inner


async def get_issues_by_query(contract_num: str = None, project_stage: str | int = None,
                              time_from: str = None, time_to: str = None):
    filter_kwargs = {}
    start_date = datetime(year=1970, month=1, day=1).date()
    if contract_num:
        filter_kwargs['cf_13'] = contract_num
    if project_stage:
        try:
            project_stage = int(project_stage)
        except ValueError:
            pass
        filter_kwargs['cf_18'] = project_stage
    if time_from or time_to:
        if time_from:
            time_from = datetime.strptime(time_from, '%Y-%m-%d').date()
        if time_to:
            time_to = datetime.strptime(time_to, '%Y-%m-%d').date()
        filter_kwargs['start_date'] = f"><{time_from if time_from else start_date}|{time_to if time_to else ''}"

    if filter_kwargs:
        issues = redmine.issue.filter(**filter_kwargs)
    else:
        issues = redmine.issue.all()
    return issues


@logging_func
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
        try:
            user_hours = issue.spent_hours
        except ResourceAttrError:
            user_hours = 0.0
        user_burned_hours_dict[user_name] += user_hours
    return user_burned_hours_dict


def create_xlsx_file(user_dict: dict) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Burned Hours Per Project"
    ws.append(["Name", "Burned Hours"])
    for user_name, user_hours in user_dict.items():
        ws.append([user_name, user_hours])
    output_file = r"src/xlsx_files/burned_hours_per_worker.xlsx"
    try:
        wb.save(output_file)
    except Exception as e:
        logger.error(f"Failed to save xlsx file: {e}")


async def get_burned_hours(**kwargs):
    issues = await get_issues_by_query(**kwargs)
    user_burned_hours = get_user_hours(issues)
    for name, hours in user_burned_hours.items():
        user_burned_hours[name] = "{:.1f}".format(hours)
    create_xlsx_file(user_burned_hours)
    return user_burned_hours


if __name__ == '__main__':
    get_burned_hours(time_from='2024-12-12', time_to='2024-12-14')
    # 24002-ПФУ (підтримка)  24005-ПФУ (модернізація)
